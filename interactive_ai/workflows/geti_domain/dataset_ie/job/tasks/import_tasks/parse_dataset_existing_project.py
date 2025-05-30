# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Prepare dataset for import to existing project task module"""

import logging
from enum import IntEnum, auto

from iai_core.entities.model_template import task_type_to_label_domain
from jobs_common.tasks import flyte_multi_container_task as task
from jobs_common.tasks.utils.logging import init_logger
from jobs_common.tasks.utils.progress import publish_metadata_update, task_progress
from jobs_common.tasks.utils.secrets import SECRETS, env_vars
from jobs_common.tasks.utils.telemetry import task_telemetry
from jobs_common_extras.datumaro_conversion.definitions import GetiProjectType

from job.repos.data_repo import ImportDataRepo
from job.tasks import IMPORT_EXPORT_TASK_POD_SPEC
from job.utils.cross_project_mapping import CrossProjectMapper
from job.utils.datumaro_parser import get_filtered_supported_project_types
from job.utils.import_utils import ImportUtils
from job.utils.progress_utils import ProgressReporter

logger = logging.getLogger(__name__)


@task(pod_spec=IMPORT_EXPORT_TASK_POD_SPEC, secret_requests=SECRETS)
@env_vars
@init_logger(package_name=__name__)
@task_telemetry
@task_progress(
    start_message="Starting dataset parsing",
    finish_message="Dataset is parsed successfully",
    failure_message="Preparing dataset import to an existing project failed",
)
def parse_dataset_for_import_to_existing_project(
    import_id: str,
    project_id: str,
) -> None:
    """
    Loads dataset to be imported into an existing project into datumaro dataset and retrieve import info
    After loading, we detect the warnings and errors in the dataset to report to the user
    We rectify multi-label classification errors by removing the affected annotations

    :param import_id: id of the dataset in the file system
    :param project_id: id of the project to import to
    """
    label_names, warnings = _parse_dataset_for_import_to_existing_project(import_id, project_id)

    # Publish dataset data to job metadata for access by other components
    publish_metadata_update({"labels": label_names, "warnings": warnings})


class _Steps(IntEnum):
    IDX_PARSE_DATASET = 0
    IDX_MAP_LABELS = auto()
    IDX_COLLECT_WARNINGS = auto()


def _parse_dataset_for_import_to_existing_project(import_id: str, project_id: str) -> tuple[tuple, list[dict]]:
    """
    Loads dataset to be imported into an existing project into datumaro dataset and retrieve import info
    After loading, we detect the warnings and errors in the dataset to report to the user
    We rectify multi-label classification errors by removing the affected annotations

    :param import_id: id of the dataset in the file system
    :param project_id: id of the project to import to
    """
    import_id_ = ImportUtils.get_validated_mongo_id(id=import_id, id_name="Import Dataset ID")
    project = ImportUtils.get_validated_project(project_id=project_id)
    project_type = ImportUtils.get_project_type(project=project)
    task_type = ImportUtils.get_validated_task_type(project=project)

    import_data_repo = ImportDataRepo()
    progress_reporter = ProgressReporter(
        step_count=len(_Steps),
        step_index=_Steps.IDX_PARSE_DATASET,
        step_message="Parsing the uploaded dataset",
    )
    progress_reporter.start_step()
    # download and unzip data
    import_data_repo.download_zipped_dataset(import_id=import_id_)
    import_data_repo.unzip_dataset(import_id=import_id_, progress_callback=progress_reporter.report)
    dataset_dir = import_data_repo.get_dataset_directory(id_=import_id_)

    # Load and parse dataset
    dataset_format = ImportUtils.detect_format(path=dataset_dir)
    dm_dataset, error_collector = ImportUtils.parse_dataset(path=dataset_dir, fmt=dataset_format)
    progress_reporter.finish_step()

    ImportUtils.check_max_number_of_media(dm_dataset, project)

    progress_reporter.reset_step(
        step_index=_Steps.IDX_MAP_LABELS,
        step_message="Finding labels mapping between dataset and project",
    )
    label_to_ann_types = ImportUtils.get_label_to_ann_types(
        dm_dataset=dm_dataset,
        progress_callback=progress_reporter.report,
    )
    label_names = CrossProjectMapper.check_if_cross_project_mapping_for_existing_project(
        dm_dataset=dm_dataset,
        label_to_ann_types=label_to_ann_types,
        project_type=project_type,
        project_identifier=project.identifier,
    )
    need_warning_local_annotations_will_be_lost = (
        label_names
        and project_type == GetiProjectType.ANOMALY
        and ImportUtils.get_exported_project_type(dm_dataset.infos())
        in [GetiProjectType.ANOMALY_DETECTION, GetiProjectType.ANOMALY_SEGMENTATION]
    )

    # Get set of labels in the dataset that are possible to import to the project
    if not label_names and not CrossProjectMapper.is_cross_mapping_case_for_geti_exported_dataset(
        dm_dataset.categories(), dm_dataset.infos(), project
    ):
        # Check if target task_type is supported regarding to CVS-105432.
        supported_project_types = get_filtered_supported_project_types(
            dm_infos=dm_dataset.infos(), label_to_ann_types=label_to_ann_types
        )
        if project_type in supported_project_types:
            # Find labels that are valid for the target task_type
            label_names = ImportUtils.get_valid_project_labels(
                project_type=project_type,
                dm_infos=dm_dataset.infos(),
                dm_categories=dm_dataset.categories(),
                label_to_ann_types=label_to_ann_types,
                include_all_labels=True,
            )
    progress_reporter.finish_step()

    # Collect and parse validation warnings
    progress_reporter.reset_step(
        step_index=_Steps.IDX_COLLECT_WARNINGS,
        step_message="Collecting validation warnings",
    )
    error_details = ImportUtils.collect_validation_warnings(
        dm_dataset=dm_dataset,
        possible_domains={task_type_to_label_domain(task_type)},
        parsing_errors=error_collector.errors,
        progress_callback=progress_reporter.report,
    )
    warnings = ImportUtils.parse_errors(error_details=error_details)
    if not label_names:
        warnings.append(
            {
                "type": "warning",
                "name": f"The dataset does not contain any valid labels for the task {project_type.name.title()}",
                "description": "It is possible to import the dataset into the project, "
                "but the media will need to be labelled manually "
                "through the annotator page.",
            }
        )
    if need_warning_local_annotations_will_be_lost:
        warnings.append(
            {
                "type": "warning",
                "name": "The local annotations will be lost",
                "description": "Please be aware that local annotations, including bounding boxes and polygons, "
                "are not supported in Anomaly projects and will not be imported.",
            }
        )

    progress_reporter.finish_step()

    # Store detected_format to avoid calling 'ImportUtils.detect_format' twice.
    dm_infos = {"detected_format": dataset_format}
    dm_dataset.transform("project_infos", dst_infos=dm_infos, overwrite=False)

    import_data_repo.save_import_info(import_id=import_id_, dataset=dm_dataset)
    import_data_repo.upload_import_info(import_id=import_id_)
    logger.info("Parsed into datumaro format and stored import info with id %s", str(import_id_))

    return label_names, warnings
