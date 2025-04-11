# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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
import logging
from enum import Enum
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from starlette.responses import JSONResponse

from communication.constants import MAX_N_MEDIA_RETURNED
from communication.rest_controllers import MediaScoreRESTController
from usecases.dataset_filter import DatasetFilterSortDirection, MediaScoreFilterField

from geti_fastapi_tools.dependencies import (
    get_project_id,
    get_request_json,
    get_test_id,
    get_workspace_id,
    setup_session_fastapi,
)
from geti_types import ID

logger = logging.getLogger(__name__)

media_score_api_prefix_url = "/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}"
media_score_router = APIRouter(
    prefix=media_score_api_prefix_url, tags=["Media Score"], dependencies=[Depends(setup_session_fastapi)]
)

Skip = Annotated[int, Query(ge=0)]


class SortBy(str, Enum):
    """Sort by fields for media score"""

    score = "score"


class SortDirection(str, Enum):
    """Sort direction for media score filtering"""

    asc = "asc"
    dsc = "dsc"


@media_score_router.post("/tests/{test_id}/results:query")
def media_scores_query(  # noqa: PLR0913
    request_json: Annotated[dict, Depends(get_request_json)],
    workspace_id: Annotated[ID, Depends(get_workspace_id)],  # noqa: ARG001
    project_id: Annotated[ID, Depends(get_project_id)],
    test_id: Annotated[ID, Depends(get_test_id)],
    limit: Annotated[int, Query(ge=1, le=MAX_N_MEDIA_RETURNED)] = MAX_N_MEDIA_RETURNED,
    skip: Skip = 0,
    sort_by: Annotated[SortBy, Query()] = SortBy.score,
    sort_direction: Annotated[SortDirection, Query()] = SortDirection.asc,
) -> JSONResponse:
    """Endpoint to query media scores"""
    query = {} if request_json is None else request_json
    result = MediaScoreRESTController().get_filtered_items(
        project_id=project_id,
        model_test_result_id=test_id,
        sort_by=MediaScoreFilterField[sort_by.upper()],
        sort_direction=DatasetFilterSortDirection[sort_direction.upper()],
        limit=limit,
        skip=skip,
        query=query,
    )
    return JSONResponse(result)
