# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

from model.job import (
    Job,
    JobCancellationInfo,
    JobConsumedResource,
    JobCost,
    JobFlyteExecutions,
    JobGpuRequest,
    JobMainFlyteExecution,
    JobResource,
    JobRevertFlyteExecution,
    JobStepDetails,
    JobTaskExecutionBranch,
)
from model.job_state import JobGpuRequestState, JobState, JobStateGroup, JobTaskState
from model.mapper.job_mapper import (
    JobConsumedResourceMapper,
    JobCostMapper,
    JobMapper,
    JobResourceMapper,
    JobStepDetailsMapper,
    JobTaskExecutionBranchMapper,
)
from model.telemetry import Telemetry

from geti_types import ID, Session
from iai_core.utils.time_utils import now


def assert_jobs_equal_deep(job1: Job, job2: Job) -> None:
    assert (
        job1.id == job2.id
        and job1.workspace_id == job2.workspace_id
        and job1.type == job2.type
        and job1.priority == job2.priority
        and job1.job_name == job2.job_name
        and job1.key == job2.key
        and job1.state == job2.state
        and job1.state_group == job2.state_group
        and job1.step_details == job2.step_details
        and job1.payload == job2.payload
        and job1.metadata == job2.metadata
        and job1.creation_time == job2.creation_time
        and job1.author == job2.author
        and job1.project_id == job2.project_id
        and job1.start_time == job2.start_time
        and job1.end_time == job2.end_time
        and job1.cancellation_info == job2.cancellation_info
        and job1.executions == job2.executions
        and job1.session.as_json() == job2.session.as_json()
        and job1.telemetry == job2.telemetry
        and job1.gpu == job2.gpu
        and job1.cost == job2.cost
    )


class TestJobTaskExecutionBranchMapper:
    @pytest.mark.parametrize(
        "document",
        [
            {},
            {"condition": "condition"},
            {"branch": "branch"},
        ],
        ids=["empty", "no_branch", "no_condition"],
    )
    def test_backward_error(self, document) -> None:
        with pytest.raises(KeyError):
            JobTaskExecutionBranchMapper.backward(document)

    def test_backward(self) -> None:
        task_execution_branch = JobTaskExecutionBranchMapper.backward({"condition": "condition", "branch": "branch"})
        assert task_execution_branch == JobTaskExecutionBranch(condition="condition", branch="branch")

    def test_forward(self) -> None:
        dict = JobTaskExecutionBranchMapper.forward(JobTaskExecutionBranch(condition="condition", branch="branch"))
        assert dict == {"condition": "condition", "branch": "branch"}


