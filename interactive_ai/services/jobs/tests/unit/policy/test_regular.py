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

from policies.job_repo import SessionBasedPolicyJobRepo
from policies.regular import (
    get_next_regular_jobs_ids_to_schedule,
    get_number_of_running_jobs_by_types,
    mark_next_regular_jobs_as_ready_for_scheduling_from_submitted_queue,
)


def mock_job_repo(self, *args, **kwargs) -> None:
    self._collection_name = "jobs"
    SessionBasedPolicyJobRepo._mongo_client = MagicMock()  # type: ignore


@patch.object(SessionBasedPolicyJobRepo, "update_many")
@patch.object(SessionBasedPolicyJobRepo, "__init__", new=mock_job_repo)
@patch("policies.regular.get_next_regular_jobs_ids_to_schedule")
@patch("policies.regular.get_number_of_running_jobs_by_types")
def test_mark_next_regular_jobs_as_ready_for_scheduling_from_submitted_queue(
    mock_get_number_of_running_jobs_by_types,
    mock_get_next_regular_jobs_ids_to_schedule,
    mock_update_many,
) -> None:
    # Arrange
    mock_get_number_of_running_jobs_by_types.return_value = 2

    mock_get_next_regular_jobs_ids_to_schedule.return_value = ["id1", "id2", "id3"]

    # Act
    mark_next_regular_jobs_as_ready_for_scheduling_from_submitted_queue(types=["train"], max_number_of_running_jobs=10)

    # Assert
    mock_get_number_of_running_jobs_by_types.assert_called_once_with(types=["train"])
    # There are already 10 train jobs out of 10 max, but only 2 running optimize jobs out of 10,
    # so we can schedule 8 more
    mock_get_next_regular_jobs_ids_to_schedule.assert_called_once_with(types=["train"], num_jobs=8)
    mock_update_many.assert_called_once_with(
        filter={
            "_id": {"$in": ["id1", "id2", "id3"]},
            "state": 0,
            "cancellation_info.is_cancelled": False,
        },
        update={
            "$set": {
                "state": 1,
            }
        },
    )


@patch.object(SessionBasedPolicyJobRepo, "update_many")
@patch.object(SessionBasedPolicyJobRepo, "__init__", new=mock_job_repo)
@patch("policies.regular.get_next_regular_jobs_ids_to_schedule")
@patch("policies.regular.get_number_of_running_jobs_by_types")
def test_mark_next_regular_jobs_as_ready_for_scheduling_from_submitted_queue_busy(
    mock_get_number_of_running_jobs_by_types,
    mock_get_next_regular_jobs_ids_to_schedule,
    mock_update_many,
) -> None:
    # Arrange
    mock_get_number_of_running_jobs_by_types.return_value = 10

    # Act
    mark_next_regular_jobs_as_ready_for_scheduling_from_submitted_queue(types=["train"], max_number_of_running_jobs=10)

    # Assert
    mock_get_number_of_running_jobs_by_types.assert_called_once_with(types=["train"])
    mock_get_next_regular_jobs_ids_to_schedule.assert_not_called()
    mock_update_many.assert_not_called()


@patch.object(SessionBasedPolicyJobRepo, "preliminary_aggregation_match_stage", return_value={})
@patch.object(SessionBasedPolicyJobRepo, "aggregate_read")
@patch.object(SessionBasedPolicyJobRepo, "__init__", new=mock_job_repo)
def test_get_next_regular_jobs_ids_to_schedule(
    mock_repo_aggregate,
    mock_preliminary_query,
) -> None:
    # Arrange
    job_id = ObjectId()
    job = {"_id": str(job_id)}
    mock_repo_aggregate.return_value = [job]

    # Act
    result = get_next_regular_jobs_ids_to_schedule(types=["train"], num_jobs=10)

    # Assert
    mock_repo_aggregate.assert_called_once_with(
        [
            {
                "$match": {
                    "state": 0,
                    "type": {"$in": ["train"]},
                    "cancellation_info.is_cancelled": False,
                }
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
            {"$limit": 10},
        ]
    )
    assert result == [job_id]
    mock_preliminary_query.assert_called()


@patch.object(SessionBasedPolicyJobRepo, "aggregate_read")
@patch.object(SessionBasedPolicyJobRepo, "__init__", new=mock_job_repo)
def test_get_number_of_running_jobs_by_type(
    mock_repo_aggregate,
) -> None:
    # Arrange
    mock_repo_aggregate.return_value = [{"count": 10}]

    # Act
    result = get_number_of_running_jobs_by_types(types=["train"])

    # Assert
    mock_repo_aggregate.assert_called_once_with(
        [
            {
                "$match": {
                    "$and": [
                        {"state": {"$gte": 1}},
                        {"state": {"$lt": 100}},
                    ],
                    "type": {"$in": ["train"]},
                    "cancellation_info.is_cancelled": False,
                }
            },
            {"$count": "count"},
        ],
    )
    assert result == 10
