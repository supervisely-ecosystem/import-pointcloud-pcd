import os
from distutils.util import strtobool
import supervisely as sly
from supervisely.io.fs import mkdir

from dotenv import load_dotenv

load_dotenv("local.env")
load_dotenv(os.path.expanduser("~/supervisely.env"))

api = sly.Api.from_env()

INPUT_PATH = os.environ.get("modal.state.slyFolder", None)
REMOVE_SOURCE = bool(strtobool(os.getenv("modal.state.remove_source")))
PROJECT_NAME = os.environ.get("modal.state.project_name")

if INPUT_PATH:
    IS_ON_AGENT = api.file.is_on_agent(INPUT_PATH)

DEFAULT_DATASET_NAME = "ds0"
ALLOWED_POINTCLOUD_EXTENSIONS = [".pcd"]

STORAGE_DIR: str = sly.app.get_data_dir()
mkdir(STORAGE_DIR, True)
