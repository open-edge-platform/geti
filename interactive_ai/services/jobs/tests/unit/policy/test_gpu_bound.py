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

from unittest.mock import MagicMock, patch

from bson import ObjectId

from model.job import Job, JobGpuRequest
from policies.gpu_bound import (
    get_number_of_reserved_gpus,
    get_submitted_gpu_bound_jobs_without_duplicates,
    mark_next_gpu_bound_jobs_ids_as_ready_for_scheduling_from_submitted_queue,
)
from policies.job_repo import SessionBasedPolicyJobRepo


def mock_job_repo(self, *args, **kwargs) -> None:
    self._collection_name = "jobs"
    SessionBasedPolicyJobRepo._mongo_client = MagicMock()  # type: ignore


@patch("scheduler.state_machine.JobMapper.backward")
@patch.object(SessionBasedPolicyJobRepo, "preliminary_aggregation_match_stage", return_value={})
@patch.object(SessionBasedPolicyJobRepo, "aggregate_read")
@patch.object(SessionBasedPolicyJobRepo, "__init__", new=mock_job_repo)
def test_get_submitted_gpu_bound_jobs_without_duplicates(
    mock_repo_aggregate,
    mock_preliminary_query,
    mock_mapper_backward,
) -> None:
    # Arrange
    document = MagicMock()
    job = MagicMock()
    mock_repo_aggregate.return_value = [document]
    mock_mapper_backward.return_value = job

    # Act
    result = get_submitted_gpu_bound_jobs_without_duplicates(gpu_jobs_types=["train"])

    # Assert
    mock_repo_aggregate.assert_called_once_with(
        [
            {
                "$match": {
                    "state": 0,
                    "type": {"$in": ["train"]},
                    "cancellation_info.is_cancelled": False,
                },
            },
            {
                "$lookup": {
                    "from": "jobs",
                    "localField": "key",
                    "foreignField": "key",
                    "as": "intermediate_duplicate",
                    "pipeline": [{}, {"$match": {"$and": [{"state": {"$gte": 1}}, {"state": {"$lt": 100}}]}}],
                }
            },
            {"$addFields": {"intermediate_duplicate_count": {"$size": "$intermediate_duplicate"}}},
            {"$match": {"intermediate_duplicate_count": 0}},
            {"$sort": {"priority": -1, "creation_time": 1}},
        ],
    )
    assert result == (job,)
    mock_preliminary_query.assert_called()


@patch.object(SessionBasedPolicyJobRepo, "update_many")
@patch.object(SessionBasedPolicyJobRepo, "__init__", new=mock_job_repo)
@patch("policies.gpu_bound.get_submitted_gpu_bound_jobs_without_duplicates")
@patch("policies.gpu_bound.get_number_of_reserved_gpus")
def test_mark_next_gpu_bound_jobs_ids_as_ready_for_scheduling_from_submitted_queue_busy(
    mock_get_number_of_reserved_gpus,
    mock_get_submitted_gpu_bound_jobs_without_duplicates,
    mock_update_many,
) -> None:
    # Arrange
    mock_get_number_of_reserved_gpus.return_value = 2

    # Act
    mark_next_gpu_bound_jobs_ids_as_ready_for_scheduling_from_submitted_queue(
        gpu_jobs_types=["train"], gpu_capacity=[2]
    )

    # Assert
    mock_get_number_of_reserved_gpus.assert_called_once_with(gpu_jobs_types=["train"])
    mock_get_submitted_gpu_bound_jobs_without_duplicates.assert_not_called()
    mock_update_many.assert_not_called()


