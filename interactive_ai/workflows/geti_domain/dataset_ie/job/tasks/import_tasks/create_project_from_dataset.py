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

"""Create project and populate it with import dataset task module"""

import logging
from enum import IntEnum, auto
from typing import TYPE_CHECKING, cast

from geti_spicedb_tools import SpiceDB
from jobs_common.tasks import flyte_multi_container_task as task
from jobs_common.tasks.utils.logging import init_logger
from jobs_common.tasks.utils.progress import publish_metadata_update, task_progress
from jobs_common.tasks.utils.secrets import SECRETS, env_vars
from jobs_common.tasks.utils.telemetry import task_telemetry
from jobs_common_extras.datumaro_conversion.convert_utils import ConvertUtils
from jobs_common_extras.datumaro_conversion.definitions import CHAINED_PROJECT_TYPES, GetiProjectType
from sc_sdk.utils.project_builder import PersistedProjectBuilder

from job.repos.data_repo import ImportDataRepo
from job.tasks import IMPORT_EXPORT_TASK_POD_SPEC
from job.utils.cross_project_mapping import CrossProjectMapper
from job.utils.datumaro_parser import DatumaroProjectParser
from job.utils.import_utils import ImportUtils
from job.utils.progress_utils import WeightedProgressReporter

if TYPE_CHECKING:
    from sc_sdk.entities.label import Label

logger = logging.getLogger(__name__)


class _Steps(IntEnum):
    IDX_PARSE_AND_TRANSFORM_DATASET = 0
    IDX_CREATE_A_PROJECT = auto()
    IDX_POPULATE_ITEMS = auto()


STEPS_PROGRESS_RATIO: list[float] = [
    0.025,  # IDX_PARSE_AND_TRANSFORM_DATASET
    0.025,  # IDX_CREATE_A_PROJECT
    0.95,  # IDX_POPULATE_ITEMS
]


@task(pod_spec=IMPORT_EXPORT_TASK_POD_SPEC, secret_requests=SECRETS)
@env_vars
@init_logger(package_name=__name__)
@task_telemetry
@task_progress(
    start_message="Starting project creation",
    finish_message="Project created and populated successfully",
    failure_message="Creating project failed",
)
def create_project_from_dataset(
    import_id: str,
    name: str,
    project_type_str: str,
    label_names: list[str],
    color_by_label: dict[str, str],
    keypoint_structure: dict[str, list[dict]],  # noqa: ARG001 TODO: need to handle this
    user_id: str,
) -> None:
    """
    Create new project from previously parsed dataset.

    :param import_id: id of the import file/dataset
    :param name: name of the project to create
    :param project_type_str: type of project to create
    :param label_names: list of names of labels from dataset to import to project
    :param color_by_label: mapping of label names to their colors
    :param keypoint_structure: keypoints edges and positions
    :param user_id: id of the user creating the project
    """
    import_id_ = ImportUtils.get_validated_mongo_id(id=import_id, id_name="Import Dataset ID")
    import_data_repo = ImportDataRepo()
    project_type = GetiProjectType[project_type_str]

    # Load dataset and apply transforms
    progress_reporter = WeightedProgressReporter(
        steps_ratio=STEPS_PROGRESS_RATIO,
        step_index=_Steps.IDX_PARSE_AND_TRANSFORM_DATASET,
        step_message="Parsing the uploaded dataset",
    )
    progress_reporter.start_step()

    # Need to download and unzip dataset, because we're using ephemeral volume
    import_data_repo.download_zipped_dataset(import_id=import_id_)
    import_data_repo.unzip_dataset(import_id=import_id_, progress_callback=progress_reporter.report)
    import_data_repo.download_import_info(import_id=import_id_)

    dm_dataset = import_data_repo.load_and_transform_dataset(import_id=import_id_)
    logger.info("Loaded datumaro dataset with id %s", str(import_id_))
    progress_reporter.finish_step()

    # Should convert annotation type before filtering(ConvertUtils.filter_dataset)
    # to avoid removal of annotations for the original task.
    # TODO: refactor this to convert annotations while filtering or converting dm_anns co sc_anns
    CrossProjectMapper.convert_annotation_type_for_cross_project(dm_dataset=dm_dataset, project_type=project_type)

    progress_reporter.reset_step(step_index=_Steps.IDX_CREATE_A_PROJECT, step_message="Creating a new project")
    progress_reporter.start_step()
    label_to_ann_types = ImportUtils.get_label_to_ann_types(
        dm_dataset=dm_dataset,
        progress_callback=progress_reporter.report,
    )
    # Create project
    parser_kwargs = {
        "project_name": name,
        "project_type": project_type,
        "dm_infos": dm_dataset.infos(),
        "dm_categories": dm_dataset.categories(),
        "label_to_ann_types": label_to_ann_types,
        "selected_labels": label_names,
        "color_by_label": color_by_label if color_by_label else None,
    }
    project, label_schema, _ = PersistedProjectBuilder.build_full_project(
        creator_id=user_id, parser_class=DatumaroProjectParser, parser_kwargs=parser_kwargs
    )
    logger.info(
        "Created project with id %s; domain %s; labels %s",
        str(project.id_),
        ImportUtils.project_type_to_rest_api_string(project_type),
        str(label_names),
    )
    progress_reporter.finish_step()

    progress_reporter.reset_step(step_index=_Steps.IDX_POPULATE_ITEMS, step_message="Populating media and annotations")
    # Chained project can include all label types (label, bbox, polygon, ellipse)
    label_domain = ImportUtils.project_type_to_label_domain(project_type=project_type)
    if project_type not in CHAINED_PROJECT_TYPES:
        # transform dataset, filter out labels that do not fit the label domain and convert masks if needed
        ConvertUtils.filter_dataset(
            dm_dataset, label_domain, label_names if project_type != GetiProjectType.KEYPOINT_DETECTION else None
        )
        logger.info(
            "Filtered datumaro dataset with id %s to only keep labels %s",
            str(import_id_),
            str(label_names),
        )
    project_labels = cast("list[Label]", label_schema.get_labels(include_empty=False))

    # init util funcs
    get_sc_label = ConvertUtils.get_labels_mapper_from_dataset(
        dm_categories=dm_dataset.categories(),
        dm_infos=dm_dataset.infos(),
        sc_labels=project_labels,
        domain=label_domain,
    )
    sc_label_to_all_parents = ConvertUtils.get_sc_label_to_all_parents(
        sc_labels=project_labels, label_schema=label_schema
    )

    progress_reporter.start_step()
    # Populate the training dataset storage in the project
    dataset_storage = project.get_training_dataset_storage()
    ImportUtils.populate_project_from_datumaro_dataset(
        project=project,
        dataset_storage_identifier=dataset_storage.identifier,
        dm_dataset=dm_dataset,
        label_schema=label_schema,
        get_sc_label=get_sc_label,
        sc_label_to_all_parents=sc_label_to_all_parents,
        user_id=user_id,
        progress_callback=progress_reporter.report,
    )
    progress_reporter.finish_step()

    SpiceDB().create_project(
        workspace_id=str(project.workspace_id),
        project_id=str(project.id_),
        creator=user_id,
    )

    ImportUtils.publish_project_created_message(project=project)

    import_data_repo.delete_import_data(import_id=import_id_)

    # Publish created project id to job metadata for access by other components
    publish_metadata_update({"project_id": str(project.id_)})
