# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

# mypy: disable-error-code="operator"

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from dependencies import get_read_only_session
from rest.schema.common import NextPage
from rest.schema.transactions import TransactionsResponse
from routers import orgs_router as router
from service.transaction import TransactionService
from utils.enums import CreditSystemTimeBoundaries, ServiceName, Tags
from utils.time import get_current_milliseconds_timestamp, get_current_month_start_timestamp

logger = logging.getLogger(__name__)


@router.get(
    "/{organization_id}/transactions",
    tags=[Tags.TRANSACTIONS],
    status_code=status.HTTP_200_OK,
    response_model=TransactionsResponse,
)
def get_transactions(  # noqa: PLR0913
    organization_id: str,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=0)] = 3,
    from_date: Annotated[
        int | None,
        Query(
            ge=CreditSystemTimeBoundaries.START.value,
            le=CreditSystemTimeBoundaries.END.value,
            description="Milliseconds timestamp",
        ),
    ] = None,
    to_date: Annotated[
        int | None,
        Query(
            ge=CreditSystemTimeBoundaries.START.value,
            le=CreditSystemTimeBoundaries.END.value,
            description="Milliseconds timestamp",
        ),
    ] = None,
    sort: list[str] = Query(default=["created,desc"]),
    project_id: Annotated[str | None, Query()] = None,
    usage_type: Annotated[ServiceName | None, Query()] = None,
    session: Session = Depends(get_read_only_session),
) -> TransactionsResponse:
    """
    Returns information about transactions within specified time range [from_date, to_date].
    Response includes only transactions from the organization's lease account to the SaaS account -
    thus showing the final credits' consumption.
    Supports sorting and filtering by project name and usage type.
    """
    logger.debug(
        f"GET transactions request for organization: {organization_id}, skip param {skip}, limit {limit}, "
        f"from_date {from_date}, to_date {to_date}, sort {sort}, project_id {project_id}, usage_type {usage_type}"
    )

    if not from_date:
        from_date = get_current_month_start_timestamp()
    if not to_date:
        to_date = get_current_milliseconds_timestamp()

    if from_date >= to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Query parameter {from_date=} should be less then {to_date=}",
        )

    # Validate and parse sort parameter
    sort_params = []
    for s in sort:
        if "," not in s:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid sort parameter: {s}")
        field, direction = s.split(",", 1)
        if direction not in {"asc", "desc"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid sort direction: {direction}")
        if field == "timestamp":
            field = "created"  # Map 'timestamp' to 'created'
        sort_params.append((field, direction))

    total_matched, transactions = TransactionService(session=session).get_transactions(
        organization_id=organization_id,
        skip=skip,
        limit=limit,
        from_date=from_date,
        to_date=to_date,
        sort=sort_params,
        project_id=project_id,
        usage_type=usage_type,
    )

    next_page_skip = skip + limit
    next_page = NextPage(skip=next_page_skip, limit=limit) if total_matched > next_page_skip else None
    return TransactionsResponse(transactions=transactions, total_matched=total_matched, next_page=next_page)
