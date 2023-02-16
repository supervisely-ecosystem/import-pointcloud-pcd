import os
from distutils.util import strtobool

from supervisely.sly_logger import logger

import supervisely as sly
from supervisely.io.fs import mkdir

# debug
from dotenv import load_dotenv

if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))

api: sly.Api = sly.Api.from_env()

TASK_ID = int(os.environ["TASK_ID"])
TEAM_ID = int(os.environ["context.teamId"])
WORKSPACE_ID = int(os.environ["context.workspaceId"])
INPUT_PATH = os.environ.get("modal.state.slyFolder", None)
REMOVE_SOURCE = bool(strtobool(os.getenv("modal.state.remove_source")))
PROJECT_NAME = os.environ.get("modal.state.project_name")

if INPUT_PATH:
    IS_ON_AGENT = api.file.is_on_agent(INPUT_PATH)

DEFAULT_DATASET_NAME = "ds0"
ALLOWED_POINTCLOUD_EXTENSIONS = [".pcd"]

STORAGE_DIR = os.path.join(sly.app.get_data_dir(), "storage_dir")
mkdir(STORAGE_DIR, True)