class TestJobStepDetailsMapper:
    @pytest.mark.parametrize(
        "document",
        [
            {},
            {"task_id": "Test task", "step_name": "Test name", "state": "WAITING"},
            {"index": 1, "step_name": "Test name", "state": "WAITING"},
            {"index": 1, "task_id": "Test task", "state": "WAITING"},
            {"index": 1, "task_id": "Test task", "step_name": "Test name"},
        ],
        ids=["empty", "no_step", "no_task_id", "no_step_name", "no_state"],
    )
    def test_backward_error(self, document) -> None:
        with pytest.raises(KeyError):
            JobStepDetailsMapper.backward(document)

    def test_backward_mandatory(self) -> None:
        step_details = JobStepDetailsMapper.backward(
            {
                "index": 1,
                "task_id": "Test task",
                "step_name": "Test name",
                "state": "WAITING",
            }
        )
        assert step_details == JobStepDetails(
            index=1,
            task_id="Test task",
            step_name="Test name",
            state=JobTaskState.WAITING,
        )

    def test_backward_full(self) -> None:
        start_time = now()
        end_time = now()
        step_details = JobStepDetailsMapper.backward(
            {
                "index": 1,
                "task_id": "Test task",
                "step_name": "Test name",
                "state": "WAITING",
                "progress": 40.6,
                "message": "Test message",
                "branches": [{"condition": "condition", "branch": "branch"}],
                "start_time": start_time,
                "end_time": end_time,
                "warning": "Warning message",
            }
        )
        assert step_details == JobStepDetails(
            index=1,
            task_id="Test task",
            step_name="Test name",
            state=JobTaskState.WAITING,
            progress=40.6,
            message="Test message",
            branches=(JobTaskExecutionBranch(condition="condition", branch="branch"),),
            start_time=start_time,
            end_time=end_time,
            warning="Warning message",
        )

    def test_forward_mandatory(self) -> None:
        dict = JobStepDetailsMapper.forward(
            JobStepDetails(
                index=1,
                task_id="Test task",
                step_name="Test name",
                state=JobTaskState.WAITING,
            )
        )
        assert dict == {
            "index": 1,
            "task_id": "Test task",
            "step_name": "Test name",
            "state": "WAITING",
            "progress": -1,
        }

    def test_forward_full(self) -> None:
        start_time = now()
        end_time = now()
        dict = JobStepDetailsMapper.forward(
            JobStepDetails(
                index=1,
                task_id="Test task",
                step_name="Test name",
                state=JobTaskState.WAITING,
                progress=40.6,
                message="Test message",
                branches=(JobTaskExecutionBranch(condition="condition", branch="branch"),),
                start_time=start_time,
                end_time=end_time,
                warning="Warning message",
            )
        )
        assert dict == {
            "index": 1,
            "task_id": "Test task",
            "step_name": "Test name",
            "state": "WAITING",
            "progress": 40.6,
            "message": "Test message",
            "branches": [{"condition": "condition", "branch": "branch"}],
            "start_time": start_time,
            "end_time": end_time,
            "warning": "Warning message",
        }


class TestJobResourceMapper:
    @pytest.mark.parametrize(
        "document",
        [
            {},
            {"unit": "images"},
            {"amount": 100},
        ],
        ids=["empty", "no_amount", "no_unit"],
    )
    def test_backward_error(self, document) -> None:
        with pytest.raises(KeyError):
            JobResourceMapper.backward(document)

    def test_backward_full(self) -> None:
        job_resource = JobResourceMapper.backward({"amount": 100, "unit": "images"})
        assert job_resource == JobResource(amount=100, unit="images")

    def test_forward_full(self) -> None:
        dict = JobResourceMapper.forward(JobResource(amount=100, unit="images"))
        assert dict == {"amount": 100, "unit": "images"}


class TestJobConsumedResourceMapper:
    @pytest.mark.parametrize(
        "document",
        [
            {},
            {"unit": "images", "consuming_date": now(), "service": "training"},
            {"amount": 100, "consuming_date": now(), "service": "training"},
            {"amount": 100, "unit": "images", "service": "training"},
        ],
        ids=["empty", "no_amount", "no_unit", "no_consuming_date"],
    )
    def test_backward_error(self, document) -> None:
        with pytest.raises(KeyError):
            JobConsumedResourceMapper.backward(document)

    def test_backward_no_service(self) -> None:
        consuming_date = now()
        job_consumed_resource = JobConsumedResourceMapper.backward(
            {"amount": 100, "unit": "images", "consuming_date": consuming_date}
        )
        assert job_consumed_resource == JobConsumedResource(
            amount=100, unit="images", consuming_date=consuming_date, service="unknown"
        )

    def test_backward_full(self) -> None:
        consuming_date = now()
        job_consumed_resource = JobConsumedResourceMapper.backward(
            {
                "amount": 100,
                "unit": "images",
                "consuming_date": consuming_date,
                "service": "training",
            }
        )
        assert job_consumed_resource == JobConsumedResource(
            amount=100, unit="images", consuming_date=consuming_date, service="training"
        )

    def test_forward_full(self) -> None:
        consuming_date = now()
        dict = JobConsumedResourceMapper.forward(
            JobConsumedResource(
                amount=100,
                unit="images",
                consuming_date=consuming_date,
                service="training",
            )
        )
        assert dict == {
            "amount": 100,
            "unit": "images",
            "consuming_date": consuming_date,
            "service": "training",
        }


