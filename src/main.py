import supervisely as sly
from supervisely import logger
from supervisely.app.widgets import SlyTqdm
import src.sly_globals as g
import src.sly_functions as f

progress_bar = SlyTqdm()


class MyImport(sly.app.Import):
    def process(self, context: sly.app.Import.Context):

        logger.info("Application has been started")

        logger.info(
            "Script arguments",
            extra={
                "context.teamId": context.team_id,
                "context.workspaceId": context.workspace_id,
                "modal.state.slyFolder": context.path,
            },
        )

        dir_info = g.api.file.list(context.team_id, g.INPUT_PATH)

        if len(dir_info) == 0:
            raise Exception(f"There are no files in selected directory: '{context.path}'")

        project_name, project_folder = f.get_project_name_from_input_path(context.path)

        datasets_names, datasets_images_map = f.get_datasets_items_map(
            dir_info, context.path, project_folder
        )
        project = g.api.project.create(
            workspace_id=context.workspace_id,
            name=project_name,
            type=sly.ProjectType.POINT_CLOUDS,
            change_name_if_conflict=True,
        )
        for dataset_name in datasets_names:
            dataset_info = g.api.dataset.create(
                project_id=project.id, name=dataset_name, change_name_if_conflict=True
            )

            pcd_names = datasets_images_map[dataset_name]["pcd_names"]
            pcd_paths = datasets_images_map[dataset_name]["pcd_paths"]
            pcd_hashes = datasets_images_map[dataset_name]["pcd_hashes"]
            pcd_rel_images_paths = datasets_images_map[dataset_name]["pcd_related_images"][
                "images_paths"
            ]
            pcd_rel_images_meta_paths = datasets_images_map[dataset_name]["pcd_related_images"][
                "images_metas_paths"
            ]

            try:
                pointclouds_infos = f.upload_pointclouds(
                    api=g.api,
                    dataset_id=dataset_info.id,
                    dataset_name=dataset_info.name,
                    progress_bar=progress_bar,
                    pcd_names=pcd_names,
                    pcd_paths=pcd_paths,
                    pcd_hashes=pcd_hashes,
                )

                if pcd_rel_images_paths.count(None) != len(pcd_rel_images_paths):
                    f.upload_related_images(
                        api=g.api,
                        dataset_name=dataset_info.name,
                        progress_bar=progress_bar,
                        pointclouds_infos=pointclouds_infos,
                        pcd_rel_images_paths=pcd_rel_images_paths,
                        pcd_rel_images_meta_paths=pcd_rel_images_meta_paths,
                    )
            except:
                sly.logger.error(
                    msg=f"Couldn't upload files from '{dataset_name}' dataset. Please check directory's file "
                    f"structure, for subdirectories and duplicated file names"
                )
                continue

        if g.REMOVE_SOURCE and not g.IS_ON_AGENT:
            g.api.file.remove(team_id=context.team_id, path=g.INPUT_PATH)
            source_dir_name = context.path.lstrip("/").rstrip("/")
            sly.logger.info(msg=f"Source directory: '{source_dir_name}' was successfully removed.")


app = MyImport()
app.run()
f.shutdown_app()
