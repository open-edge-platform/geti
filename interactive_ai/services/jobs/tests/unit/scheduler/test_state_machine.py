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

import json
from datetime import timedelta
from unittest.mock import ANY, MagicMock, call, patch

import pytest
from bson import ObjectId
from pymongo.results import UpdateResult

from model.job import (
    JobCancellationInfo,
    JobConsumedResource,
    JobCost,
    JobGpuRequest,
    JobResource,
    JobStepDetails,
    JobTaskExecutionBranch,
)
from model.job_state import JobGpuRequestState, JobState, JobStateGroup, JobTaskState
from model.mapper.job_mapper import JobMapper
from scheduler.job_repo import SessionBasedSchedulerJobRepo
from scheduler.state_machine import StateMachine

from geti_spicedb_tools import SpiceDB
from geti_types import ID, make_session, session_context
from sc_sdk.repos.mappers import IDToMongo
from sc_sdk.utils.time_utils import now

ORG = ID(ObjectId())

DUMMY_JOB_KEY = json.dumps({"job_key": "value"})
workspace_id = ID("test_workspace")
project_id = ID("234567890123456789010000")
payload = {"workspace_id": workspace_id, "project_id": project_id}


def mock_state_machine(self, *args, **kwargs) -> None:
    self._client = MagicMock()


def mock_job_repo(self, *args, **kwargs) -> None:
    self._collection_name = "jobs"
    SessionBasedSchedulerJobRepo._mongo_client = MagicMock()  # type: ignore


def reset_singletons() -> None:
    StateMachine._instance = None