class TestJobCostMapper:
    @pytest.mark.parametrize(
        "document",
        [
            {},
            {
                "lease_id": "7d227a60-96f7-4294-bc0a-2fd07debe9d2",
                "consumed": [],
                "reported": False,
            },
            {"resources": [], "consumed": [], "reported": False},
            {
                "resources": [],
                "lease_id": "7d227a60-96f7-4294-bc0a-2fd07debe9d2",
                "reported": False,
            },
            {
                "resources": [],
                "lease_id": "7d227a60-96f7-4294-bc0a-2fd07debe9d2",
                "consumed": [],
            },
        ],
        ids=["empty", "no_resources", "no_lease_id", "no_consumed", "no_reported"],
    )
    def test_backward_error(self, document) -> None:
        with pytest.raises(KeyError):
            JobCostMapper.backward(document)

    def test_backward_full(self) -> None:
        consuming_date = now()
        job_cost = JobCostMapper.backward(
            {
                "requests": [{"amount": 100, "unit": "images"}],
                "lease_id": "7d227a60-96f7-4294-bc0a-2fd07debe9d2",
                "consumed": [
                    {
                        "amount": 100,
                        "unit": "images",
                        "consuming_date": consuming_date,
                        "service": "training",
                    }
                ],
                "reported": False,
            }
        )
        assert job_cost == JobCost(
            requests=(JobResource(amount=100, unit="images"),),
            lease_id="7d227a60-96f7-4294-bc0a-2fd07debe9d2",
            consumed=(
                JobConsumedResource(
                    amount=100,
                    unit="images",
                    consuming_date=consuming_date,
                    service="training",
                ),
            ),
            reported=False,
        )

    def test_forward_full(self) -> None:
        consuming_date = now()
        dict = JobCostMapper.forward(
            JobCost(
                requests=(JobResource(amount=100, unit="images"),),
                lease_id="7d227a60-96f7-4294-bc0a-2fd07debe9d2",
                consumed=(
                    JobConsumedResource(
                        amount=100,
                        unit="images",
                        consuming_date=consuming_date,
                        service="training",
                    ),
                ),
                reported=True,
            )
        )
        assert dict == {
            "requests": [{"amount": 100, "unit": "images"}],
            "lease_id": "7d227a60-96f7-4294-bc0a-2fd07debe9d2",
            "consumed": [
                {
                    "amount": 100,
                    "unit": "images",
                    "consuming_date": consuming_date,
                    "service": "training",
                }
            ],
            "reported": True,
        }


