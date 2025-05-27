# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
import random
import re
import time

from behave import given, then, when
from behave.runner import Context
from geti_client import (
    CreateProjectRequest,
    CreateProjectRequestPipeline,
    CreateProjectRequestPipelineConnectionsInner,
    CreateProjectRequestPipelineTasksInner,
    CreateProjectRequestPipelineTasksInnerLabelsInner,
    EditProjectRequest,
    EditProjectRequestPipeline,
    ProjectsApi,
)
from static_definitions import PROJECT_TYPE_TO_TASK_MAPPING, JobType, ProjectType, TaskType

logger = logging.getLogger(__name__)


def _parse_label_structure(
    label_structure: str,
) -> tuple[dict[str, str], dict[str, str]]:
    """
    Parse the label structure from a docstring with the following representation

    Groups: parent_group (parent_label_1, parent_label_2); child_group (child_label_3, child_label_4)
    Hierarchy: parent_label_1 -> child_group

    :param label_structure: string with the label structure
    :return: tuple containing:
      - group_by_label_name: dictionary mapping label names to group names
      - parent_by_child_label_name: dictionary mapping child label names to parent label names
    """
    group_by_label_name = {}
    parent_by_child_label_name = {}

    # Split the structure into groups and hierarchy parts
    groups_part, hierarchy_part = label_structure.strip().split("Hierarchy:")

    # Parse groups
    group_pattern = re.compile(r"(\w+)\s*\(([^)]+)\)")
    for match in group_pattern.finditer(groups_part):
        group_name = match.group(1).strip()
        labels = match.group(2).split(",")
        for label in labels:
            group_by_label_name[label.strip()] = group_name

    # Parse hierarchy
    hierarchy_pairs = hierarchy_part.split(";")
    for pair in hierarchy_pairs:
        if "->" in pair:
            parent, child_group = pair.split("->")
            parent = parent.strip()
            child_group = child_group.strip()
            # Apply parenthood to all labels in the child group
            for label, group in group_by_label_name.items():
                if group == child_group:
                    parent_by_child_label_name[label] = parent

    return group_by_label_name, parent_by_child_label_name


def _parse_keypoint_structure(
    keypoint_structure: str,
) -> tuple[list[str], list[dict], list[dict]]:
    """
    Parse the keypoint structure from a docstring with the following representation


    Keypoints: label_1, label_2, .....
    Edges: label_1-label_2, label_2-label_3, .....
    Positions: x1, y1; x2, y2; .....


    :param keypoint_structure: string with the keypoint structure
    :return: tuple containing:
      - keypoint_labels: the keypoint labels
      - keypoint_edges: the keypoint graph edges
      - keypoint_positions: the Keypoint positions
    """
    keypoint_labels = []
    keypoint_edges = []
    keypoint_positions = []

    # Split the structure into keypoint, edges, and position parts
    keypoints_part, edges_part, positions_part = keypoint_structure.strip().split("&")

    # Parse keypoints
    _, keypoints = keypoints_part.split(":")
    for keypoint in keypoints.split(","):
        keypoint = keypoint.strip()
        keypoint_labels.append(keypoint)

    # Parse edges
    _, edges = edges_part.split(":")
    for edge in edges.split(","):
        edge = edge.strip()
        keypoint_edges.append({"nodes": edge.split("-")})

    # Parse positions
    _, positions = positions_part.split(":")
    for label, position in zip(keypoint_labels, positions.split(";")):
        position = position.strip()
        x, y = position.split(",")
        keypoint_positions.append({"label": label, "x": float(x), "y": float(y)})

    return keypoint_labels, keypoint_edges, keypoint_positions


