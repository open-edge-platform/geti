# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Create export dataset task module"""

import logging
import os
from enum import IntEnum, auto
from typing import Any

from datumaro.components.dataset import StreamDataset
from datumaro.components.media import Image as dm_Image
from datumaro.components.media import MediaElement as dm_MediaElement
from geti_types import ID, ProjectIdentifier
from iai_core.entities.label_schema import LabelSchema, NullLabelSchema
from iai_core.repos import DatasetStorageRepo, LabelSchemaRepo
from jobs_common.tasks import flyte_multi_container_task as task
from jobs_common.tasks.utils.logging import init_logger
from jobs_common.tasks.utils.progress import publish_metadata_update, task_progress
from jobs_common.tasks.utils.secrets import SECRETS, env_vars
from jobs_common.tasks.utils.telemetry import task_telemetry
from jobs_common_extras.datumaro_conversion.definitions import ANOMALY_PROJECT_TYPES, FORMAT_NAME_MAP
from jobs_common_extras.datumaro_conversion.sc_extractor import (
    ProgressConfig,
    ScExtractorFromDatasetStorage,
    VideoExportConfig,
)

from job.repos.data_repo import ExportDataRepo
from job.tasks import IMPORT_EXPORT_TASK_POD_SPEC
from job.utils.export_utils import ExportUtils
from job.utils.import_utils import ImportUtils
from job.utils.progress_utils import WeightedProgressReporter

logger = logging.getLogger(__name__)


class _Steps(IntEnum):
    IDX_BUILD_DATASET = 0
    IDX_EXPORT_DATASET = auto()
    IDX_ARCHIVE_DATASET = auto()


STEPS_PROGRESS_RATIO: list[float] = [
    0.02,  # IDX_BUILD_DATASET
    0.96,  # IDX_EXPORT_DATASET
    0.02,  # IDX_ARCHIVE_DATASET
]


EXPORT_STORAGE_PATH = os.path.join(os.environ.get("STORAGE_DIR_PATH", "/ie_storage"), "exports")


