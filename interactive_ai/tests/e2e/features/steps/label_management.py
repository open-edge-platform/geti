# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

from behave import then, when
from behave.runner import Context
from geti_client import (
    CreateProject201Response,
    EditProjectRequest,
    EditProjectRequestPipeline,
    EditProjectRequestPipelineConnectionsInner,
    EditProjectRequestPipelineTasksInner,
    EditProjectRequestPipelineTasksInnerLabelsInner,
    ProjectsApi,
)
from static_definitions import PROJECT_TYPE_TO_EMPTY_LABEL_NAME_MAPPING

logger = logging.getLogger(__name__)


def _add_label(context: Context, new_label_name: str) -> None:
    projects_api: ProjectsApi = context.projects_api
    project_info: CreateProject201Response = context.project_info
    first_non_empty_label = next(
        label for task in project_info.pipeline.tasks if task.labels for label in task.labels if not label.is_empty
    )
    edit_pipeline = EditProjectRequestPipeline(
        connections=[
            EditProjectRequestPipelineConnectionsInner(var_from=conn.var_from, to=conn.to)
            for conn in project_info.pipeline.connections
        ],
        tasks=[
            EditProjectRequestPipelineTasksInner(
                id=task.id,
                title=task.title,
                task_type=task.task_type,
                labels=(
                    [  # existing labels
                        EditProjectRequestPipelineTasksInnerLabelsInner(
                            id=label.id,
                            name=label.name,
                            color=label.color,
                            group=label.group,
                            is_empty=label.is_empty,
                            is_anomalous=label.is_anomalous,
                            parent_id=label.parent_id,
                        )
                        for label in task.labels
                        if not label.is_empty  # empty labels should not be included in the update payload
                    ]
                    if task.labels
                    else []
                )
                + (
                    [  # new label
                        EditProjectRequestPipelineTasksInnerLabelsInner(
                            name=new_label_name,
                            color="#FF0000",
                            group=first_non_empty_label.group,  # copy the group from a non-empty label
                            is_empty=False,
                            is_anomalous=False,
                            parent_id=first_non_empty_label.parent_id,
                            # copy the parent_id from a non-empty label
                            revisit_affected_annotations=True,
                        )
                    ]
                    if task.task_type not in ("dataset", "crop")
                    else []
                ),
            )
            for task in project_info.pipeline.tasks
        ],
    )

    context.project_info = projects_api.edit_project(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        project_id=context.project_id,
        edit_project_request=EditProjectRequest(
            id=context.project_id,
            name=context.project_info.name,
            pipeline=edit_pipeline,
        ),
    )


@when("the user deletes label '{label_name}'")
def step_when_user_deletes_label(context: Context, label_name: str) -> None:
    """
    Removes the passed label from the pipeline and updates the project via a PUT request.
    """
    projects_api: ProjectsApi = context.projects_api
    project_info: CreateProject201Response = context.project_info
    edit_pipeline = EditProjectRequestPipeline(
        connections=[
            EditProjectRequestPipelineConnectionsInner(var_from=conn.var_from, to=conn.to)
            for conn in project_info.pipeline.connections
        ],
        tasks=[
            EditProjectRequestPipelineTasksInner(
                id=task.id,
                title=task.title,
                task_type=task.task_type,
                labels=[
                    EditProjectRequestPipelineTasksInnerLabelsInner(
                        id=label.id,
                        name=label.name,
                        color=label.color,
                        group=label.group,
                        is_empty=label.is_empty,
                        is_anomalous=label.is_anomalous,
                        parent_id=label.parent_id,
                        is_deleted=label.name == label_name,
                    )
                    for label in task.labels
                    if not label.is_empty
                ]
                if task.labels
                else [],
            )
            for task in project_info.pipeline.tasks
        ],
    )

    response = projects_api.edit_project(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        project_id=context.project_id,
        edit_project_request=EditProjectRequest(
            id=context.project_id,
            name=context.project_info.name,
            pipeline=edit_pipeline,
        ),
    )
    context.project_info = response


@when("the user tries to delete label '{label_name}'")
def step_when_user_tries_deleting_label(context: Context, label_name: str) -> None:
    try:
        step_when_user_deletes_label(context=context, label_name=label_name)
    except Exception as e:
        context.exception = e


@when("the user adds a new label '{new_label_name}'")
def step_when_user_adds_label(context: Context, new_label_name: str) -> None:
    _add_label(context=context, new_label_name=new_label_name)


@when("the user tries to add a new label '{new_label_name}'")
def step_when_user_tries_adding_label(context: Context, new_label_name: str) -> None:
    try:
        _add_label(context=context, new_label_name=new_label_name)
    except Exception as e:
        context.exception = e


@then("the project has labels '{raw_label_names}'")
def step_then_project_has_labels(context: Context, raw_label_names: str) -> None:
    """
    Verifies that the project has the expected "raw_label_names" via a GET request.
    """
    projects_api: ProjectsApi = context.projects_api

    # Fetch information about the project and its labels
    context.project_info = projects_api.get_project_info(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        project_id=context.project_id,
    )

    # Verify that the project has the expected labels (plus the empty label, if applicable)
    expected_label_names = set(raw_label_names.split(", "))
    if empty_label_name := PROJECT_TYPE_TO_EMPTY_LABEL_NAME_MAPPING.get(context.project_type):
        expected_label_names.add(empty_label_name)
    found_label_names = {
        label.name
        for task in context.project_info.pipeline.tasks
        if task.task_type not in ("dataset", "crop")
        for label in task.labels
    }
    assert found_label_names == expected_label_names, (
        f"Expected labels: {expected_label_names}, found: {found_label_names}"
    )
