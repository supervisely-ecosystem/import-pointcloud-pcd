"""Offline test harness: runs the src/main.py script against a small in-memory fake of
sly.Api. No Supervisely server is contacted. Run from the repo root:
    python -m pytest tests
with the SDK version from dev_requirements.txt installed (plus pytest).
"""
import importlib
import os
import sys
from types import SimpleNamespace

import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT_DIR, "src")
APP_MODULES = (
    "main", "sly_globals", "sly_functions", "workflow", "download_progress",
    "src", "src.sly_globals", "src.sly_functions", "src.download_progress",
)


class FakeFileApi:
    def __init__(self, files):
        # files: {remote_path: bytes}
        self.files = dict(files)
        self.removed = []

    def list(self, team_id, path, *args, **kwargs):
        return [
            {"path": p, "name": os.path.basename(p), "hash": f"hash-{p}"}
            for p in self.files
            if p.startswith(path)
        ]

    def is_on_agent(self, remote_path):
        return remote_path.startswith("agent://")

    def get_directory_size(self, team_id, path):
        return sum(len(v) for p, v in self.files.items() if p.startswith(path))

    def download_directory(self, team_id, remote_path, local_save_path, progress_cb=None):
        for p, data in self.files.items():
            if p.startswith(remote_path):
                local = os.path.join(local_save_path, p[len(remote_path):].lstrip("/"))
                os.makedirs(os.path.dirname(local), exist_ok=True)
                with open(local, "wb") as fh:
                    fh.write(data)

    def remove(self, team_id, path):
        self.removed.append(path)


class FakePointcloudApi:
    def __init__(self, reject_names=()):
        self.reject_names = set(reject_names)
        self.uploaded = []
        self.related_images = []

    def get_list(self, dataset_id):
        return []

    def upload_paths(self, dataset_id, names, paths, **kwargs):
        bad = [n for n in names if n in self.reject_names]
        if bad:
            # e.g. the server rejecting a corrupt .pcd (HTTP 400 after retries)
            raise RuntimeError(f"HTTP 400 from point-clouds.bulk.add for {bad}")
        infos = []
        for name in names:
            self.uploaded.append((dataset_id, name))
            infos.append(SimpleNamespace(id=len(self.uploaded), name=name))
        return infos

    def upload_related_image(self, path):
        return [f"hash-{os.path.basename(path)}"]

    def add_related_images(self, images_infos):
        self.related_images.extend(images_infos)


class FakeApi:
    def __init__(self, files, reject_names=()):
        self.file = FakeFileApi(files)
        self.pointcloud = FakePointcloudApi(reject_names)
        self._ds = 0
        self.project = SimpleNamespace(
            get_info_by_id=lambda id: None,
            create=lambda workspace_id, name, type=None, change_name_if_conflict=False: (
                SimpleNamespace(id=100, name=name)
            ),
        )
        self.dataset = SimpleNamespace(create=self._create_dataset, get_info_by_id=None)
        self.output_project = None
        self.task = SimpleNamespace(set_output_project=self._set_output_project)
        self.app = SimpleNamespace(
            workflow=SimpleNamespace(
                add_output_project=lambda id: None, add_output_dataset=lambda id: None
            )
        )

    def _create_dataset(self, project_id, name, change_name_if_conflict=False):
        self._ds += 1
        return SimpleNamespace(id=self._ds, name=name)

    def _set_output_project(self, task_id, project_id, project_name=None):
        self.output_project = project_id


@pytest.fixture
def run_app(tmp_path, monkeypatch):
    """Run the app script for the given Team Files content.

    Returns (error, api): the exception the task ends with (None on success) and the fake.
    """
    import supervisely as sly

    def _run(files, input_path="/pcd/", remove_source=True, reject_names=()):
        api = FakeApi(files, reject_names)
        monkeypatch.setenv("ENV", "production")
        monkeypatch.setenv("SLY_APP_DATA_DIR", str(tmp_path / "data"))
        monkeypatch.setenv("TASK_ID", "1")
        monkeypatch.setenv("context.teamId", "8")
        monkeypatch.setenv("context.workspaceId", "9")
        monkeypatch.setenv("modal.state.slyFolder", input_path)
        monkeypatch.setenv("modal.state.removeSource", "true" if remove_source else "false")
        monkeypatch.setenv("modal.state.projectName", "")
        for name in ("modal.state.files", "modal.state.slyProjectId", "modal.state.slyDatasetId",
                     "modal.state.projectId", "modal.state.datasetId"):
            monkeypatch.delenv(name, raising=False)
        monkeypatch.setattr(sly.Api, "from_env", classmethod(lambda cls, *a, **k: api))
        # the app shuts its FastAPI server down at the end; nothing to shut down here
        monkeypatch.setattr(sly.app.fastapi, "shutdown", lambda *a, **k: None)
        # the image runs `python src/main.py` with the repo root on PYTHONPATH
        monkeypatch.syspath_prepend(ROOT_DIR)
        monkeypatch.syspath_prepend(SRC_DIR)
        for mod in APP_MODULES:
            sys.modules.pop(mod, None)
        try:
            importlib.import_module("main")
        except Exception as e:  # noqa: BLE001 - the task's final error is what we check
            return e, api
        return None, api

    yield _run
    for mod in APP_MODULES:
        sys.modules.pop(mod, None)
