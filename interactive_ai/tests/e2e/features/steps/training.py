# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from behave import step, then, when
from behave.runner import Context
from geti_client import ModelsApi, TrainJob, TrainModelRequest
from static_definitions import TaskType


def _train(
    context: Context,
    model_type: str | None = None,
    task_type: str | None = None,
    from_scratch: bool = False,
) -> None:
    models_api: ModelsApi = context.models_api
    task_id = next(
        (
            task.id
            for task in context.project_info.pipeline.tasks
            if task.labels and (not task_type or TaskType(task.task_type) == TaskType(task_type))
        ),
        None,
    )
    if not task_id:
        raise ValueError("Could not find task to train in project")

    train_response = models_api.train_model(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        project_id=context.project_id,
        train_model_request=TrainModelRequest(
            model_template_id=model_type,
            task_id=task_id,
            train_from_scratch=from_scratch,
        ),
    )
    context.job_id = train_response.job_id


@step("the user requests to train a model")
def step_when_user_trains_model(context: Context):
    _train(context=context)


@when("the user requests to train a model of type '{model_type}'")
def step_when_user_trains_model_of_type(context: Context, model_type: str):
    _train(context=context, model_type=model_type)


@then("a model of type '{expected_model_type}' is created")
def step_then_model_created(context: Context, expected_model_type: str):
    train_job_info: TrainJob = context.job_info.actual_instance

    context.model_storage_id = train_job_info.metadata.trained_model.model_storage_id
    context.model_id = train_job_info.metadata.trained_model.model_id

    models_api: ModelsApi = context.models_api
    context.model_storage_info = models_api.get_model_group(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        project_id=context.project_id,
        model_group_id=context.model_storage_id,
    )
    context.model_info = models_api.get_model_detail(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        project_id=context.project_id,
        model_group_id=context.model_storage_id,
        model_id=context.model_id,
    )

    trained_model_type = context.model_storage_info.model_template_id
    assert trained_model_type == expected_model_type, (
        f"The trained model does not have the expected architecture (expected '{expected_model_type}', found '{trained_model_type}')"  # noqa: E501
    )


@then("the model has training-time statistics")
def step_then_model_has_training_time_statistics(context: Context):
    models_api: ModelsApi = context.models_api

    model_statistics = models_api.get_model_statistics(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        project_id=context.project_id,
        model_group_id=context.model_storage_id,
        model_id=context.model_id,
    ).model_statistics

    available_headers = {statistic.header for statistic in model_statistics}
    is_anomaly_project = any(
        TaskType(task.task_type) is TaskType.ANOMALY for task in context.project_info.pipeline.tasks if task.labels
    )

    assert "Training date" in available_headers, "Training date is missing from model statistics"
    assert "Training job duration" in available_headers, "Training job duration is missing from model statistics"
    assert "Training duration" in available_headers, "Training duration is missing from model statistics"
    assert "Dataset split" in available_headers, "Dataset split is missing from model statistics"
    if not is_anomaly_project:  # Some anomaly models do not output loss statistics
        assert any("loss" in h.lower() for h in available_headers), "Loss statistics are missing"


@then("the model has a training dataset")
def step_then_model_has_training_dataset(context: Context):
    assert context.model_info.training_dataset_info is not None, "Model does not have a training dataset"


@then("the model lifecycle stage is {lifecycle_stage}")
def step_then_model_lifecycle_is(context: Context, lifecycle_stage: str):
    assert context.model_info.lifecycle_stage == lifecycle_stage, (
        f"Model is not in the expected lifecycle stage (expected '{lifecycle_stage}', found '{context.model_info.lifecycle_stage}'."  # noqa: E501
    )
