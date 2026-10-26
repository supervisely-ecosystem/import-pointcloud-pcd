import os
import supervisely as sly
from supervisely import logger
from supervisely.app.widgets import SlyTqdm

import sly_functions as f
import sly_globals as g
import workflow as w

progress_bar = SlyTqdm()

logger.info("Application has been started")

logger.info(
    "Script arguments",
    extra={
        "context.teamId": g.TEAM_ID,
        "context.workspaceId": g.WORKSPACE_ID,
        "modal.state.slyFolder": g.INPUT_PATH,
        "modal.state.files": g.INPUT_FILES,
    },
)

dir_info = g.api.file.list(g.TEAM_ID, g.INPUT_PATH)

if len(dir_info) == 0:
    raise Exception(f"There are no files in selected directory: '{g.INPUT_PATH}'")

if len(dir_info) == 1 and f.is_archive(dir_info[0]["path"]):
    raise Exception(
        f"Please select directory with pointclouds. Selected file: '{dir_info[0]['path']}' is archive."
    )

f.download_project(g.api, g.INPUT_PATH)

datasets_names, datasets_images_map = f.get_datasets_items_map(dir_info, g.STORAGE_DIR)

if g.PROJECT_ID is None:
    project_name = f.get_project_name_from_input_path(g.INPUT_PATH)

    sly.logger.debug(f"Project name: {project_name}")

    project = g.api.project.create(
        workspace_id=g.WORKSPACE_ID,
        name=project_name,
        type=sly.ProjectType.POINT_CLOUDS,
        change_name_if_conflict=True,
    )
else:
    project = g.api.project.get_info_by_id(g.PROJECT_ID)

# Count what we plan to import vs what is actually imported, so the source is only
# removed from Team Files when every point cloud (and its related images) made it.
planned_cnt = sum(len(datasets_images_map[ds]["pcd_names"]) for ds in datasets_names)
imported_cnt = 0  # point clouds of datasets imported completely, incl. related images
failed_datasets = []

pcd_cnt = 0
dataset_info = None
for dataset_name in datasets_names:
    if g.DATASET_ID is None:
        dataset_info = g.api.dataset.create(
            project_id=project.id, name=dataset_name, change_name_if_conflict=True
        )
    else:
        if dataset_info is None:
            dataset_info = g.api.dataset.get_info_by_id(g.DATASET_ID)
    used_pcd_names = [pcd.name for pcd in g.api.pointcloud.get_list(dataset_info.id)]

    checked_names = []
    pcd_names = datasets_images_map[dataset_name]["pcd_names"]
    for pcd_name in pcd_names:
        if pcd_name in used_pcd_names or pcd_name in checked_names:
            temp_name, temp_ext = os.path.splitext(pcd_name)
            new_file_name = f"{temp_name}_{sly.rand_str(5)}{temp_ext}"
            sly.logger.warning(
                f"Name {pcd_name} already exists in dataset {dataset_info.name}: renamed to {new_file_name}"
            )
            checked_names.append(new_file_name)
        else:
            checked_names.append(pcd_name)
    pcd_paths = datasets_images_map[dataset_name]["pcd_paths"]
    pcd_rel_images_paths = datasets_images_map[dataset_name]["pcd_related_images"]["images_paths"]
    pcd_rel_images_meta_paths = datasets_images_map[dataset_name]["pcd_related_images"][
        "images_metas_paths"
    ]

    try:
        pointclouds_infos = f.upload_pointclouds(
            api=g.api,
            dataset_id=dataset_info.id,
            dataset_name=dataset_info.name,
            progress_bar=progress_bar,
            pcd_names=checked_names,
            pcd_paths=pcd_paths,
        )
        pcd_cnt += len(pointclouds_infos)
        if pcd_rel_images_paths.count(None) != len(pcd_rel_images_paths):
            f.upload_related_images(
                api=g.api,
                dataset_name=dataset_info.name,
                progress_bar=progress_bar,
                pointclouds_infos=pointclouds_infos,
                pcd_rel_images_paths=pcd_rel_images_paths,
                pcd_rel_images_meta_paths=pcd_rel_images_meta_paths,
            )
        if len(pointclouds_infos) != len(pcd_names):
            raise RuntimeError(
                f"{len(pointclouds_infos)} of {len(pcd_names)} point clouds were uploaded"
            )
        imported_cnt += len(pointclouds_infos)
    except Exception as e:
        failed_datasets.append(dataset_name)
        sly.logger.error(
            msg=f"Couldn't upload files from '{dataset_name}' dataset. Please check directory's file "
            f"structure, for subdirectories and duplicated file names. Error: {repr(e)}"
        )
        continue

if pcd_cnt == 0:
    raise Exception("No pointclouds were uploaded. Please check directory's file structure.")

failed_cnt = planned_cnt - imported_cnt
skipped_cnt = len(f.SKIPPED_FILES)
sly.logger.info(
    f"Import summary: {imported_cnt} of {planned_cnt} point clouds imported completely, "
    f"failed datasets: {failed_datasets}, {skipped_cnt} files skipped."
)
import_complete = failed_cnt == 0 and not failed_datasets and skipped_cnt == 0

source_kept = False
if g.REMOVE_SOURCE and not g.IS_ON_AGENT:
    source_dir_name = g.INPUT_PATH.lstrip("/").rstrip("/")
    if import_complete:
        g.api.file.remove(team_id=g.TEAM_ID, path=g.INPUT_PATH)
        sly.logger.info(msg=f"Source directory: '{source_dir_name}' was successfully removed.")
    else:
        source_kept = True
        reasons = []
        if failed_datasets:
            reasons.append(
                f"{failed_cnt} of {planned_cnt} point clouds were not imported completely "
                f"(datasets: {', '.join(failed_datasets)})"
            )
        if skipped_cnt > 0:
            reasons.append(f"{skipped_cnt} files were skipped")
        sly.logger.warning(
            f"Source directory: '{source_dir_name}' was NOT removed from Team Files "
            f"because the import was not complete ({'; '.join(reasons)}). "
            "Check the messages above; the source is kept so no data is lost.",
            extra={"skipped_files": f.SKIPPED_FILES[:100]},
        )

g.api.task.set_output_project(task_id=g.TASK_ID, project_id=project.id, project_name=project.name)
if g.DATASET_ID:
    w.workflow_output(g.api, g.DATASET_ID, type="dataset")
else:
    w.workflow_output(g.api, project.id, type="project")

if failed_datasets:
    # Do not report success when data was lost on the way; what was imported stays in
    # the project.
    msg = (
        f"Datasets {failed_datasets} were not imported completely (see errors above): "
        f"{imported_cnt} of {planned_cnt} point clouds were imported completely into "
        f"project '{project.name}' (id: {project.id})."
    )
    if source_kept:
        msg += " The source in Team Files was kept."
    raise RuntimeError(msg)

f.shutdown_app()