def _create_project_from_scratch(  # noqa: C901
    context: Context,
    project_type: ProjectType,
    label_names: list[str] | None = None,
    group_by_label_name: dict[str, str] | None = None,
    parent_by_child_label_name: dict[str, str] | None = None,
    keypoint_edges: list[dict] | None = None,
    keypoint_positions: list[dict] | None = None,
) -> None:
    """
    Create a project from scratch with the given project type and label structure.

    Requires context:
    - projects_api

    Sets context:
    - project_info
    - project_id
    - dataset_id
    - label_info_by_name
    - _media_info_by_name

    :param context: the context object
    :param project_type: the project type
    :param label_names: the list of label names
    :param group_by_label_name: the mapping of label names to group names
    :param parent_by_child_label_name: the mapping of child label names to parent label names
    """
    context.project_type = project_type
    projects_api: ProjectsApi = context.projects_api

    try:
        api_task_types = PROJECT_TYPE_TO_TASK_MAPPING[project_type]
    except KeyError:
        raise ValueError(f"Unsupported project type: {project_type}")

    if api_task_types[0] == "anomaly":
        label_names = []  # Labels do not have to be provided in the request to create anomaly projects
    if label_names is None:
        label_names = ["Foo", "Bar", "Baz"]

    if len(api_task_types) > 1:
        first_task_labels = [label_names[0]]
        second_task_labels = label_names[1:]
    else:
        first_task_labels = label_names
        second_task_labels = []

    assign_labels_to_distinct_groups = project_type is ProjectType.MULTILABEL_CLASSIFICATION
    if group_by_label_name is None:
        group_by_label_name = {}

    if parent_by_child_label_name is None:
        parent_by_child_label_name = {}

    if keypoint_edges is None:
        keypoint_edges = []

    if keypoint_positions is None:
        keypoint_positions = []

    keypoint_structure = {
        "edges": keypoint_edges,
        "positions": keypoint_positions,
    }

    connections = [
        CreateProjectRequestPipelineConnectionsInner(
            var_from="dataset",
            to=api_task_types[0],
        ),
    ]
    if len(api_task_types) > 1:
        connections.extend(
            [
                CreateProjectRequestPipelineConnectionsInner(
                    var_from=api_task_types[0],
                    to="crop",
                ),
                CreateProjectRequestPipelineConnectionsInner(
                    var_from="crop",
                    to=api_task_types[1],
                ),
            ]
        )

    tasks = [
        CreateProjectRequestPipelineTasksInner(
            title="dataset",
            task_type="dataset",
        ),
        CreateProjectRequestPipelineTasksInner(
            title=api_task_types[0],
            task_type=api_task_types[0],
            labels=[
                CreateProjectRequestPipelineTasksInnerLabelsInner(
                    name=label_name,
                    color=f"#{random.randint(0, 0xFFFFFF):06x}",
                    group=(
                        f"Group {label_name}"
                        if assign_labels_to_distinct_groups
                        else group_by_label_name.get(label_name, "Default group")
                    ),
                    parent_id=parent_by_child_label_name.get(label_name),
                )
                for label_name in first_task_labels
            ],
            keypoint_structure=keypoint_structure,
        ),
    ]
    if len(api_task_types) > 1:
        tasks.extend(
            [
                CreateProjectRequestPipelineTasksInner(
                    title="crop",
                    task_type="crop",
                ),
                CreateProjectRequestPipelineTasksInner(
                    title=api_task_types[1],
                    task_type=api_task_types[1],
                    labels=[
                        CreateProjectRequestPipelineTasksInnerLabelsInner(
                            name=label_name,
                            color=f"#{random.randint(0, 0xFFFFFF):06x}",
                            group=group_by_label_name.get(label_name, "Default second task group"),
                            parent_id=parent_by_child_label_name.get(label_name),
                        )
                        for label_name in second_task_labels
                    ],
                ),
            ]
        )

    create_project_response = projects_api.create_project(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        create_project_request=CreateProjectRequest(
            name=f"Project - {project_type}",
            pipeline=CreateProjectRequestPipeline(
                connections=connections,
                tasks=tasks,
            ),
        ),
    )
    context.project_info = create_project_response  # store the whole response for convenience in other steps
    context.project_id = create_project_response.id
    context.dataset_id = create_project_response.datasets[0].id
    context._dataset_info_by_name = {
        dataset_info.name: dataset_info for dataset_info in create_project_response.datasets
    }
    context.label_info_by_name = {  # dict[str, CreateProject201ResponsePipelineTasksInnerLabelsInner]
        label.name: label for task in create_project_response.pipeline.tasks if task.labels for label in task.labels
    }
    context._media_info_by_name = {}  # dict[str, Image | Video]; populated when uploading media

    # After creating the project, it may remain inaccessible for a few seconds due to SpiceDB consistency model.
    # To avoid 403 Forbidden errors in subsequent steps, wait for the project to become accessible.
    time.sleep(5)  # SpiceDB cache is refreshed every 5s by default


@given("a project of type '{project_type}' with structure")
def step_given_project_with_custom_type_and_label_structure(context: Context, project_type: str) -> None:
    # the label structure is provided as docstring and accessible here via context.text
    group_by_label_name, parent_by_child_label_name = _parse_label_structure(context.text)
    _create_project_from_scratch(
        context=context,
        project_type=ProjectType(project_type),
        label_names=list(group_by_label_name),
        group_by_label_name=group_by_label_name,
        parent_by_child_label_name=parent_by_child_label_name,
    )


