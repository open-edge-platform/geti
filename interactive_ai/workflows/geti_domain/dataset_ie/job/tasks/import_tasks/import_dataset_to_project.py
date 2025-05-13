# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Import dataset to existing project task module"""

import logging
from enum import IntEnum, auto
from typing import TYPE_CHECKING, cast

from geti_types import ID
from iai_core.entities.model_template import task_type_to_label_domain
from iai_core.repos import LabelSchemaRepo
from jobs_common.tasks import flyte_multi_container_task as task
from jobs_common.tasks.utils.logging import init_logger
from jobs_common.tasks.utils.progress import publish_metadata_update, task_progress
from jobs_common.tasks.utils.secrets import SECRETS, env_vars
from jobs_common.tasks.utils.telemetry import task_telemetry
from jobs_common_extras.datumaro_conversion.convert_utils import ConvertUtils

from job.repos.data_repo import ImportDataRepo
from job.tasks import IMPORT_EXPORT_TASK_POD_SPEC
from job.utils.cross_project_mapping import CrossProjectMapper
from job.utils.exceptions import InvalidLabelException
from job.utils.import_utils import ImportUtils
from job.utils.progress_utils import WeightedProgressReporter

if TYPE_CHECKING:
    from iai_core.entities.label import Label

logger = logging.getLogger(__name__)


class _Steps(IntEnum):
    IDX_PARSE_AND_TRANSFORM_DATASET = 0
    IDX_POPULATE_ITEMS = auto()


STEPS_PROGRESS_RATIO: list[float] = [
    0.05,  # IDX_PARSE_AND_TRANSFORM_DATASET
    0.95,  # IDX_POPULATE_ITEMS
]


@task(pod_spec=IMPORT_EXPORT_TASK_POD_SPEC, secret_requests=SECRETS)
@env_vars
@init_logger(package_name=__name__)
@task_telemetry
@task_progress(
    start_message="Starting dataset import",
    finish_message="Project populated successfully",
    failure_message="Importing dataset failed",
)
def import_dataset_to_project(
    project_id: str,
    import_id: str,
    label_ids_map: dict[str, str],
    dataset_storage_id: str,
    dataset_name: str,
    user_id: str,
) -> None:
    """
    Add loaded and parsed dataset with given dataset id to project with given project id

    :param project_id: id of project
    :param import_id: id of the datumaro dataset in the filesystem
    :param dataset_storage_id: id of the dataset storage, if importing to an existing one
    :param dataset_name: Name of the new dataset storage, if importing to a new one
    :param label_ids_map: map of dm label names to geti label ids
    :param user_id: id the user who uploaded
    :return a dictionary containing info about the dataset_storage
    """
    import_id_ = ImportUtils.get_validated_mongo_id(id=import_id, id_name="Import Dataset ID")
    project = ImportUtils.get_validated_project(project_id=project_id)
    task_type = project.get_trainable_task_nodes()[0].task_properties.task_type
    domain = task_type_to_label_domain(task_type=task_type)
    labels_map = ImportUtils.get_validated_labels_map(labels_map=label_ids_map, project_identifier=project.identifier)

    # Load dataset and apply transforms
    import_data_repo = ImportDataRepo()
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

    project_type = ImportUtils.task_types_to_project_type([task_type])
    # Should convert annotation type before filtering(ConvertUtils.filter_dataset)
    # to avoid removal of annotations for the original task.
    # TODO: refactor this to convert annotations while filtering or converting dm_anns co sc_anns
    CrossProjectMapper.convert_annotation_type_for_cross_project(dm_dataset=dm_dataset, project_type=project_type)

    # Map labels by id
    dm_labels_name = list(labels_map.keys())
    if not ConvertUtils.check_all_label_names_in_dataset(dm_dataset.categories(), dm_labels_name):
        raise InvalidLabelException("Some label names are not present in the dataset")

    # Filter dataset to keep only labels chosen by the user
    ConvertUtils.filter_dataset(dm_dataset, domain, dm_labels_name)
    logger.info(
        "Filtered datumaro dataset with id %s to only keep labels %s",
        str(import_id),
        str(dm_labels_name),
    )

    # Handle mapping to the empty label
    ConvertUtils.filter_empty_label(dm_dataset, labels_map)

    progress_reporter.reset_step(
        step_index=_Steps.IDX_POPULATE_ITEMS,
        step_message="Populating media and annotations",
    )

    # init util funcs
    get_sc_label = ConvertUtils.get_labels_mapper_from_labels_map(dm_dataset.categories(), labels_map)
    latest_schema = LabelSchemaRepo(project.identifier).get_latest()
    sc_label_to_all_parents = ConvertUtils.get_sc_label_to_all_parents(
        sc_labels=cast("list[Label]", latest_schema.get_all_labels()),
        label_schema=latest_schema,
    )

    # Populate the project
    if dataset_storage_id:
        dataset_storage = project.get_dataset_storage_by_id(dataset_storage_id=ID(dataset_storage_id))
    else:
        dataset_storage = ImportUtils.create_dataset_storage(project=project, dataset_name=dataset_name)

    progress_reporter.start_step()
    ImportUtils.populate_project_from_datumaro_dataset(
        project=project,
        dataset_storage_identifier=dataset_storage.identifier,
        dm_dataset=dm_dataset,
        label_schema=latest_schema,
        get_sc_label=get_sc_label,
        sc_label_to_all_parents=sc_label_to_all_parents,
        user_id=user_id,
        progress_callback=progress_reporter.report,
    )
    progress_reporter.finish_step()

    # Publish info of the populated dataset storage
    output_dictionary = {
        "dataset": {
            "id": str(dataset_storage.id_),
            "name": dataset_storage.name,
            "use_for_training": dataset_storage.use_for_training,
            "creation_time": dataset_storage.creation_date.isoformat(),
        }
    }

    import_data_repo.delete_import_data(import_id=import_id_)

    publish_metadata_update(output_dictionary)
