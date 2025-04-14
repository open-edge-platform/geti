# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements import workflows"""

from flytekit import workflow

from job.tasks.import_tasks.create_project_from_dataset import create_project_from_dataset
from job.tasks.import_tasks.import_dataset_to_project import import_dataset_to_project
from job.tasks.import_tasks.parse_dataset_existing_project import parse_dataset_for_import_to_existing_project
from job.tasks.import_tasks.parse_dataset_new_project import parse_dataset_for_import_to_new_project


@workflow
def prepare_import_new_project_workflow(import_id: str) -> None:
    """
    Prepare import workflow for import to new project
    Parses the dataset
    Collects warnings for different possible geti tasks
    Collects possible labels for each geti task
    Updates metadata with warnings, possible tasks and labels
    Stores import info for next step of import

    :param import_id: id of uploaded zipped dataset
    """
    parse_dataset_for_import_to_new_project(import_id=import_id)


@workflow
def prepare_import_existing_project_workflow(import_id: str, project_id: str) -> None:
    """
    Prepare import workflow for import to existing project
    Parses the dataset
    Collects warnings for the geti task(s) of project
    Collects possible labels for the geti task
    Updates metadata with warnings, possible labels
    Stores import info for next step of import

    :param import_id: id of uploaded zipped dataset
    :param project_id: id of the project to import to
    """
    parse_dataset_for_import_to_existing_project(
        import_id=import_id,
        project_id=project_id,
    )


@workflow
def create_project_from_dataset_workflow(
    import_id: str,
    project_name: str,
    project_type: str,
    label_names: list[str],
    color_by_label: dict[str, str],
    keypoint_structure: dict[str, list[dict]],
    user_id: str,
) -> None:
    """
    Create new project from previously parsed dataset based on user input

    :param import_id: id of the uploaded and prepared dataset
    :param project_name: Name of the project to be created
    :param project_type: type of the project to be created
    :param label_names: names of the labels to keep
    :param color_by_label: mapping of labels to their colors
    :param keypoint_structure: keypoints edges and positions
    :param user_id: id of the user creating the project
    """
    create_project_from_dataset(
        import_id=import_id,
        name=project_name,
        project_type_str=project_type,
        label_names=label_names,
        color_by_label=color_by_label,
        keypoint_structure=keypoint_structure,
        user_id=user_id,
    )


@workflow
def import_dataset_to_project_workflow(
    project_id: str,
    import_id: str,
    labels_map: dict[str, str],
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
    :param labels_map: map of dm label names to geti label ids
    :param user_id: id the user who uploaded
    :return a dictionary containing info about the dataset_storage
    """
    import_dataset_to_project(
        project_id=project_id,
        import_id=import_id,
        label_ids_map=labels_map,
        dataset_storage_id=dataset_storage_id,
        dataset_name=dataset_name,
        user_id=user_id,
    )