@given("a project of type '{project_type}' with keypoint structure")
def step_given_project_with_custom_type_and_keypoint_structure(context: Context, project_type: str) -> None:
    # the keypoint structure is provided as docstring and accessible here via context.text
    keypoint_labels, keypoint_edges, keypoint_positions = _parse_keypoint_structure(context.text)
    _create_project_from_scratch(
        context=context,
        project_type=ProjectType(project_type),
        label_names=keypoint_labels,
        keypoint_edges=keypoint_edges,
        keypoint_positions=keypoint_positions,
    )


@given("a project of type '{project_type}' with labels '{raw_label_names}'")
def step_given_project_with_custom_type_and_label_names(
    context: Context, project_type: str, raw_label_names: str
) -> None:
    label_names = raw_label_names.split(", ")
    _create_project_from_scratch(context=context, project_type=ProjectType(project_type), label_names=label_names)


@given("a project of type '{project_type}'")
def step_given_project_with_custom_type(context: Context, project_type) -> None:
    _create_project_from_scratch(context=context, project_type=ProjectType(project_type))


@when("the user renames the project to '{new_name}'")
def step_when_user_renames_project(context: Context, new_name: str) -> None:
    projects_api: ProjectsApi = context.projects_api

    pipeline_dict = context.project_info.pipeline.to_dict()
    for task in pipeline_dict["tasks"]:
        # No Object label cannot be edited
        task["labels"] = [label for label in task.get("labels", []) if label["group"].lower() != "no object"]
    pipeline = EditProjectRequestPipeline.from_dict(pipeline_dict)
    projects_api.edit_project(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        project_id=context.project_id,
        edit_project_request=EditProjectRequest(name=new_name, pipeline=pipeline, id=context.project_id),
    )
    context.project_info = projects_api.get_project_info(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        project_id=context.project_id,
    )


@when("the user deletes the project")
def step_when_user_deletes_project(context: Context) -> None:
    projects_api: ProjectsApi = context.projects_api
    # Delete the project: note that we do not remove the project id from the context to allow for further steps to
    # verify the project deletion
    projects_api.delete_project(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        project_id=context.project_id,
    )


@when("the user tries to delete the project")
def step_when_user_tries_to_delete_project(context: Context) -> None:
    try:
        step_when_user_deletes_project(context=context)
    except Exception as e:
        context.exception = e


@when("the user loads the project")
def step_when_user_loads_project(context: Context) -> None:
    projects_api: ProjectsApi = context.projects_api
    context.project_info = projects_api.get_project_info(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        project_id=context.project_id,
    )


@when("the user tries to load the project")
def step_when_user_tries_to_load_project(context: Context) -> None:
    try:
        step_when_user_loads_project(context=context)
    except Exception as e:
        context.exception = e


@then("the project name is '{new_name}'")
def step_then_project_name_is(context: Context, new_name: str) -> None:
    assert context.project_info.name == new_name, (
        f"Expected project name {new_name}, but found {context.project_info.name}"
    )


@then("a project of type '{project_type}' is created from '{job_type}' job")
def step_then_imported_project_is_created_via_import(context: Context, project_type: str, job_type: str) -> None:
    expected_project_type = ProjectType(project_type)
    expected_job_type = JobType(job_type)
    projects_api: ProjectsApi = context.projects_api

    job_info = context.job_info.actual_instance
    if expected_job_type is JobType.DATASET_IMPORT_TO_NEW_PROJECT:
        context.project_id = job_info.metadata.project_id
    elif expected_job_type is JobType.PROJECT_IMPORT:
        context.project_id = job_info.metadata.project.id
    else:
        raise ValueError(f"Unsupported job type: {expected_job_type}")
    context.project_info = projects_api.get_project_info(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        project_id=context.project_id,
    )

    # Check that the project has the expected tasks
    project_tasks = [TaskType(task.task_type) for task in context.project_info.pipeline.tasks if task.labels]
    expected_tasks = PROJECT_TYPE_TO_TASK_MAPPING[expected_project_type]
    assert project_tasks == expected_tasks, f"Expected tasks {expected_tasks}, but found {project_tasks}"

    # Initialize other context attributes for the next steps, if any
    context.dataset_id = context.project_info.datasets[0].id
    context.label_info_by_name = {
        label.name: label for task in context.project_info.pipeline.tasks if task.labels for label in task.labels
    }