@task(pod_spec=IMPORT_EXPORT_TASK_POD_SPEC, secret_requests=SECRETS)
@env_vars
@init_logger(package_name=__name__)
@task_telemetry
@task_progress(
    start_message="Starting export dataset creation",
    finish_message="Export dataset is created",
    failure_message="Exporting dataset failed",
)
def export_dataset_task(  # noqa: PLR0915
    organization_id: str,
    project_id: str,
    dataset_storage_id: str,
    include_unannotated: bool,
    export_format: str,
    save_video_as_images: bool,
) -> str:
    """
    Export dataset storage from Geti to zipped dataset task

    :param organization_id: ID of the organization
    :param project_id: ID of the project holding the dataset storage
    :param dataset_storage_id: ID of the dataset to export
    :param export_format: format to export dataset to
    :param include_unannotated: whether to include unannotated media in export
    :param save_video_as_images: Whether to export video as frame images or not.
        For formats that don't natively support videos (all except Datumaro),
        this parameter is implicitly overridden to true.
    :return: ID of the exported dataset
    """
    project = ImportUtils.get_validated_project(project_id)
    dataset_storage = DatasetStorageRepo(
        ProjectIdentifier(workspace_id=project.workspace_id, project_id=ID(project_id))
    ).get_by_id(ID(dataset_storage_id))
    export_data_repo = ExportDataRepo()
    export_id: ID = DatasetStorageRepo.generate_id()

    # Determine whether to store project metadata
    project_type = ImportUtils.get_project_type(project=project)
    label_schema: LabelSchema = LabelSchemaRepo(project.identifier).get_latest()
    if isinstance(label_schema, NullLabelSchema):
        label_schema = ExportUtils.build_label_schema_from_dataset_storage(
            dataset_storage=dataset_storage,
            include_empty=False,
        )
    ExportUtils.determine_use_label_schema(project_type)
    store_project_metadata = export_format == "datumaro"
    if export_format != "datumaro":
        logger.info(f"Videos will be exported as images for format '{export_format}'.")
        save_video_as_images = True

    # Create datumaro dataset with data from geti dataset
    try:
        path = export_data_repo.get_dataset_directory(id_=export_id)
        dm_fmt: str = FORMAT_NAME_MAP[export_format]

        if save_video_as_images:
            save_video_annotation_range = False
        else:
            tasks = project.get_trainable_task_nodes()
            # VideoAnnotationRange is supported only for a single global/anomaly task projects
            # If this condition is changed, please modify the condition in
            # AnnotationRESTController::make_video_range_annotation @ Resources MS
            save_video_annotation_range = len(tasks) == 1 and (
                tasks[0].task_properties.is_global or tasks[0].task_properties.is_anomaly
            )

        video_root = os.path.join(path, "videos", "default") if not save_video_as_images else None
        video_export_config = VideoExportConfig(video_root, save_video_annotation_range) if video_root else None

        progress_reporter = WeightedProgressReporter(
            steps_ratio=STEPS_PROGRESS_RATIO,
            step_index=_Steps.IDX_BUILD_DATASET,
            step_message="Building a dataset for export",
        )
        # | format   | stream | iter_count |
        # |----------|--------|------------|
        # | coco     | o      | 1          |
        # | datumaro | o      | 2          |
        # | voc      | o      | 2          |
        # | yolo     | o      | 1          |
        # So we don't need to consider the case, stream=x
        progress_config = ProgressConfig(
            progress_callback=progress_reporter.report,  # this will be called while exporting
            total_iter_count=1 if export_format in ["coco", "yolo"] else 2,
        )
        progress_reporter.start_step()
        dm_dataset = StreamDataset(
            ScExtractorFromDatasetStorage(
                dataset_storage=dataset_storage,
                label_schema=label_schema,
                include_unannotated=include_unannotated,
                video_export_config=video_export_config,
                progress_config=progress_config,
            ),
            media_type=dm_Image if save_video_as_images else dm_MediaElement,
        )

        progress_reporter.finish_step()
        logger.info(f"Dataset with ID `{str(export_id)}` is built for export.")

        # Add extra metadata to dm dataset
        export_options: dict[str, Any] = {"save_media": True}
        if dm_fmt == "voc":
            dm_dataset.transform("polygons_to_masks")
            export_options["label_map"] = ExportUtils.create_voc_label_map(label_schema)
        if store_project_metadata:
            dm_infos = dm_dataset.infos()
            dm_infos["GetiProjectTask"] = ImportUtils.project_type_to_rest_api_string(project_type)
            if project_type in ANOMALY_PROJECT_TYPES:
                if label_schema is None:
                    anomaly_labels = []
                else:
                    anomaly_labels = [
                        label.name for label in label_schema.get_labels(include_empty=False) if label.is_anomalous
                    ]
                dm_infos["GetiAnomalyLabels"] = anomaly_labels
            dm_infos["GetiTaskTypeLabels"] = ExportUtils.get_task_type_with_labels(project=project)
            dm_dataset.transform("project_infos", dst_infos=dm_infos, overwrite=False)

        progress_reporter.reset_step(_Steps.IDX_EXPORT_DATASET, f"Exporting a dataset to {export_format} format")
        progress_reporter.start_step()
        # Export dataset to filesystem in needed format
        dm_dataset.export(path, dm_fmt, **export_options)
        progress_reporter.finish_step()
        logger.info(f"Dataset with ID `{str(export_id)}` is exported to {dm_fmt} format.")

        progress_reporter.reset_step(_Steps.IDX_ARCHIVE_DATASET, "Archiving exported dataset")
        progress_reporter.start_step()
        # Archive dataset
        zipped_size = export_data_repo.zip_dataset(export_id)
        progress_reporter.report(1, 2)
        logger.info(f"Dataset with ID {str(export_id)} is zipped successfully. (size={zipped_size})")
        # Upload zipped dataset to the s3 storage for later download
        export_data_repo.upload_zipped_dataset(export_id)
        progress_reporter.finish_step()
        logger.info(f"The zipped dataset with ID {str(export_id)} is uploaded successfully")

        # Create and publish download url to supply to user
        download_url = (
            f"api/v1/organizations/{organization_id}/workspaces/{str(project.workspace_id)}/projects/{project_id}/"
            f"datasets/{dataset_storage_id}/exports/{str(export_id)}/download"
        )
        publish_metadata_update({"download_url": download_url, "size": zipped_size})
    except Exception as e:
        if isinstance(e, AttributeError):
            message = "Error while exporting dataset. Possibly due to media being deleted during export."
        else:
            message = "Unknown Error encountered while exporting dataset."
        logger.exception(message)
        raise

    return str(export_id)