@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_get_session_ids_with_jobs_not_in_final_state(
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    collection = MagicMock()
    SessionBasedSchedulerJobRepo._collection = collection  # type: ignore[method-assign]
    collection.aggregate.return_value = [
        {
            "_id": ID("test_job_doc"),
            "workspace_id": workspace_id,
            "creation_time": "today",
            "type": "train",
            "priority": 0,
            "job_name": "Train job",
            "state": 0,
            "state_group": "SCHEDULED",
            "cancellation_info": {"is_cancelled": False},
            "step_details": [],
            "key": "dummy_key",
            "payload": {
                "workspace_id": workspace_id,
            },
            "metadata": {"project_name": "test_project"},
            "author": ID("author"),
            "executions": {"main": {}},
            "session": {
                "organization_id": str(ORG),
                "workspace_id": str(workspace_id),
            },
            "telemetry": {"context": ""},
            "organization_id": IDToMongo.forward(ORG),
        }
    ]

    # Act
    session_ids = StateMachine().get_session_ids_with_jobs_not_in_final_state()

    # Assert
    assert session_ids == {ORG: workspace_id}
    collection.aggregate.assert_called_once_with(
        [
            {
                "$match": {
                    "state": {"$lt": 100},
                }
            },
        ],
        allowDiskUse=True,
    )


@patch("scheduler.state_machine.JobMapper.backward")
@patch.object(SessionBasedSchedulerJobRepo, "get_document_by_id")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_get_by_id_none(
    mock_repo_get_by_id,
    mock_mapper_backward,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_id = ID("job_id")

    mock_repo_get_by_id.return_value = None

    # Act
    returned_job = StateMachine().get_by_id(job_id=job_id)

    # Assert
    assert returned_job is None
    mock_repo_get_by_id.assert_called_once_with(job_id)
    mock_mapper_backward.assert_not_called()


@patch("scheduler.state_machine.JobMapper.backward")
@patch.object(SessionBasedSchedulerJobRepo, "get_document_by_id")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_get_by_id(
    mock_repo_get_by_id,
    mock_mapper_backward,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_id = ID("job_id")
    job_dict = {"_id": "job_id"}
    job: dict = {}

    mock_repo_get_by_id.return_value = job_dict
    mock_mapper_backward.return_value = job

    # Act
    returned_job = StateMachine().get_by_id(job_id=job_id)

    # Assert
    assert returned_job == job
    mock_repo_get_by_id.assert_called_once_with(job_id)
    mock_mapper_backward.assert_called_once_with(job_dict)


@patch.object(SessionBasedSchedulerJobRepo, "aggregate_read")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_find_jobs_ids_by_project_id(
    mock_repo_aggregate,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_id = ID("job_id")
    mock_repo_aggregate.return_value = [{"_id": job_id}]

    # Act
    jobs_ids = StateMachine().find_jobs_ids_by_project_id(project_id=project_id)

    # Assert
    assert jobs_ids == (job_id,)
    mock_repo_aggregate.assert_called_once_with(
        [
            {
                "$match": {
                    "project_id": "234567890123456789010000",
                }
            }
        ]
    )


@patch.object(SpiceDB, "delete_job")
@patch.object(SessionBasedSchedulerJobRepo, "delete_by_id")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_delete_deleted(
    mock_repo_delete_by_id,
    mock_spicedb_delete_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_id = ID("job_id")
    mock_repo_delete_by_id.return_value = True

    # Act
    deleted = StateMachine().delete_job(job_id=job_id)

    # Assert
    mock_repo_delete_by_id.assert_called_once_with(job_id)
    mock_spicedb_delete_job.assert_called_once_with(job_id="job_id")
    assert deleted


@patch.object(SpiceDB, "delete_job")
@patch.object(SessionBasedSchedulerJobRepo, "delete_by_id")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_delete_not_deleted(
    mock_repo_delete_by_id,
    mock_spicedb_delete_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_id = ID("job_id")
    mock_repo_delete_by_id.return_value = False

    # Act
    deleted = StateMachine().delete_job(job_id=job_id)

    # Assert
    mock_repo_delete_by_id.assert_called_once_with(job_id)
    mock_spicedb_delete_job.assert_not_called()
    assert not deleted


@patch.object(SessionBasedSchedulerJobRepo, "update")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_mark_cancelled_and_deleted(mock_repo_update, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_id = ID("job_id")

    # Act
    StateMachine().mark_cancelled_and_deleted(job_id=job_id)

    # Assert
    mock_repo_update.assert_called_once_with(
        job_id=job_id,
        update={
            "$set": {
                "cancellation_info.delete_job": True,
                "cancellation_info.is_cancelled": True,
                "cancellation_info.request_time": ANY,
            }
        },
    )


@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_find_and_lock_job_for_scheduling_none(request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    collection = MagicMock()
    SessionBasedSchedulerJobRepo._collection = collection  # type: ignore[method-assign]
    collection.find_one_and_update.return_value = None

    # Act
    result = StateMachine().find_and_lock_job_for_scheduling()

    # Assert
    assert result is None
    collection.find_one_and_update.assert_called_once_with(
        filter={
            "state": 1,
            "cancellation_info.is_cancelled": False,
        },
        update={
            "$set": {
                "state": 2,
                "state_group": "SCHEDULED",
                "executions.main.process_start_time": ANY,
            }
        },
        upsert=False,
        return_document=True,
    )


@patch.object(JobMapper, "backward")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_find_and_lock_job_for_scheduling(mock_backward, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    collection = MagicMock()
    SessionBasedSchedulerJobRepo._collection = collection  # type: ignore[method-assign]

    document = MagicMock()
    job = MagicMock()
    collection.find_one_and_update.return_value = document
    mock_backward.return_value = job

    # Act
    found_job = StateMachine().find_and_lock_job_for_scheduling()

    # Assert
    assert found_job == job
    collection.find_one_and_update.assert_called_once_with(
        filter={
            "state": 1,
            "cancellation_info.is_cancelled": False,
        },
        update={
            "$set": {
                "state": 2,
                "state_group": "SCHEDULED",
                "executions.main.process_start_time": ANY,
            }
        },
        upsert=False,
        return_document=True,
    )
    mock_backward.assert_called_once_with(document)


@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_reset_scheduling_jobs(request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    collection = MagicMock()
    SessionBasedSchedulerJobRepo._collection = collection  # type: ignore[method-assign]
    collection.update_many.return_value = UpdateResult({"nModified": 1}, True)
    threshold = now() - timedelta(seconds=10)

    # Act
    result = StateMachine().reset_scheduling_jobs(threshold=threshold)

    # Assert
    collection.update_many.assert_called_once_with(
        filter={
            "state": 2,
            "executions.main.process_start_time": {"$lt": threshold},
        },
        update={
            "$set": {
                "state": 0,
                "state_group": "SCHEDULED",
            },
            "$unset": {"executions.main.process_start_time": ""},
            "$inc": {"executions.main.start_retry_counter": 1},
        },
    )
    assert result == 1


@pytest.mark.parametrize("updated", [True, False])
@patch.object(SessionBasedSchedulerJobRepo, "update")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_reset_scheduling_job(mock_repo_update, updated, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_id = ID("job_id")
    mock_repo_update.return_value = updated

    # Act
    result = StateMachine().reset_scheduling_job(job_id=job_id)

    # Assert
    assert result == updated
    mock_repo_update.assert_called_once_with(
        job_id=ID("job_id"),
        update={
            "$set": {
                "state": 0,
                "state_group": "SCHEDULED",
            },
            "$unset": {"executions.main.process_start_time": ""},
            "$inc": {"executions.main.start_retry_counter": 1},
        },
    )


@pytest.mark.parametrize("updated", [True, False])
@patch.object(SessionBasedSchedulerJobRepo, "update")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_set_scheduled_state(mock_repo_update, updated, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_id = ID("job_id")
    mock_repo_update.return_value = updated

    # Act
    result = StateMachine().set_scheduled_state(
        job_id=job_id,
        flyte_launch_plan_id="launch_plan_id",
        flyte_execution_id="execution_id",
        step_details=[
            JobStepDetails(
                index=1,
                task_id="task_id",
                step_name="step_name",
                state=JobTaskState.WAITING,
                branches=(JobTaskExecutionBranch(condition="condition", branch="branch"),),
                progress=-1,
            )
        ],
    )

    # Assert
    assert result == updated
    mock_repo_update.assert_called_once_with(
        job_id=job_id,
        update={
            "$set": {
                "state": 3,
                "state_group": "SCHEDULED",
                "executions.main.launch_plan_id": "launch_plan_id",
                "executions.main.execution_id": "execution_id",
                "step_details": [
                    {
                        "index": 1,
                        "task_id": "task_id",
                        "step_name": "step_name",
                        "state": "WAITING",
                        "branches": [
                            {
                                "condition": "condition",
                                "branch": "branch",
                            }
                        ],
                        "progress": -1,
                    }
                ],
            },
            "$unset": {"executions.main.process_start_time": ""},
        },
    )


@pytest.mark.parametrize("updated", [True, False])
@patch.object(SessionBasedSchedulerJobRepo, "update")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_set_running_state(mock_repo_update, updated, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_id = ID("job_id")
    mock_repo_update.return_value = updated

    # Act
    result = StateMachine().set_running_state(job_id=job_id)

    # Assert
    assert result == updated
    mock_repo_update.assert_called_once_with(
        job_id=job_id,
        update={
            "$set": {
                "state": 4,
                "state_group": "RUNNING",
                "start_time": ANY,
            },
        },
    )


@pytest.mark.parametrize("updated", [True, False])
@patch.object(SessionBasedSchedulerJobRepo, "update")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_set_step_details(mock_repo_update, updated, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_id = ID("job_id")
    mock_repo_update.return_value = updated

    # Act
    result = StateMachine().set_step_details(
        job_id=job_id,
        task_id="task_id",
        state=JobTaskState.RUNNING,
        progress=0,
        message="Starting",
    )

    # Assert
    assert result == updated
    mock_repo_update.assert_called_once_with(
        job_id=job_id,
        update={
            "$set": {
                "step_details.$[task].state": "RUNNING",
                "step_details.$[task].progress": 0,
                "step_details.$[task].message": "Starting",
            }
        },
        array_filters=[{"task.task_id": "task_id"}],
    )


@pytest.mark.parametrize("updated", [True, False])
@patch.object(SessionBasedSchedulerJobRepo, "update")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_update_metadata(mock_repo_update, updated, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_id = ID("job_id")
    mock_repo_update.return_value = updated

    # Act
    result = StateMachine().update_metadata(
        job_id=job_id,
        metadata={"key": "value"},
    )

    # Assert
    assert result == updated
    mock_repo_update.assert_called_once_with(
        job_id=job_id,
        update=[{"$set": {"metadata": {"$mergeObjects": ["$metadata", {"key": "value"}]}}}],
    )


@pytest.mark.freeze_time("2024-01-01 00:00:01")
@patch.object(SessionBasedSchedulerJobRepo, "update")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "get_by_id")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_update_cost_consumed(mock_sm_get_by_id, mock_repo_update, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_id = ID("job_id")
    mock_repo_update.return_value = True
    job = MagicMock()
    job.cost = JobCost(
        requests=(JobResource(amount=100, unit="images"), JobResource(amount=100, unit="images")),
        lease_id="lease_id",
        consumed=(JobConsumedResource(amount=100, unit="images", consuming_date=now(), service="training"),),
        reported=False,
    )
    mock_sm_get_by_id.return_value = job

    # Act
    result = StateMachine().update_cost_consumed(
        job_id=job_id,
        consumed_resources=[
            JobConsumedResource(amount=100, unit="images", consuming_date=now(), service="training"),
            JobConsumedResource(amount=1, unit="frames", consuming_date=now(), service="other_service"),
        ],
    )

    # Assert
    assert result
    mock_sm_get_by_id.assert_called_once_with(job_id=job_id)
    mock_repo_update.assert_called_once_with(
        job_id=job_id,
        update={
            "$push": {
                "cost.consumed": {
                    "$each": [{"amount": 1, "unit": "frames", "consuming_date": now(), "service": "other_service"}]
                }
            }
        },
    )


@pytest.mark.parametrize("updated", [True, False])
@patch.object(SessionBasedSchedulerJobRepo, "update")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_set_gpu_state_released(mock_repo_update, request, updated) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_id = ID("job_id")
    mock_repo_update.return_value = updated

    # Act
    result = StateMachine().set_gpu_state_released(job_id=job_id)

    # Assert
    assert result == updated
    mock_repo_update.assert_called_once_with(job_id=job_id, update=[{"$set": {"gpu.state": "RELEASED"}}])


@patch("scheduler.state_machine.publish_event")
@patch.object(SessionBasedSchedulerJobRepo, "update")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "get_by_id")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
@pytest.mark.freeze_time("2024-01-01 00:00:01")
@pytest.mark.parametrize("gpu_bound", [True, False], ids=["Gpu-bound", "Regular"])
def test_set_and_publish_finished_state_updated(
    mock_get_by_id,
    mock_repo_update,
    mock_publish,
    request,
    gpu_bound,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    start_time = now() - timedelta(minutes=5)
    end_time = now()

    job_id = ID("job_id")
    mock_job = MagicMock()
    mock_job.type = "train"
    mock_job.metadata = {"meta": "data"}
    mock_job.payload = {"pay": "load"}
    mock_job.start_time = start_time
    if gpu_bound:
        mock_job.gpu = JobGpuRequest(num_required=1, state=JobGpuRequestState.RESERVED)
    body = {
        "workspace_id": str(workspace_id),
        "job_type": mock_job.type,
        "job_payload": mock_job.payload,
        "job_metadata": mock_job.metadata,
        "start_time": mock_job.start_time.isoformat(),
        "end_time": end_time.isoformat(),
    }
    mock_get_by_id.return_value = mock_job
    mock_repo_update.return_value = True

    # Act
    with session_context(session=make_session(workspace_id=workspace_id)):
        updated = StateMachine().set_and_publish_finished_state(job_id=job_id)

    # Assert
    assert updated
    update_set = {"state": 100, "state_group": "FINISHED", "end_time": end_time}
    if gpu_bound:
        update_set["gpu.state"] = "RELEASED"
    mock_repo_update.assert_called_once_with(job_id=job_id, update={"$set": update_set})

    mock_get_by_id.assert_called_once_with(job_id)
    if end_time is not None:
        mock_publish.assert_called_once_with(
            topic="on_job_finished",
            body=body,
            key=str(mock_job.id).encode(),
            headers_getter=ANY,
        )
    else:
        mock_publish.assert_not_called()


@patch("scheduler.state_machine.publish_event")
@patch.object(SessionBasedSchedulerJobRepo, "update")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "get_by_id")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
@pytest.mark.freeze_time("2024-01-01 00:00:01")
@pytest.mark.parametrize("gpu_bound", [True, False], ids=["Gpu-bound", "Regular"])
def test_set_and_publish_finished_state_not_updated(
    mock_get_by_id,
    mock_repo_update,
    mock_publish,
    request,
    gpu_bound,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    start_time = now() - timedelta(minutes=5)
    end_time = now()

    job_id = ID("job_id")
    mock_job = MagicMock()
    mock_job.type = "train"
    mock_job.metadata = {"meta": "data"}
    mock_job.payload = {"pay": "load"}
    mock_job.start_time = start_time
    if gpu_bound:
        mock_job.gpu = JobGpuRequest(num_required=1, state=JobGpuRequestState.RESERVED)
    mock_get_by_id.return_value = mock_job
    mock_repo_update.return_value = False

    # Act
    updated = StateMachine().set_and_publish_finished_state(job_id=job_id)

    # Assert
    assert not updated
    update_set = {"state": 100, "state_group": "FINISHED", "end_time": end_time}
    if gpu_bound:
        update_set["gpu.state"] = "RELEASED"
    mock_repo_update.assert_called_once_with(job_id=job_id, update={"$set": update_set})

    mock_get_by_id.assert_called_once_with(job_id)
    mock_publish.assert_not_called()


@pytest.mark.parametrize("updated", [True, False])
@patch.object(SessionBasedSchedulerJobRepo, "update")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_set_ready_for_revert_state(mock_repo_update, updated, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_id = ID("job_id")
    mock_repo_update.return_value = updated

    # Act
    result = StateMachine().set_ready_for_revert_state(job_id=job_id)

    # Assert
    assert result == updated
    mock_repo_update.assert_called_once_with(
        job_id=job_id,
        update={
            "$set": {"state": 6, "executions.revert": {}},
        },
    )


@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_find_and_lock_job_for_reverting_none(request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    collection = MagicMock()
    SessionBasedSchedulerJobRepo._collection = collection  # type: ignore[method-assign]
    collection.find_one_and_update.return_value = None

    # Act
    result = StateMachine().find_and_lock_job_for_reverting()

    # Assert
    assert result is None
    collection.find_one_and_update.assert_called_once_with(
        filter={
            "state": 6,
        },
        update={
            "$set": {
                "state": 7,
                "executions.revert.process_start_time": ANY,
            }
        },
        upsert=False,
        return_document=True,
    )


@patch.object(JobMapper, "backward")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_find_and_lock_job_for_reverting(mock_backward, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    collection = MagicMock()
    SessionBasedSchedulerJobRepo._collection = collection  # type: ignore[method-assign]

    document = MagicMock()
    job = MagicMock()
    collection.find_one_and_update.return_value = document
    mock_backward.return_value = job

    # Act
    found_job = StateMachine().find_and_lock_job_for_reverting()

    # Assert
    assert found_job == job
    collection.find_one_and_update.assert_called_once_with(
        filter={
            "state": 6,
        },
        update={
            "$set": {
                "state": 7,
                "executions.revert.process_start_time": ANY,
            }
        },
        upsert=False,
        return_document=True,
    )
    mock_backward.assert_called_once_with(document)


@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_reset_revert_scheduling_jobs(request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    collection = MagicMock()
    SessionBasedSchedulerJobRepo._collection = collection  # type: ignore[method-assign]
    collection.update_many.return_value = UpdateResult({"nModified": 1}, True)
    threshold = now() - timedelta(seconds=10)

    # Act
    result = StateMachine().reset_revert_scheduling_jobs(threshold=threshold)

    # Assert
    collection.update_many.assert_called_once_with(
        filter={
            "state": 7,
            "executions.revert.process_start_time": {"$lt": threshold},
        },
        update={
            "$set": {
                "state": 6,
            },
            "$unset": {"executions.revert.process_start_time": ""},
            "$inc": {"executions.revert.start_retry_counter": 1},
        },
    )
    assert result == 1


@pytest.mark.parametrize("updated", [True, False])
@patch.object(SessionBasedSchedulerJobRepo, "update")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_reset_revert_scheduling_job(mock_repo_update, updated, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_id = ID("job_id")
    mock_repo_update.return_value = updated

    # Act
    result = StateMachine().reset_revert_scheduling_job(job_id=job_id)

    # Assert
    assert result == updated
    mock_repo_update.assert_called_once_with(
        job_id=ID("job_id"),
        update={
            "$set": {
                "state": 6,
            },
            "$unset": {"executions.revert.process_start_time": ""},
            "$inc": {"executions.revert.start_retry_counter": 1},
        },
    )


@pytest.mark.parametrize("updated", [True, False])
@patch.object(SessionBasedSchedulerJobRepo, "update")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_set_revert_scheduled_state(mock_repo_update, updated, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_id = ID("job_id")
    mock_repo_update.return_value = updated

    # Act
    result = StateMachine().set_revert_scheduled_state(
        job_id=job_id,
        flyte_execution_id="execution_id",
    )

    # Assert
    assert result == updated
    mock_repo_update.assert_called_once_with(
        job_id=job_id,
        update={
            "$set": {
                "state": 8,
                "executions.revert.execution_id": "execution_id",
            },
            "$unset": {"executions.revert.process_start_time": ""},
        },
    )


@pytest.mark.parametrize("updated", [True, False])
@patch.object(SessionBasedSchedulerJobRepo, "update")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_set_revert_running_state(mock_repo_update, updated, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_id = ID("job_id")
    mock_repo_update.return_value = updated

    # Act
    result = StateMachine().set_revert_running_state(job_id=job_id)

    # Assert
    assert result == updated
    mock_repo_update.assert_called_once_with(
        job_id=job_id,
        update={
            "$set": {
                "state": 9,
            },
        },
    )


@patch("scheduler.state_machine.publish_event")
@patch.object(SessionBasedSchedulerJobRepo, "update")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "get_by_id")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
@pytest.mark.freeze_time("2024-01-01 00:00:01")
@pytest.mark.parametrize("gpu_bound", [True, False], ids=["Gpu-bound", "Regular"])
@pytest.mark.parametrize("start_time", [now() - timedelta(minutes=5), None])
def test_set_and_publish_failed_state_updated(
    mock_get_by_id,
    mock_repo_update,
    mock_publish,
    request,
    gpu_bound,
    start_time,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    end_time = now()

    job_id = ID("job_id")
    mock_job = MagicMock()
    mock_job.type = "train"
    mock_job.metadata = {"meta": "data"}
    mock_job.payload = {"pay": "load"}
    mock_job.start_time = start_time
    if gpu_bound:
        mock_job.gpu = JobGpuRequest(num_required=1, state=JobGpuRequestState.RESERVED)
    body = {
        "workspace_id": str(workspace_id),
        "job_type": mock_job.type,
        "job_payload": mock_job.payload,
        "job_metadata": mock_job.metadata,
        "start_time": mock_job.start_time.isoformat() if mock_job.start_time is not None else None,
        "end_time": end_time.isoformat(),
    }
    mock_get_by_id.return_value = mock_job
    mock_repo_update.return_value = True

    # Act
    with session_context(session=make_session(workspace_id=workspace_id)):
        updated = StateMachine().set_and_publish_failed_state(job_id=job_id)

    # Assert
    assert updated
    update_set = {"state": 101, "state_group": "FAILED", "end_time": end_time}
    if gpu_bound:
        update_set["gpu.state"] = "RELEASED"
    mock_repo_update.assert_called_once_with(
        job_id=job_id,
        update={
            "$set": update_set,
            "$unset": {
                "executions.main.process_start_time": "",
                "executions.revert.process_start_time": "",
            },
        },
    )

    mock_get_by_id.assert_called_once_with(job_id)
    mock_publish.assert_called_once_with(
        topic="on_job_failed",
        body=body,
        key=str(mock_job.id).encode(),
        headers_getter=ANY,
    )


@patch("scheduler.state_machine.publish_event")
@patch.object(SessionBasedSchedulerJobRepo, "update")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "get_by_id")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
@pytest.mark.freeze_time("2024-01-01 00:00:01")
@pytest.mark.parametrize("gpu_bound", [True, False], ids=["Gpu-bound", "Regular"])
def test_set_and_publish_failed_state_not_updated(
    mock_get_by_id,
    mock_repo_update,
    mock_publish,
    request,
    gpu_bound,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    start_time = now() - timedelta(minutes=5)
    end_time = now()

    job_id = ID("job_id")
    mock_job = MagicMock()
    mock_job.type = "train"
    mock_job.metadata = {"meta": "data"}
    mock_job.payload = {"pay": "load"}
    mock_job.start_time = start_time
    if gpu_bound:
        mock_job.gpu = JobGpuRequest(num_required=1, state=JobGpuRequestState.RESERVED)
    mock_get_by_id.return_value = mock_job
    mock_repo_update.return_value = False

    # Act
    updated = StateMachine().set_and_publish_failed_state(job_id=job_id)

    # Assert
    assert not updated
    update_set = {"state": 101, "state_group": "FAILED", "end_time": end_time}
    if gpu_bound:
        update_set["gpu.state"] = "RELEASED"
    mock_repo_update.assert_called_once_with(
        job_id=job_id,
        update={
            "$set": update_set,
            "$unset": {
                "executions.main.process_start_time": "",
                "executions.revert.process_start_time": "",
            },
        },
    )

    mock_get_by_id.assert_called_once_with(job_id)
    mock_publish.assert_not_called()


@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_get_job_to_delete_none(request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    collection = MagicMock()
    SessionBasedSchedulerJobRepo._collection = collection  # type: ignore[method-assign]
    collection.find_one.return_value = None

    # Act
    result = StateMachine().get_job_to_delete()

    # Assert
    assert result is None
    collection.find_one.assert_called_once_with(
        filter={
            "$and": [
                {"$or": [{"state": 100}, {"state": 101}, {"state": 102}]},
                {"cancellation_info.delete_job": True},
                {"$or": [{"cost": {"$exists": False}}, {"cost.reported": True}]},
            ]
        },
    )


@patch.object(JobMapper, "backward")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_get_job_to_delete(mock_backward, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    collection = MagicMock()
    SessionBasedSchedulerJobRepo._collection = collection  # type: ignore[method-assign]

    document = MagicMock()
    job = MagicMock()
    collection.find_one.return_value = document
    mock_backward.return_value = job

    # Act
    found_job = StateMachine().get_job_to_delete()

    # Assert
    assert found_job == job
    collection.find_one.assert_called_once_with(
        filter={
            "$and": [
                {"$or": [{"state": 100}, {"state": 101}, {"state": 102}]},
                {"cancellation_info.delete_job": True},
                {"$or": [{"cost": {"$exists": False}}, {"cost.reported": True}]},
            ]
        },
    )
    mock_backward.assert_called_once_with(document)


@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_get_cancelled_job_no_job_states(request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    collection = MagicMock()
    SessionBasedSchedulerJobRepo._collection = collection  # type: ignore[method-assign]
    collection.find_one.return_value = None

    # Act
    result = StateMachine().get_cancelled_job()

    # Assert
    assert result is None
    collection.find_one.assert_called_once_with(filter={"cancellation_info.is_cancelled": True})


@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_get_cancelled_job_none(request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    collection = MagicMock()
    SessionBasedSchedulerJobRepo._collection = collection  # type: ignore[method-assign]
    collection.find_one.return_value = None

    # Act
    result = StateMachine().get_cancelled_job(job_states=(JobState.SUBMITTED, JobState.READY_FOR_SCHEDULING))

    # Assert
    assert result is None
    collection.find_one.assert_called_once_with(
        filter={
            "state": {"$in": [0, 1]},
            "cancellation_info.is_cancelled": True,
        },
    )


@patch.object(JobMapper, "backward")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_get_cancelled_job(mock_backward, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    collection = MagicMock()
    SessionBasedSchedulerJobRepo._collection = collection  # type: ignore[method-assign]

    document = MagicMock()
    job = MagicMock()
    collection.find_one.return_value = document
    mock_backward.return_value = job

    # Act
    found_job = StateMachine().get_cancelled_job(job_states=(JobState.SUBMITTED, JobState.READY_FOR_SCHEDULING))

    # Assert
    assert found_job == job
    collection.find_one.assert_called_once_with(
        filter={
            "state": {"$in": [0, 1]},
            "cancellation_info.is_cancelled": True,
        },
    )
    mock_backward.assert_called_once_with(document)


@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_find_and_lock_job_for_canceling_none(request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    collection = MagicMock()
    SessionBasedSchedulerJobRepo._collection = collection  # type: ignore[method-assign]
    collection.find_one_and_update.return_value = None

    # Act
    result = StateMachine().find_and_lock_job_for_canceling()

    # Assert
    assert result is None
    collection.find_one_and_update.assert_called_once_with(
        filter={
            "$or": [{"state": 3}, {"state": 4}],
            "cancellation_info.is_cancelled": True,
        },
        update={"$set": {"state": 5, "executions.main.process_start_time": ANY}},
        upsert=False,
        return_document=True,
    )


@patch.object(JobMapper, "backward")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_find_and_lock_job_for_canceling(mock_backward, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    collection = MagicMock()
    SessionBasedSchedulerJobRepo._collection = collection  # type: ignore[method-assign]

    document = MagicMock()
    job = MagicMock()
    collection.find_one_and_update.return_value = document
    mock_backward.return_value = job

    # Act
    found_job = StateMachine().find_and_lock_job_for_canceling()

    # Assert
    assert found_job == job
    collection.find_one_and_update.assert_called_once_with(
        filter={
            "$or": [{"state": 3}, {"state": 4}],
            "cancellation_info.is_cancelled": True,
        },
        update={"$set": {"state": 5, "executions.main.process_start_time": ANY}},
        upsert=False,
        return_document=True,
    )
    mock_backward.assert_called_once_with(document)


@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_reset_canceling_jobs(request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    collection = MagicMock()
    SessionBasedSchedulerJobRepo._collection = collection  # type: ignore[method-assign]
    collection.update_many.return_value = UpdateResult({"nModified": 1}, True)
    threshold = now() - timedelta(seconds=10)

    # Act
    result = StateMachine().reset_canceling_jobs(threshold=threshold)

    # Assert
    collection.update_many.assert_has_calls(
        [
            call(
                filter={
                    "state": 5,
                    "state_group": "SCHEDULED",
                    "executions.main.process_start_time": {"$lt": threshold},
                },
                update={
                    "$set": {
                        "state": 3,
                    },
                    "$unset": {"executions.main.process_start_time": ""},
                    "$inc": {"executions.main.cancel_retry_counter": 1},
                },
            ),
            call(
                filter={
                    "state": 5,
                    "state_group": "RUNNING",
                    "executions.main.process_start_time": {"$lt": threshold},
                },
                update={
                    "$set": {
                        "state": 4,
                    },
                    "$unset": {"executions.main.process_start_time": ""},
                    "$inc": {"executions.main.cancel_retry_counter": 1},
                },
            ),
        ]
    )
    assert result == 2


@pytest.mark.parametrize(
    "state_group, state",
    [
        (JobStateGroup.SCHEDULED, JobState.SCHEDULED),
        (JobStateGroup.RUNNING, JobState.RUNNING),
    ],
)
@patch.object(SessionBasedSchedulerJobRepo, "get_document_by_id")
@patch.object(SessionBasedSchedulerJobRepo, "update")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_reset_canceling_job_not_found(
    mock_repo_update,
    mock_repo_get_by_id,
    request,
    state_group,
    state,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_id = ID("job_id")
    mock_repo_get_by_id.return_value = None

    # Act
    result = StateMachine().reset_canceling_job(job_id=job_id)

    # Assert
    assert not result
    mock_repo_update.assert_not_called()


@pytest.mark.parametrize("updated", [True, False])
@pytest.mark.parametrize(
    "state_group, state",
    [
        (JobStateGroup.SCHEDULED, JobState.SCHEDULED),
        (JobStateGroup.RUNNING, JobState.RUNNING),
    ],
)
@patch.object(SessionBasedSchedulerJobRepo, "get_document_by_id")
@patch.object(SessionBasedSchedulerJobRepo, "update")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_reset_canceling_job(
    mock_repo_update,
    mock_repo_get_by_id,
    request,
    updated,
    state_group,
    state,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_id = ID("job_id")
    mock_repo_update.return_value = updated
    mock_repo_get_by_id.return_value = {"state_group": state_group.value}

    # Act
    result = StateMachine().reset_canceling_job(job_id=job_id)

    # Assert
    assert result == updated
    mock_repo_update.assert_called_once_with(
        job_id=ID("job_id"),
        update={
            "$set": {
                "state": state.value,
            },
            "$unset": {"executions.main.process_start_time": ""},
            "$inc": {"executions.main.cancel_retry_counter": 1},
        },
    )


@pytest.mark.parametrize(
    "state_group, state",
    [
        (JobStateGroup.SCHEDULED, JobState.SCHEDULED),
        (JobStateGroup.RUNNING, JobState.RUNNING),
    ],
)
@patch.object(SessionBasedSchedulerJobRepo, "get_document_by_id")
@patch.object(SessionBasedSchedulerJobRepo, "update")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_drop_cancelled_flag_not_found(
    mock_repo_update,
    mock_repo_get_by_id,
    request,
    state_group,
    state,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_id = ID("job_id")
    mock_repo_get_by_id.return_value = None

    # Act
    result = StateMachine().drop_cancelled_flag(job_id=job_id)

    # Assert
    assert not result
    mock_repo_update.assert_not_called()


@pytest.mark.parametrize("updated", [True, False])
@pytest.mark.parametrize(
    "state_group, state",
    [
        (JobStateGroup.SCHEDULED, JobState.SCHEDULED),
        (JobStateGroup.RUNNING, JobState.RUNNING),
    ],
)
@patch.object(SessionBasedSchedulerJobRepo, "get_document_by_id")
@patch.object(SessionBasedSchedulerJobRepo, "update")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_drop_cancelled_flag(
    mock_repo_update,
    mock_repo_get_by_id,
    request,
    updated,
    state_group,
    state,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_id = ID("job_id")
    mock_repo_update.return_value = updated
    mock_repo_get_by_id.return_value = {"state_group": state_group.value}

    # Act
    result = StateMachine().drop_cancelled_flag(job_id=job_id)

    # Assert
    assert result == updated
    mock_repo_update.assert_called_once_with(
        job_id=ID("job_id"),
        update={
            "$set": {
                "state": state.value,
                "cancellation_info.is_cancelled": False,
            },
            "$unset": {
                "executions.main.process_start_time": "",
                "executions.main.cancel_retry_counter": "",
            },
        },
    )


@patch("scheduler.state_machine.publish_event")
@patch.object(SessionBasedSchedulerJobRepo, "update")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "get_by_id")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
@pytest.mark.freeze_time("2024-01-01 00:00:01")
@pytest.mark.parametrize("gpu_bound", [True, False], ids=["Gpu-bound", "Regular"])
@pytest.mark.parametrize("start_time", [now() - timedelta(minutes=5), None])
def test_set_and_publish_cancelled_state_updated(
    mock_get_by_id,
    mock_repo_update,
    mock_publish,
    request,
    gpu_bound,
    start_time,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    cancel_time = now()

    job_id = ID("job_id")
    mock_job = MagicMock()
    mock_job.type = "train"
    mock_job.metadata = {"meta": "data"}
    mock_job.payload = {"pay": "load"}
    mock_job.start_time = start_time
    mock_job.cancellation_info = JobCancellationInfo(cancel_time=cancel_time)
    if gpu_bound:
        mock_job.gpu = JobGpuRequest(num_required=1, state=JobGpuRequestState.RESERVED)
    body = {
        "workspace_id": str(workspace_id),
        "job_type": mock_job.type,
        "job_payload": mock_job.payload,
        "job_metadata": mock_job.metadata,
        "start_time": mock_job.start_time.isoformat() if mock_job.start_time is not None else None,
        "cancel_time": cancel_time.isoformat(),
    }
    mock_get_by_id.return_value = mock_job
    mock_repo_update.return_value = True

    # Act
    with session_context(session=make_session(workspace_id=workspace_id)):
        updated = StateMachine().set_and_publish_cancelled_state(job_id=job_id)

    # Assert
    assert updated
    update_set = {
        "state": 102,
        "state_group": "CANCELLED",
        "cancellation_info.cancel_time": ANY,
        "step_details.$[waitingtask].state": "CANCELLED",
        "step_details.$[runningtask].state": "CANCELLED",
    }
    if gpu_bound:
        update_set["gpu.state"] = "RELEASED"
    mock_repo_update.assert_called_once_with(
        job_id=job_id,
        update={
            "$set": update_set,
            "$unset": {
                "executions.main.process_start_time": "",
                "executions.revert.process_start_time": "",
            },
        },
        array_filters=[
            {"waitingtask.state": JobTaskState.WAITING.value},
            {"runningtask.state": JobTaskState.RUNNING.value},
        ],
    )

    mock_get_by_id.assert_called_once_with(job_id)
    mock_publish.assert_called_once_with(
        topic="on_job_cancelled",
        body=body,
        key=str(mock_job.id).encode(),
        headers_getter=ANY,
    )


@patch("scheduler.state_machine.publish_event")
@patch.object(SessionBasedSchedulerJobRepo, "update")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "get_by_id")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
@pytest.mark.freeze_time("2024-01-01 00:00:01")
@pytest.mark.parametrize("gpu_bound", [True, False], ids=["Gpu-bound", "Regular"])
def test_set_and_publish_cancelled_state_not_updated(
    mock_get_by_id,
    mock_repo_update,
    mock_publish,
    request,
    gpu_bound,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    start_time = now() - timedelta(minutes=5)
    now()
    job_id = ID("job_id")
    mock_job = MagicMock()
    mock_job.type = "train"
    mock_job.metadata = {"meta": "data"}
    mock_job.payload = {"pay": "load"}
    mock_job.start_time = start_time
    if gpu_bound:
        mock_job.gpu = JobGpuRequest(num_required=1, state=JobGpuRequestState.RESERVED)
    mock_get_by_id.return_value = mock_job
    mock_repo_update.return_value = False

    # Act
    updated = StateMachine().set_and_publish_cancelled_state(job_id=job_id)

    # Assert
    assert not updated
    update_set = {
        "state": 102,
        "state_group": "CANCELLED",
        "cancellation_info.cancel_time": ANY,
        "step_details.$[waitingtask].state": "CANCELLED",
        "step_details.$[runningtask].state": "CANCELLED",
    }
    if gpu_bound:
        update_set["gpu.state"] = "RELEASED"
    mock_repo_update.assert_called_once_with(
        job_id=job_id,
        update={
            "$set": update_set,
            "$unset": {
                "executions.main.process_start_time": "",
                "executions.revert.process_start_time": "",
            },
        },
        array_filters=[
            {"waitingtask.state": JobTaskState.WAITING.value},
            {"runningtask.state": JobTaskState.RUNNING.value},
        ],
    )

    mock_get_by_id.assert_called_once_with(job_id)
    mock_publish.assert_not_called()


@patch("microservice.job_manager.JobMapper.backward")
@patch.object(SessionBasedSchedulerJobRepo, "aggregate_read")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_get_scheduled_jobs_not_in_final_state_not_found(mock_repo_aggregate, mock_mapper_backward, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_repo_aggregate.return_value = []

    # Act
    jobs = StateMachine().get_scheduled_jobs_not_in_final_state()

    # Assert
    assert jobs == ()
    mock_repo_aggregate.assert_called_once_with(
        [
            {
                "$match": {
                    "$and": [
                        {"state": {"$gte": 3}},
                        {"state": {"$lt": 100}},
                    ],
                }
            }
        ]
    )
    mock_mapper_backward.assert_not_called()


@patch("microservice.job_manager.JobMapper.backward")
@patch.object(SessionBasedSchedulerJobRepo, "aggregate_read")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_get_scheduled_jobs_not_in_final_state_found(mock_repo_aggregate, mock_mapper_backward, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    document = MagicMock()
    job = MagicMock()
    mock_repo_aggregate.return_value = [document]
    mock_mapper_backward.return_value = job

    # Act
    jobs = StateMachine().get_scheduled_jobs_not_in_final_state()

    # Assert
    assert jobs == (job,)
    mock_repo_aggregate.assert_called_once_with(
        [
            {
                "$match": {
                    "$and": [
                        {"state": {"$gte": 3}},
                        {"state": {"$lt": 100}},
                    ],
                }
            }
        ]
    )
    mock_mapper_backward.assert_called_once_with(document)


@pytest.mark.parametrize("updated", [True, False])
@patch.object(SessionBasedSchedulerJobRepo, "update")
@patch.object(SessionBasedSchedulerJobRepo, "__init__", new=mock_job_repo)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_reset_job_to_submitted_state(mock_repo_update, updated, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_id = ID("job_id")
    mock_repo_update.return_value = updated

    # Act
    result = StateMachine().reset_job_to_submitted_state(job_id=job_id)

    # Assert
    assert result == updated
    mock_repo_update.assert_called_once_with(
        job_id=job_id,
        update={
            "$set": {
                "state": 0,
                "state_group": "SCHEDULED",
                "step_details": [],
                "executions": {"main": {}},
            },
        },
    )