@patch.object(SessionBasedPolicyJobRepo, "update_many")
@patch.object(SessionBasedPolicyJobRepo, "__init__", new=mock_job_repo)
@patch("policies.gpu_bound.get_submitted_gpu_bound_jobs_without_duplicates")
@patch("policies.gpu_bound.get_number_of_reserved_gpus")
def test_mark_next_gpu_bound_jobs_ids_as_ready_for_scheduling_from_submitted_queue_not_found(
    mock_get_number_of_reserved_gpus,
    mock_get_submitted_gpu_bound_jobs_without_duplicates,
    mock_update_many,
) -> None:
    # Arrange
    mock_get_number_of_reserved_gpus.return_value = 0
    mock_get_submitted_gpu_bound_jobs_without_duplicates.return_value = ()

    # Act
    mark_next_gpu_bound_jobs_ids_as_ready_for_scheduling_from_submitted_queue(
        gpu_jobs_types=["train"], gpu_capacity=[2]
    )

    # Assert
    mock_get_number_of_reserved_gpus.assert_called_once_with(gpu_jobs_types=["train"])
    mock_get_submitted_gpu_bound_jobs_without_duplicates.assert_called_once_with(gpu_jobs_types=["train"])
    mock_update_many.assert_not_called()


@patch.object(SessionBasedPolicyJobRepo, "update_many")
@patch.object(SessionBasedPolicyJobRepo, "__init__", new=mock_job_repo)
@patch("policies.gpu_bound.get_submitted_gpu_bound_jobs_without_duplicates")
@patch("policies.gpu_bound.get_number_of_reserved_gpus")
def test_mark_next_gpu_bound_jobs_ids_as_ready_for_scheduling_from_submitted_queue(
    mock_get_number_of_reserved_gpus,
    mock_get_submitted_gpu_bound_jobs_without_duplicates,
    mock_update_many,
) -> None:
    # Arrange
    mock_get_number_of_reserved_gpus.return_value = 0

    job1 = MagicMock(spec=Job)
    job1.id = ObjectId()
    job1.gpu = MagicMock(spec=JobGpuRequest)
    job1.gpu.num_required = 1

    job2 = MagicMock(spec=Job)
    job2.id = ObjectId()
    job2.gpu = MagicMock(spec=JobGpuRequest)
    job2.gpu.num_required = 3

    mock_get_submitted_gpu_bound_jobs_without_duplicates.return_value = (job1, job2)

    # Act
    mark_next_gpu_bound_jobs_ids_as_ready_for_scheduling_from_submitted_queue(
        gpu_jobs_types=["train"], gpu_capacity=[2]
    )

    # Assert
    mock_get_number_of_reserved_gpus.assert_called_once_with(gpu_jobs_types=["train"])
    mock_get_submitted_gpu_bound_jobs_without_duplicates.assert_called_once_with(gpu_jobs_types=["train"])
    mock_update_many.assert_called_once_with(
        filter={
            "_id": {"$in": [job1.id]},
            "state": 0,
            "cancellation_info.is_cancelled": False,
        },
        update={"$set": {"state": 1, "gpu.state": "RESERVED"}},
    )


@patch.object(SessionBasedPolicyJobRepo, "aggregate_read")
@patch.object(SessionBasedPolicyJobRepo, "__init__", new=mock_job_repo)
def test_get_number_of_reserved_gpus_empty(
    mock_repo_aggregate,
) -> None:
    # Arrange
    mock_repo_aggregate.return_value = []

    # Act
    result = get_number_of_reserved_gpus(gpu_jobs_types=["train"])

    # Assert
    mock_repo_aggregate.assert_called_once_with(
        [
            {"$match": {"type": {"$in": ["train"]}, "gpu.state": "RESERVED"}},
            {"$project": {"gpu_required": "$gpu.num_required"}},
        ],
    )
    assert result == 0


@patch.object(SessionBasedPolicyJobRepo, "aggregate_read")
@patch.object(SessionBasedPolicyJobRepo, "__init__", new=mock_job_repo)
def test_get_number_of_reserved_gpus(
    mock_repo_aggregate,
) -> None:
    # Arrange
    jobs = [{"gpu_required": 1} for _ in range(10)]
    mock_repo_aggregate.return_value = jobs

    # Act
    result = get_number_of_reserved_gpus(gpu_jobs_types=["train"])

    # Assert
    mock_repo_aggregate.assert_called_once_with(
        [
            {"$match": {"type": {"$in": ["train"]}, "gpu.state": "RESERVED"}},
            {"$project": {"gpu_required": "$gpu.num_required"}},
        ],
    )
    assert result == 10