class TestJobMapper:
    @pytest.mark.parametrize(
        "document",
        [
            {},
            {
                "workspace_id": "workspace",
                "type": "train",
                "priority": 0,
                "job_name": "Train",
                "key": "job_key",
                "state": 0,
                "state_group": "SCHEDULED",
                "cancellation_info": {"is_cancelled": False},
                "step_details": [],
                "payload": {"workspace_id": "workspace"},
                "creation_time": now(),
                "author": "author_uid",
                "telemetry": {"context": ""},
                "session": {
                    "organization_id": "000000000000000000000001",
                    "workspace_id": "63b183d00000000000000001",
                },
            },
            {
                "id": "job_id",
                "type": "train",
                "priority": 0,
                "job_name": "Train",
                "key": "job_key",
                "state": 0,
                "state_group": "SCHEDULED",
                "cancellation_info": {"is_cancelled": False},
                "step_details": [],
                "payload": {"workspace_id": "workspace"},
                "creation_time": now(),
                "author": "author_uid",
                "telemetry": {"context": ""},
                "session": {
                    "organization_id": "000000000000000000000001",
                    "workspace_id": "63b183d00000000000000001",
                },
            },
            {
                "id": "job_id",
                "workspace_id": "workspace",
                "priority": 0,
                "job_name": "Train",
                "key": "job_key",
                "state": 0,
                "state_group": "SCHEDULED",
                "cancellation_info": {"is_cancelled": False},
                "step_details": [],
                "payload": {"workspace_id": "workspace"},
                "creation_time": now(),
                "author": "author_uid",
                "telemetry": {"context": ""},
                "session": {
                    "organization_id": "000000000000000000000001",
                    "workspace_id": "63b183d00000000000000001",
                },
            },
            {
                "id": "job_id",
                "workspace_id": "workspace",
                "type": "train",
                "job_name": "Train",
                "key": "job_key",
                "state": 0,
                "state_group": "SCHEDULED",
                "cancellation_info": {"is_cancelled": False},
                "step_details": [],
                "payload": {"workspace_id": "workspace"},
                "creation_time": now(),
                "author": "author_uid",
                "telemetry": {"context": ""},
                "session": {
                    "organization_id": "000000000000000000000001",
                    "workspace_id": "63b183d00000000000000001",
                },
            },
            {
                "id": "job_id",
                "workspace_id": "workspace",
                "type": "train",
                "priority": 0,
                "key": "job_key",
                "state": 0,
                "state_group": "SCHEDULED",
                "cancellation_info": {"is_cancelled": False},
                "step_details": [],
                "payload": {"workspace_id": "workspace"},
                "creation_time": now(),
                "author": "author_uid",
                "telemetry": {"context": ""},
                "session": {
                    "organization_id": "000000000000000000000001",
                    "workspace_id": "63b183d00000000000000001",
                },
            },
            {
                "id": "job_id",
                "workspace_id": "workspace",
                "type": "train",
                "priority": 0,
                "job_name": "Train",
                "state": 0,
                "state_group": "SCHEDULED",
                "cancellation_info": {"is_cancelled": False},
                "step_details": [],
                "payload": {"workspace_id": "workspace"},
                "creation_time": now(),
                "author": "author_uid",
                "telemetry": {"context": ""},
                "session": {
                    "organization_id": "000000000000000000000001",
                    "workspace_id": "63b183d00000000000000001",
                },
            },
            {
                "id": "job_id",
                "workspace_id": "workspace",
                "type": "train",
                "priority": 0,
                "job_name": "Train",
                "key": "job_key",
                "state_group": "SCHEDULED",
                "cancellation_info": {"is_cancelled": False},
                "step_details": [],
                "payload": {"workspace_id": "workspace"},
                "creation_time": now(),
                "author": "author_uid",
                "telemetry": {"context": ""},
                "session": {
                    "organization_id": "000000000000000000000001",
                    "workspace_id": "63b183d00000000000000001",
                },
            },
            {
                "id": "job_id",
                "workspace_id": "workspace",
                "type": "train",
                "priority": 0,
                "job_name": "Train",
                "key": "job_key",
                "state": 0,
                "cancellation_info": {"is_cancelled": False},
                "step_details": [],
                "payload": {"workspace_id": "workspace"},
                "creation_time": now(),
                "author": "author_uid",
                "telemetry": {"context": ""},
                "session": {
                    "organization_id": "000000000000000000000001",
                    "workspace_id": "63b183d00000000000000001",
                },
            },
            {
                "id": "job_id",
                "workspace_id": "workspace",
                "type": "train",
                "priority": 0,
                "job_name": "Train",
                "key": "job_key",
                "state": 0,
                "state_group": "SCHEDULED",
                "step_details": [],
                "payload": {"workspace_id": "workspace"},
                "creation_time": now(),
                "author": "author_uid",
                "telemetry": {"context": ""},
                "session": {
                    "organization_id": "000000000000000000000001",
                    "workspace_id": "63b183d00000000000000001",
                },
            },
            {
                "id": "job_id",
                "workspace_id": "workspace",
                "type": "train",
                "priority": 0,
                "job_name": "Train",
                "key": "job_key",
                "state": 0,
                "state_group": "SCHEDULED",
                "cancellation_info": {"is_cancelled": False},
                "payload": {"workspace_id": "workspace"},
                "creation_time": now(),
                "author": "author_uid",
                "telemetry": {"context": ""},
                "session": {
                    "organization_id": "000000000000000000000001",
                    "workspace_id": "63b183d00000000000000001",
                },
            },
            {
                "id": "job_id",
                "workspace_id": "workspace",
                "type": "train",
                "priority": 0,
                "job_name": "Train",
                "key": "job_key",
                "state": 0,
                "state_group": "SCHEDULED",
                "cancellation_info": {"is_cancelled": False},
                "step_details": [],
                "creation_time": now(),
                "author": "author_uid",
                "telemetry": {"context": ""},
                "session": {
                    "organization_id": "000000000000000000000001",
                    "workspace_id": "63b183d00000000000000001",
                },
            },
            {
                "id": "job_id",
                "workspace_id": "workspace",
                "type": "train",
                "priority": 0,
                "job_name": "Train",
                "key": "job_key",
                "state": 0,
                "state_group": "SCHEDULED",
                "cancellation_info": {"is_cancelled": False},
                "step_details": [],
                "payload": {"workspace_id": "workspace"},
                "author": "author_uid",
                "telemetry": {"context": ""},
                "session": {
                    "organization_id": "000000000000000000000001",
                    "workspace_id": "63b183d00000000000000001",
                },
            },
            {
                "id": "job_id",
                "workspace_id": "workspace",
                "type": "train",
                "priority": 0,
                "job_name": "Train",
                "key": "job_key",
                "state": 0,
                "state_group": "SCHEDULED",
                "cancellation_info": {"is_cancelled": False},
                "step_details": [],
                "payload": {"workspace_id": "workspace"},
                "creation_time": now(),
                "telemetry": {"context": ""},
                "session": {
                    "organization_id": "000000000000000000000001",
                    "workspace_id": "63b183d00000000000000001",
                },
            },
            {
                "id": "job_id",
                "workspace_id": "workspace",
                "type": "train",
                "priority": 0,
                "job_name": "Train",
                "key": "job_key",
                "state": 0,
                "state_group": "SCHEDULED",
                "cancellation_info": {"is_cancelled": False},
                "step_details": [],
                "payload": {"workspace_id": "workspace"},
                "author": "author_uid",
                "creation_time": now(),
                "telemetry": {"context": ""},
            },
        ],
        ids=[
            "empty",
            "no_id",
            "no_workspace_id",
            "no_type",
            "no_priority",
            "no_job_name",
            "no_key",
            "no_state",
            "no_state_group",
            "no_cancelled",
            "no_progress",
            "no_payload",
            "no_creation_time",
            "no_author",
            "no_session",
        ],
    )
    def test_backward_error(self, document) -> None:
        with pytest.raises(KeyError):
            JobMapper.backward(document)

    def test_mandatory(self) -> None:
        creation_time = now()
        job = JobMapper.backward(
            {
                "_id": "job_id",
                "workspace_id": "workspace",
                "type": "train",
                "priority": 0,
                "job_name": "Train",
                "key": "job_key",
                "state": 0,
                "state_group": "SCHEDULED",
                "cancellation_info": {"is_cancelled": False},
                "step_details": [],
                "payload": {"workspace_id": "workspace"},
                "metadata": {"project_name": "test_project"},
                "creation_time": creation_time,
                "author": "author_uid",
                "executions": {"main": {}},
                "session": {
                    "organization_id": "000000000000000000000001",
                    "workspace_id": "63b183d00000000000000001",
                },
                "telemetry": {"context": ""},
            }
        )
        job_dict = JobMapper.forward(job)
        assert_jobs_equal_deep(
            job,
            Job(
                id=ID("job_id"),
                workspace_id=ID("workspace"),
                type="train",
                priority=0,
                job_name="Train",
                key="job_key",
                state=JobState.SUBMITTED,
                state_group=JobStateGroup.SCHEDULED,
                step_details=(),
                payload={"workspace_id": "workspace"},
                metadata={"project_name": "test_project"},
                creation_time=creation_time,
                author=ID("author_uid"),
                cancellation_info=JobCancellationInfo(cancellable=True, is_cancelled=False),
                executions=JobFlyteExecutions(main=JobMainFlyteExecution()),
                session=Session(
                    organization_id=ID("000000000000000000000001"),
                    workspace_id=ID("63b183d00000000000000001"),
                ),
                telemetry=Telemetry(),
            ),
        )
        assert_jobs_equal_deep(JobMapper.backward(job_dict), job)

    def test_full(self) -> None:
        current_timestamp = now()
        job = JobMapper.backward(
            {
                "_id": "job_id",
                "workspace_id": "workspace",
                "type": "train",
                "priority": 0,
                "job_name": "Train",
                "key": "job_key",
                "state": 0,
                "state_group": "SCHEDULED",
                "step_details": [],
                "payload": {"workspace_id": "workspace"},
                "metadata": {"project_name": "test_project"},
                "creation_time": current_timestamp,
                "author": "author_uid",
                "project_id": "project",
                "process_start_time": current_timestamp,
                "start_time": current_timestamp,
                "end_time": current_timestamp,
                "start_retry_counter": 2,
                "flyte_launch_plan_id": "launch_plan_id",
                "flyte_execution_id": "execution_id",
                "cancellation_info": {
                    "cancellable": True,
                    "is_cancelled": True,
                    "cancel_time": current_timestamp,
                },
                "cancel_retry_counter": 3,
                "executions": {
                    "main": {
                        "launch_plan_id": "launch_plan_id",
                        "execution_id": "execution_id",
                        "start_retry_counter": 2,
                        "cancel_retry_counter": 4,
                        "process_start_time": current_timestamp,
                    },
                    "revert": {
                        "execution_id": "revert_execution_id",
                        "start_retry_counter": 3,
                        "process_start_time": current_timestamp,
                    },
                },
                "session": {
                    "organization_id": "000000000000000000000001",
                    "workspace_id": "63b183d00000000000000001",
                },
                "telemetry": {"context": ""},
                "gpu": {"num_required": 1, "state": "RESERVED"},
                "cost": {
                    "requests": [{"amount": 100, "unit": "images"}],
                    "lease_id": "7d227a60-96f7-4294-bc0a-2fd07debe9d2",
                    "consumed": [
                        {
                            "amount": 100,
                            "unit": "images",
                            "consuming_date": current_timestamp,
                            "service": "training",
                        }
                    ],
                    "reported": False,
                },
            }
        )
        job_dict = JobMapper.forward(job)
        assert_jobs_equal_deep(
            job,
            Job(
                id=ID("job_id"),
                workspace_id=ID("workspace"),
                type="train",
                priority=0,
                job_name="Train",
                key="job_key",
                state=JobState.SUBMITTED,
                state_group=JobStateGroup.SCHEDULED,
                step_details=(),
                payload={"workspace_id": "workspace"},
                metadata={"project_name": "test_project"},
                creation_time=current_timestamp,
                author=ID("author_uid"),
                project_id=ID("project"),
                start_time=current_timestamp,
                end_time=current_timestamp,
                cancellation_info=JobCancellationInfo(
                    cancellable=True, is_cancelled=True, cancel_time=current_timestamp
                ),
                executions=JobFlyteExecutions(
                    main=JobMainFlyteExecution(
                        launch_plan_id="launch_plan_id",
                        execution_id="execution_id",
                        start_retry_counter=2,
                        cancel_retry_counter=4,
                        process_start_time=current_timestamp,
                    ),
                    revert=JobRevertFlyteExecution(
                        execution_id="revert_execution_id",
                        start_retry_counter=3,
                        process_start_time=current_timestamp,
                    ),
                ),
                session=Session(
                    organization_id=ID("000000000000000000000001"),
                    workspace_id=ID("63b183d00000000000000001"),
                ),
                telemetry=Telemetry(context=""),
                gpu=JobGpuRequest(num_required=1, state=JobGpuRequestState.RESERVED),
                cost=JobCost(
                    requests=(JobResource(amount=100, unit="images"),),
                    lease_id="7d227a60-96f7-4294-bc0a-2fd07debe9d2",
                    consumed=(
                        JobConsumedResource(
                            amount=100,
                            unit="images",
                            consuming_date=current_timestamp,
                            service="training",
                        ),
                    ),
                    reported=False,
                ),
            ),
        )
        assert_jobs_equal_deep(JobMapper.backward(job_dict), job)
