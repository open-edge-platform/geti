# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import MagicMock, patch

import pytest
from bson import ObjectId
from flytekit.exceptions.user import FlyteUserException

from model.job import JobStepDetails, JobTaskExecutionBranch
from model.job_state import JobTaskState
from scheduler.flyte import ExecutionType, Flyte
from scheduler.jobs_templates import JobsTemplates, JobTemplateStep
from scheduler.loops.scheduling import (
    FlyteWorkflowNotFound,
    run_scheduling_loop,
    schedule_main_job,
    start_execution,
    start_main_execution,
)
from scheduler.state_machine import StateMachine

from geti_types import ID

ORG = ID(ObjectId())
job_id = ID("test_job")


def mock_flyte_client(self, *args, **kwargs) -> None:
    self.client = MagicMock()
    self.client.client = MagicMock()


def mock_state_machine(self, *args, **kwargs) -> None:
    return None


def mock_jobs_templates(self, *args, **kwargs) -> None:
    return None


def reset_singletons() -> None:
    Flyte._instance = None  # type: ignore[attr-defined]
    StateMachine._instance = None  # type: ignore[attr-defined]
    JobsTemplates._instance = None  # type: ignore[attr-defined]


@patch(
    "scheduler.loops.scheduling.schedule_main_job",
)
@patch.object(StateMachine, "find_and_lock_job_for_scheduling")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_run_revert_scheduling_loop_none(
    mock_find_and_lock_job_for_scheduling,
    mock_schedule_main_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_find_and_lock_job_for_scheduling.return_value = None

    # Act
    run_scheduling_loop()

    # Assert
    mock_schedule_main_job.assert_not_called()


@patch(
    "scheduler.loops.scheduling.schedule_main_job",
)
@patch(
    "scheduler.loops.scheduling.session_context",
)
@patch.object(StateMachine, "find_and_lock_job_for_scheduling")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_run_revert_scheduling_loop_schedule_revert_job(
    mock_find_and_lock_job_for_scheduling,
    mock_session_context,
    mock_schedule_main_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job = MagicMock()
    mock_find_and_lock_job_for_scheduling.side_effect = [job, None]

    # Act
    run_scheduling_loop()

    # Assert
    mock_session_context.assert_called_once_with(session=job.session)
    mock_schedule_main_job.assert_called_once_with(job_id=job.id)


@patch.object(JobsTemplates, "get_job_steps")
@patch(
    "scheduler.loops.scheduling.start_main_execution",
)
@patch.object(StateMachine, "set_and_publish_failed_state")
@patch.object(StateMachine, "set_scheduled_state")
@patch.object(StateMachine, "reset_scheduling_job")
@patch.object(StateMachine, "get_by_id")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_schedule_main_job_not_found(
    mock_js_get_by_id,
    mock_js_reset_scheduling_job,
    mock_js_set_scheduled_state,
    mock_js_set_and_publish_failed_state,
    mock_start_main_execution,
    mock_get_job_steps,
    fxt_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_js_get_by_id.return_value = None

    # Act
    schedule_main_job(job_id=job_id)

    # Assert
    mock_js_get_by_id.assert_called_once_with(job_id=job_id)
    mock_js_reset_scheduling_job.assert_not_called()
    mock_js_set_scheduled_state.assert_not_called()
    mock_js_set_and_publish_failed_state.assert_not_called()
    mock_start_main_execution.assert_not_called()
    mock_get_job_steps.assert_not_called()


@patch.object(JobsTemplates, "get_job_steps")
@patch(
    "scheduler.loops.scheduling.start_main_execution",
    side_effect=FlyteUserException("Failed to start execution"),
)
@patch.object(StateMachine, "set_and_publish_failed_state")
@patch.object(StateMachine, "set_scheduled_state")
@patch.object(StateMachine, "reset_scheduling_job")
@patch.object(StateMachine, "get_by_id")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_schedule_main_job_failure(
    mock_js_get_by_id,
    mock_js_reset_scheduling_job,
    mock_js_set_scheduled_state,
    mock_js_set_and_publish_failed_state,
    mock_start_main_execution,
    mock_get_job_steps,
    fxt_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_js_get_by_id.return_value = fxt_job

    # Act
    schedule_main_job(job_id=job_id)

    # Assert
    mock_js_get_by_id.assert_called_once_with(job_id=job_id)
    mock_js_reset_scheduling_job.assert_called_once_with(job_id=job_id)
    mock_js_set_scheduled_state.assert_not_called()
    mock_js_set_and_publish_failed_state.assert_not_called()
    mock_start_main_execution.assert_called_once_with(job=fxt_job)
    mock_get_job_steps.assert_not_called()


@patch.object(JobsTemplates, "get_job_steps")
@patch.object(JobsTemplates, "__init__", new=mock_jobs_templates)
@patch("scheduler.loops.scheduling.start_main_execution")
@patch.object(StateMachine, "set_and_publish_failed_state")
@patch.object(StateMachine, "set_scheduled_state")
@patch.object(StateMachine, "reset_scheduling_job")
@patch.object(StateMachine, "get_by_id")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_schedule_main_job_success(
    mock_js_get_by_id,
    mock_js_reset_scheduling_job,
    mock_js_set_scheduled_state,
    mock_js_set_and_publish_failed_state,
    mock_start_main_execution,
    mock_get_job_steps,
    fxt_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_js_get_by_id.return_value = fxt_job

    workflow = MagicMock()
    execution = MagicMock()
    mock_start_main_execution.return_value = workflow, execution

    step_details = [
        JobTemplateStep(name="Test task 1", task_id="task_id_1"),
        JobTemplateStep(
            name="Test task 2",
            task_id="task_id_2",
            branches=[
                {
                    "condition": "condition",
                    "branch": "branch",
                    "skip_message": "Step is skipped",
                }
            ],
        ),
    ]
    mock_get_job_steps.return_value = step_details

    # Act
    schedule_main_job(job_id=job_id)

    # Assert
    mock_js_get_by_id.assert_called_once_with(job_id=job_id)
    mock_js_reset_scheduling_job.assert_not_called()
    mock_js_set_scheduled_state.assert_called_once_with(
        job_id=job_id,
        flyte_launch_plan_id=execution.spec.launch_plan.name,
        flyte_execution_id=execution.id.name,
        step_details=[
            JobStepDetails(
                index=1,
                task_id="task_id_1",
                step_name="Test task 1",
                state=JobTaskState.WAITING,
                progress=-1,
            ),
            JobStepDetails(
                index=2,
                task_id="task_id_2",
                step_name="Test task 2",
                state=JobTaskState.WAITING,
                branches=(JobTaskExecutionBranch(condition="condition", branch="branch"),),
                progress=-1,
            ),
        ],
    )
    mock_js_set_and_publish_failed_state.assert_not_called()
    mock_start_main_execution.assert_called_once_with(job=fxt_job)
    mock_get_job_steps.assert_called_once_with(job_type=fxt_job.type)


@patch.object(JobsTemplates, "get_job_steps")
@patch("scheduler.loops.scheduling.start_main_execution")
@patch.object(StateMachine, "set_and_publish_failed_state")
@patch.object(StateMachine, "set_scheduled_state")
@patch.object(StateMachine, "reset_scheduling_job")
@patch.object(StateMachine, "get_by_id")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_schedule_main_job_max_retry_counter(
    mock_js_get_by_id,
    mock_js_reset_scheduling_job,
    mock_js_set_scheduled_state,
    mock_js_set_and_publish_failed_state,
    mock_start_main_execution,
    mock_get_job_steps,
    fxt_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    fxt_job.executions.main.start_retry_counter = 10
    mock_js_get_by_id.return_value = fxt_job

    execution = MagicMock()
    mock_start_main_execution.return_value = execution

    # Act
    schedule_main_job(job_id=job_id)

    # Assert
    mock_js_get_by_id.assert_called_once_with(job_id=job_id)
    mock_js_reset_scheduling_job.assert_not_called()
    mock_js_set_scheduled_state.assert_not_called()
    mock_js_set_and_publish_failed_state.assert_called_once_with(job_id=job_id)
    mock_start_main_execution.assert_not_called()
    mock_get_job_steps.assert_not_called()


@patch(
    "scheduler.loops.scheduling.start_execution",
)
@patch(
    "scheduler.loops.scheduling.resolve_main_job",
)
@patch(
    "scheduler.loops.scheduling.get_main_execution_name",
)
@patch.object(Flyte, "fetch_workflow")
@patch.object(Flyte, "__init__", new=mock_flyte_client)
def test_start_main_execution_no_workflow(
    mock_flyte_fetch_workflow,
    mock_get_main_execution_name,
    mock_resolve_main_job,
    mock_start_execution,
    fxt_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_get_main_execution_name.return_value = "execution_name"
    mock_resolve_main_job.return_value = ("workflow_name", "workflow_version")
    mock_flyte_fetch_workflow.return_value = None

    # Act
    with pytest.raises(FlyteWorkflowNotFound):
        start_main_execution(job=fxt_job)

    # Assert
    mock_flyte_fetch_workflow.assert_called_once_with(
        workflow_name="workflow_name", workflow_version="workflow_version"
    )
    mock_get_main_execution_name.assert_called_once_with(job_id=fxt_job.id)
    mock_resolve_main_job.assert_called_once_with(job_type=fxt_job.type)
    mock_start_execution.assert_not_called()


@patch(
    "scheduler.loops.scheduling.start_execution",
)
@patch(
    "scheduler.loops.scheduling.resolve_main_job",
)
@patch(
    "scheduler.loops.scheduling.get_main_execution_name",
)
@patch.object(Flyte, "fetch_workflow")
@patch.object(Flyte, "__init__", new=mock_flyte_client)
def test_start_main_execution(
    mock_flyte_fetch_workflow,
    mock_get_main_execution_name,
    mock_resolve_main_job,
    mock_start_execution,
    fxt_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_get_main_execution_name.return_value = "execution_name"
    mock_resolve_main_job.return_value = ("workflow_name", "workflow_version")

    workflow = MagicMock()
    mock_flyte_fetch_workflow.return_value = workflow

    execution = MagicMock()
    mock_start_execution.return_value = execution

    # Act
    result_workflow, result_exectuion = start_main_execution(job=fxt_job)

    # Assert
    mock_flyte_fetch_workflow.assert_called_once_with(
        workflow_name="workflow_name", workflow_version="workflow_version"
    )
    mock_get_main_execution_name.assert_called_once_with(job_id=fxt_job.id)
    mock_resolve_main_job.assert_called_once_with(job_type=fxt_job.type)
    mock_start_execution.assert_called_once_with(
        job=fxt_job,
        workflow=workflow,
        execution_type=ExecutionType.MAIN,
        execution_name="execution_name",
        payload=fxt_job.payload,
    )
    assert result_workflow == workflow
    assert result_exectuion == execution


@patch.object(Flyte, "start_workflow_execution")
@patch.object(Flyte, "fetch_workflow_execution")
@patch.object(Flyte, "__init__", new=mock_flyte_client)
def test_start_execution_existing(
    mock_flyte_fetch_workflow_execution,
    mock_flyte_start_workflow_execution,
    fxt_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    workflow = MagicMock()

    execution = MagicMock()
    mock_flyte_fetch_workflow_execution.return_value = execution

    # Act
    result = start_execution(
        job=fxt_job,
        workflow=workflow,
        execution_type=ExecutionType.MAIN,
        execution_name="execution_name",
        payload={"key": "value"},
    )

    # Assert
    mock_flyte_fetch_workflow_execution.assert_called_once_with(execution_name="execution_name")
    mock_flyte_start_workflow_execution.assert_not_called()
    assert result == execution


@patch.object(Flyte, "start_workflow_execution")
@patch.object(Flyte, "fetch_workflow_execution")
@patch.object(Flyte, "__init__", new=mock_flyte_client)
def test_start_execution_new(
    mock_flyte_fetch_workflow_execution,
    mock_flyte_start_workflow_execution,
    fxt_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    workflow = MagicMock()
    execution = MagicMock()

    mock_flyte_fetch_workflow_execution.return_value = None
    mock_flyte_start_workflow_execution.return_value = execution

    # Act
    result = start_execution(
        job=fxt_job,
        workflow=workflow,
        execution_type=ExecutionType.MAIN,
        execution_name="execution_name",
        payload={"key": "value"},
    )

    # Assert
    mock_flyte_fetch_workflow_execution.assert_called_once_with(execution_name="execution_name")
    mock_flyte_start_workflow_execution.assert_called_once_with(
        workspace_id=fxt_job.workspace_id,
        job=fxt_job,
        project_id=fxt_job.project_id,
        execution_type=ExecutionType.MAIN,
        execution_name="execution_name",
        workflow=workflow,
        payload={"key": "value"},
        telemetry=fxt_job.telemetry,
        session=fxt_job.session,
    )
    assert result == execution
