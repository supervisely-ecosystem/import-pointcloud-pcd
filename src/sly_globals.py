import os
from distutils.util import strtobool

import supervisely as sly
from dotenv import load_dotenv
from supervisely.io.fs import mkdir

if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))

api: sly.Api = sly.Api.from_env()

TASK_ID = int(os.environ["TASK_ID"])
TEAM_ID = int(os.environ["context.teamId"])
WORKSPACE_ID = int(os.environ["context.workspaceId"])
INPUT_FILES = os.environ.get("modal.state.files", None)
INPUT_PATH = os.environ.get("modal.state.slyFolder", None) or INPUT_FILES
REMOVE_SOURCE = bool(strtobool(os.getenv("modal.state.removeSource")))
PROJECT_NAME = os.environ.get("modal.state.projectName")

# if existing project (or dataset) is selected
PROJECT_ID = os.environ.get("modal.state.slyProjectId") or None
DATASET_ID = os.environ.get("modal.state.slyDatasetId") or None

if PROJECT_ID is not None:
    PROJECT_ID = int(PROJECT_ID)
if DATASET_ID is not None:
    DATASET_ID = int(DATASET_ID)

if INPUT_PATH:
    IS_ON_AGENT = api.file.is_on_agent(INPUT_PATH)


DEFAULT_DATASET_NAME = "ds0"
ALLOWED_POINTCLOUD_EXTENSIONS = [".pcd"]

STORAGE_DIR = os.path.join(sly.app.get_data_dir(), "storage_dir")
mkdir(STORAGE_DIR, True)
