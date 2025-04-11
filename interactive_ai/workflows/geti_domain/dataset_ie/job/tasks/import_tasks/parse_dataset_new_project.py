# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

"""Prepare dataset for import to new project task module"""

import logging
from enum import IntEnum, auto

from jobs_common.features.feature_flag_provider import FeatureFlag, FeatureFlagProvider
from jobs_common.tasks import flyte_multi_container_task as task
from jobs_common.tasks.utils.logging import init_logger
from jobs_common.tasks.utils.progress import publish_metadata_update, task_progress
from jobs_common.tasks.utils.secrets import SECRETS, env_vars
from jobs_common.tasks.utils.telemetry import task_telemetry
from jobs_common_extras.datumaro_conversion.definitions import GetiProjectType

from job.repos.data_repo import ImportDataRepo
from job.tasks import IMPORT_EXPORT_TASK_POD_SPEC
from job.utils.cross_project_mapping import CrossProjectMapper
from job.utils.datumaro_parser import get_project_metas_with_labels
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
    failure_message="Preparing dataset import to a new project failed",
)
def parse_dataset_for_import_to_new_project(import_id: str) -> None:
    """
    Loads dataset and maps each label to a list of compatible domains.
    When loading dataset, occurring import errors are aggregated and saved to job metadata to be shown to user.
    Actionable validation errors are collected and fixed

    :param import_id: id of the dataset to load
    :return: Dictionary mapping domains to labels, list of import warnings
    """
    supported_project_types, warnings = _parse_dataset_for_import_to_new_project(import_id)

    # Publish dataset data to job metadata for access by other components
    publish_metadata_update({"warnings": warnings, "supported_project_types": supported_project_types})


class _Steps(IntEnum):
    IDX_PARSE_DATASET = 0
    IDX_FIND_SUPPORTED_TASKS = auto()
    IDX_COLLECT_WARNINGS = auto()


def _parse_dataset_for_import_to_new_project(import_id: str) -> tuple[list, list]:
    import_id_ = ImportUtils.get_validated_mongo_id(id=import_id, id_name="Import Dataset ID")
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

    ImportUtils.check_max_number_of_media(dm_dataset)

    progress_reporter.reset_step(
        step_index=_Steps.IDX_FIND_SUPPORTED_TASKS, step_message="Finding supported project types and labels"
    )
    label_to_ann_types = ImportUtils.get_label_to_ann_types(
        dm_dataset=dm_dataset,
        progress_callback=progress_reporter.report,
    )
    project_metas_with_labels = get_project_metas_with_labels(
        dm_infos=dm_dataset.infos(),
        dm_categories=dm_dataset.categories(),
        label_to_ann_types=label_to_ann_types,
    )
    CrossProjectMapper.check_if_cross_project_mapping_for_new_project(
        dm_dataset=dm_dataset,
        label_to_ann_types=label_to_ann_types,
        project_metas_with_labels=project_metas_with_labels,
    )

    # Get possible tasks/domains for dataset import and set of possible labels for each possible task
    possible_domains = set()
    # Format dataset data for saving to job metadata
    supported_project_types = []
    need_warning_local_annotations_will_be_lost = False
    is_classification_task_supported = False
    for project_meta in project_metas_with_labels:
        project_type = project_meta["project_type"]
        # Handle an anomaly dataset as if it was exported from an anomaly classification task.
        if FeatureFlagProvider.is_enabled(feature_flag=FeatureFlag.FEATURE_FLAG_ANOMALY_REDUCTION) and project_type in [
            GetiProjectType.ANOMALY_DETECTION,
            GetiProjectType.ANOMALY_SEGMENTATION,
        ]:
            need_warning_local_annotations_will_be_lost = True
            continue
        if project_type == GetiProjectType.CLASSIFICATION:
            is_classification_task_supported = True
        supported_project_types.append(
            {
                "project_type": ImportUtils.project_type_to_rest_api_string(
                    geti_project_type=project_type,
                ),
                "pipeline": project_meta["pipeline"],
            }
        )
        possible_domains.add(ImportUtils.project_type_to_label_domain(project_type=project_type))
    progress_reporter.finish_step()

    # Collect and parse validation warnings
    progress_reporter.reset_step(step_index=_Steps.IDX_COLLECT_WARNINGS, step_message="Collecting validation warnings")
    error_details = ImportUtils.collect_validation_warnings(
        dm_dataset=dm_dataset,
        possible_domains=possible_domains,
        parsing_errors=error_collector.errors,
        progress_callback=progress_reporter.report,
    )
    warnings = ImportUtils.parse_errors(error_details=error_details)
    if not warnings and not supported_project_types:
        warnings.append(
            {
                "type": "warning",
                "name": "The dataset does not contain any labels",
                "description": "It is possible to use the dataset if you first "
                "create a project with labels, then import the "
                "dataset into it.",
            }
        )

    # For the det->cls case, Users should be warned if the detection dataset contains only one label,
    # as this would prevent the creation of a classification project.
    if not is_classification_task_supported and (
        ImportUtils.get_exported_project_type(dm_dataset.infos()) == GetiProjectType.DETECTION
    ):
        warnings.append(
            {
                "type": "warning",
                "name": "At least two labels are required to create a classification project",
                "description": "You cannot create a new classification project from a detection dataset "
                "that has a single label. To do this, you must first create a new classification project "
                "and then import the detection dataset into that project.",
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

    # Save dataset info to s3 storage
    dm_infos = {"detected_format": dataset_format}
    dm_dataset.transform("project_infos", dst_infos=dm_infos, overwrite=False)

    import_data_repo.save_import_info(import_id=import_id_, dataset=dm_dataset)
    import_data_repo.upload_import_info(import_id=import_id_)
    logger.info("Parsed into datumaro format and stored import info with id %s", str(import_id))

    return supported_project_types, warnings
