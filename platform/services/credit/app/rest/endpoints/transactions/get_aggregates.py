# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from typing import Annotated

from fastapi import Depends, Query, status
from sqlalchemy.orm import Session

from dependencies import get_read_only_session
from rest.schema.transactions import AggregatesResponse
from routers import orgs_router as router
from service.transaction import TransactionService
from utils.enums import AggregatesKey, CreditSystemTimeBoundaries, Tags
from utils.time import datetime_to_unix_milliseconds, get_current_datetime, get_current_milliseconds_timestamp

logger = logging.getLogger(__name__)


def _get_key_parameter(key: list[AggregatesKey] = Query(None)) -> list[AggregatesKey]:
    """
    Validates and returns the 'key' query parameter as a list of AggregatesKey.

    Returns:
        A validated list of AggregatesKey enum values.

    Raises:
        HTTPException: 400 error if 'key' is not provided or is an empty list.

    Usage:
        Use as a dependency in FastAPI route handlers to enforce 'key' parameter.
    """
    if key is None or len(key) == 0:
        raise ValueError("The 'key' query parameter is required and must not be empty.")

    return key


@router.get(
    "/{organization_id}/transactions/aggregates",
    tags=[Tags.TRANSACTIONS],
    status_code=status.HTTP_200_OK,
    response_model=AggregatesResponse,
)
def get_credit_consumption_aggregates(
    organization_id: str,
    key: list[AggregatesKey] = Depends(_get_key_parameter),
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
    project_id: Annotated[list[str] | None, Query()] = None,
    session: Session = Depends(get_read_only_session),
) -> AggregatesResponse:
    """
    The Aggregating endpoint allows to retrieve credit consumption grouped by various
    dimensions such as project and service, date, etc.
    """
    logger.debug(
        f"Transaction aggregation called with the following query parameters: {key=}, {project_id=}, "
        f"{from_date=}, {to_date=}"
    )

    if from_date is None:
        current_datetime = get_current_datetime()
        from_date = datetime_to_unix_milliseconds(
            current_datetime.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        )
        logger.debug(f"from_date query parameter not set. Setting to first day of current month - {from_date}.")
    if to_date is None:
        to_date = get_current_milliseconds_timestamp()
        logger.debug(f"to_date query parameter not set. Setting to current day - {to_date}.")

    return TransactionService(session=session).aggregate_transactions(
        organization_id=organization_id,
        aggregate_keys=key,
        from_date=from_date,
        to_date=to_date,
        projects=project_id,
    )
