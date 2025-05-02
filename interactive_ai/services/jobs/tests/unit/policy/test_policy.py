# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os
from unittest.mock import MagicMock, call, patch

import pytest

from policies import GpuPolicy, MaxRunningJobsPolicy, Prioritizer, QuotaPolicy, ResourceManager
from policies.job_repo import SessionBasedPolicyJobRepo

from geti_types import ID
from iai_core.repos.mappers import IDToMongo

ORG = ID("000000000000000000000001")
WORK = ID("000000000000000000000002")


def mock_prioritizer(self, *args, **kwargs) -> None:
    self._client = MagicMock()


def mock_job_repo(self, *args, **kwargs) -> None:
    self._collection_name = "jobs"
    SessionBasedPolicyJobRepo._mongo_client = MagicMock()  # type: ignore


def reset_singletons() -> None:
    Prioritizer._instance = None
    ResourceManager._instance = None


@patch.object(SessionBasedPolicyJobRepo, "__init__", new=mock_job_repo)
@patch("policies.policy.mark_next_gpu_bound_jobs_ids_as_ready_for_scheduling_from_submitted_queue")
@patch("policies.policy.mark_next_regular_jobs_as_ready_for_scheduling_from_submitted_queue")
@patch.object(Prioritizer, "get_job_type_policy")
@patch.object(Prioritizer, "get_submitted_job_types")
@patch.object(Prioritizer, "__init__", new=mock_prioritizer)
def test_mark_next_jobs_as_ready_for_scheduling_from_submitted_queue_empty(
    mock_get_submitted_job_types,
    mock_get_job_type_policy,
    mock_mark_next_regular_jobs_as_ready_for_scheduling_from_submitted_queue,
    mock_mark_next_gpu_bound_jobs_ids_as_ready_for_scheduling_from_submitted_queue,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_get_submitted_job_types.return_value = []

    # Act
    Prioritizer().mark_next_jobs_as_ready_for_scheduling_from_submitted_queue()

    # Assert
    mock_get_submitted_job_types.assert_called_once_with()
    mock_get_job_type_policy.assert_not_called()
    mock_mark_next_regular_jobs_as_ready_for_scheduling_from_submitted_queue.assert_not_called()
    mock_mark_next_gpu_bound_jobs_ids_as_ready_for_scheduling_from_submitted_queue.assert_not_called()


@patch.object(SessionBasedPolicyJobRepo, "__init__", new=mock_job_repo)
@patch("policies.policy.mark_next_gpu_bound_jobs_ids_as_ready_for_scheduling_from_submitted_queue")
@patch.object(Prioritizer, "get_job_type_policy")
@patch.object(Prioritizer, "get_submitted_job_types")
@patch.object(Prioritizer, "__init__", new=mock_prioritizer)
def test_mark_next_jobs_as_ready_for_scheduling_from_submitted_queue_gpu_bound_no_capacity(
    mock_get_submitted_job_types,
    mock_get_job_type_policy,
    mock_mark_next_gpu_bound_jobs_ids_as_ready_for_scheduling_from_submitted_queue,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_get_submitted_job_types.return_value = ["train"]
    mock_get_job_type_policy.return_value = GpuPolicy()

    # Act
    Prioritizer().mark_next_jobs_as_ready_for_scheduling_from_submitted_queue()

    # Assert
    mock_get_submitted_job_types.assert_called_once_with()
    mock_get_job_type_policy.assert_called_once_with(type="train")
    mock_mark_next_gpu_bound_jobs_ids_as_ready_for_scheduling_from_submitted_queue.assert_not_called()


@patch.object(SessionBasedPolicyJobRepo, "__init__", new=mock_job_repo)
@patch("policies.policy.mark_next_gpu_bound_jobs_ids_as_ready_for_scheduling_from_submitted_queue")
@patch("policies.policy.mark_next_regular_jobs_as_ready_for_scheduling_from_submitted_queue")
@patch("policies.policy.get_organization_job_quota")
@patch.object(Prioritizer, "get_job_type_policy")
@patch.object(Prioritizer, "get_submitted_job_types")
@patch.object(Prioritizer, "__init__", new=mock_prioritizer)
def test_mark_next_jobs_as_ready_for_scheduling_from_submitted_queue(
    mock_get_submitted_job_types,
    mock_get_job_type_policy,
    mock_get_organization_job_quota,
    mock_mark_next_regular_jobs_as_ready_for_scheduling_from_submitted_queue,
    mock_mark_next_gpu_bound_jobs_ids_as_ready_for_scheduling_from_submitted_queue,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_get_submitted_job_types.return_value = [
        "train",
        "optimize",
        "test",
        "quota1",
        "quota2",
    ]
    ResourceManager().gpu_capacity = [5]

    def side_effect(type):
        if type == "train":
            return GpuPolicy()
        if type == "optimize":
            return MaxRunningJobsPolicy(limit=5)
        if type == "test":
            return MaxRunningJobsPolicy(limit=10)
        if type == "quota1" or type == "quota2":
            return QuotaPolicy()
        return MaxRunningJobsPolicy(limit=0)

    mock_get_job_type_policy.side_effect = side_effect

    mock_get_organization_job_quota.return_value = 7

    # Act
    Prioritizer().mark_next_jobs_as_ready_for_scheduling_from_submitted_queue()

    # Assert
    mock_get_submitted_job_types.assert_called_once_with()
    mock_get_job_type_policy.assert_has_calls(
        [
            call(type="train"),
            call(type="optimize"),
            call(type="test"),
            call(type="quota1"),
            call(type="quota2"),
        ],
    )
    mock_mark_next_regular_jobs_as_ready_for_scheduling_from_submitted_queue.assert_has_calls(
        [
            call(types=["optimize"], max_number_of_running_jobs=5),
            call(types=["test"], max_number_of_running_jobs=10),
            call(types=["quota1", "quota2"], max_number_of_running_jobs=7),
        ],
    )
    mock_mark_next_gpu_bound_jobs_ids_as_ready_for_scheduling_from_submitted_queue.assert_called_once_with(
        gpu_jobs_types=["train"], gpu_capacity=[5]
    )


@patch.object(SessionBasedPolicyJobRepo, "__init__", new=mock_job_repo)
@patch.object(Prioritizer, "__init__", new=mock_prioritizer)
def test_get_session_ids_with_submitted_jobs(
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    collection = MagicMock()
    SessionBasedPolicyJobRepo._collection = collection  # type: ignore[method-assign]
    collection.aggregate.return_value = [
        {
            "_id": ID("test_job_doc"),
            "workspace_id": WORK,
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
                "workspace_id": WORK,
            },
            "metadata": {"project_name": "test_project"},
            "author": ID("author"),
            "executions": {"main": {}},
            "session": {
                "organization_id": str(ORG),
                "workspace_id": str(WORK),
            },
            "telemetry": {"context": ""},
            "organization_id": IDToMongo.forward(ORG),
        }
    ]

    # Act
    result = Prioritizer().get_session_ids_with_submitted_jobs()

    # Assert
    collection.aggregate.assert_called_once_with(
        [
            # Find SUBMITTED and not cancelled jobs
            {
                "$match": {
                    "state": 0,
                    "cancellation_info.is_cancelled": False,
                }
            }
        ],
        allowDiskUse=True,
    )
    assert result == {ORG: WORK}


@patch.object(SessionBasedPolicyJobRepo, "aggregate_read")
@patch.object(SessionBasedPolicyJobRepo, "__init__", new=mock_job_repo)
@patch.object(Prioritizer, "__init__", new=mock_prioritizer)
def test_get_submitted_job_types(
    mock_repo_aggregate,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_repo_aggregate.return_value = [{"_id": "train"}]

    # Act
    result = Prioritizer().get_submitted_job_types()

    # Assert
    mock_repo_aggregate.assert_called_once_with(
        [
            {
                "$match": {
                    "state": 0,
                    "cancellation_info.is_cancelled": False,
                }
            },
            {"$group": {"_id": "$type"}},
        ],
    )
    assert result == {"train"}


@pytest.mark.parametrize(
    "env_vars, result",
    [
        (
            {
                "MAX_JOBS_RUNNING_PER_ORGANIZATION": "2",
                "MAX_TRAIN_JOBS_RUNNING_PER_ORGANIZATION": "4",
            },
            MaxRunningJobsPolicy(limit=4),
        ),
        (
            {
                "MAX_JOBS_RUNNING_PER_ORGANIZATION": "2",
                "MAX_TRAIN_JOBS_RUNNING_PER_ORGANIZATION": "gpu",
            },
            GpuPolicy(),
        ),
        (
            {
                "MAX_JOBS_RUNNING_PER_ORGANIZATION": "2",
                "MAX_TRAIN_JOBS_RUNNING_PER_ORGANIZATION": "quota",
            },
            QuotaPolicy(),
        ),
        ({"MAX_JOBS_RUNNING_PER_ORGANIZATION": "3"}, MaxRunningJobsPolicy(limit=3)),
    ],
)
def test_get_job_type_policy(env_vars, result, request) -> None:
    request.addfinalizer(reset_singletons)
    # Arrange

    # Act
    with patch.dict(os.environ, env_vars):
        max_number_of_running_jobs = Prioritizer().get_job_type_policy("train")

    # Assert
    assert max_number_of_running_jobs == result


def test_get_job_type_policy_failure() -> None:
    # Arrange

    # Act
    with pytest.raises(Exception) as error:
        Prioritizer().get_job_type_policy("train")

    # Assert
    assert str(error.value) == "Environment variable MAX_JOBS_RUNNING_PER_ORGANIZATION must be properly defined"
