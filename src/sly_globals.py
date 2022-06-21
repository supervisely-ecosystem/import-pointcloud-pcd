import os
from pathlib import Path
from distutils.util import strtobool

from fastapi import FastAPI
from supervisely.sly_logger import logger

import supervisely
from supervisely.io.fs import mkdir
from supervisely.app.fastapi import create
from dotenv import load_dotenv

app_root_directory = str(Path(__file__).parent.absolute().parents[0])
logger.info(f"App root directory: {app_root_directory}")

load_dotenv(os.path.join(app_root_directory, "debug.env"))
load_dotenv(os.path.join(app_root_directory, "secret_debug.env"))

api = supervisely.Api.from_env()
app = FastAPI()
sly_app = create()

app.mount("/sly", sly_app)

TASK_ID = int(os.environ["TASK_ID"])
TEAM_ID = int(os.environ["context.teamId"])
WORKSPACE_ID = int(os.environ["context.workspaceId"])
INPUT_PATH = os.environ.get("modal.state.slyFolder", None)
REMOVE_SOURCE = bool(strtobool(os.getenv("modal.state.remove_source")))

DEFAULT_DATASET_NAME = "ds0"
ALLOWED_POINTCLOUD_EXTENSIONS = [".ply"]

STORAGE_DIR = os.path.join(app_root_directory, "debug", "data", "storage_dir")
mkdir(STORAGE_DIR, True)
