# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Utils for jobs aggregation pipelines.
Provides method to build a sub-pipeline to filter out jobs with running duplicates.
"""

import logging
from typing import Any

from model.job_state import JobState
from policies.job_repo import SessionBasedPolicyJobRepo

from sc_sdk.repos.base.session_repo import QueryAccessMode

logger = logging.getLogger(__name__)


def get_duplicate_check_sub_pipeline() -> list[dict[Any, Any]]:
    """
    Returns a sub-pipeline to filter out jobs with running duplicates.
    :return list[dict[Any, Any]]: sub-pipeline
    """
    job_repo = SessionBasedPolicyJobRepo()
    return [
        # Join jobs with duplicate "key" field
        {
            "$lookup": {
                "from": job_repo._collection_name,  # pylint: disable=protected-access
                "localField": "key",
                "foreignField": "key",
                "as": "intermediate_duplicate",
                "pipeline": [
                    job_repo.preliminary_aggregation_match_stage(QueryAccessMode.READ),
                    # Filter duplicate jobs by state, looking for intermediate ones
                    {
                        "$match": {
                            "$and": [
                                {"state": {"$gte": JobState.READY_FOR_SCHEDULING.value}},
                                {"state": {"$lt": JobState.FINISHED.value}},
                            ],
                        }
                    },
                ],
            }
        },
        # Count intermediate duplicate jobs
        {"$addFields": {"intermediate_duplicate_count": {"$size": "$intermediate_duplicate"}}},
        # Pick ones without intermediate duplicate jobs
        {"$match": {"intermediate_duplicate_count": 0}},
    ]
