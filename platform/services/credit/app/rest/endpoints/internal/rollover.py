# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from datetime import datetime, time, timedelta, timezone
from typing import Annotated

from fastapi import Depends, Query, Response, status
from sqlalchemy.orm import Session

from dependencies import get_session
from routers import internal_router
from service.credit_account import CreditAccountService
from utils.enums import CreditSystemTimeBoundaries, Tags
from utils.time import datetime_to_unix_milliseconds, get_current_milliseconds_timestamp, unix_milliseconds_to_datetime

logger = logging.getLogger(__name__)


@internal_router.post(
    path="/credit_accounts/rollover", tags=[Tags.CREDIT_ACCOUNTS, Tags.INTERNAL], status_code=status.HTTP_200_OK
)
def rollover_credit_accounts(
    renewal_date: Annotated[
        int | None,
        Query(
            ge=CreditSystemTimeBoundaries.START.value,
            le=CreditSystemTimeBoundaries.END.value,
            description="Milliseconds timestamp",
        ),
    ] = None,
    db_session: Session = Depends(get_session),
) -> Response:
    """
    Performs credit accounts renewal.
    """
    if renewal_date is None:
        renewal_date = get_current_milliseconds_timestamp()

    base_time = datetime.combine(
        unix_milliseconds_to_datetime(renewal_date),
        time.min,
        timezone.utc,
    )
    logger.info(
        f"Calculated renewal base time: {base_time}. "
        f"Renewing subscriptions for the following 7 days, starting from the {base_time + timedelta(days=1)}"
    )
    start_date_time = datetime_to_unix_milliseconds(base_time + timedelta(days=1))
    logger.debug(f"{start_date_time=}")
    end_date_time = datetime_to_unix_milliseconds(base_time + timedelta(days=8))
    logger.debug(f"{end_date_time=}")
    CreditAccountService(session=db_session).rollover_credit_accounts(
        start_date_time=start_date_time, end_date_time=end_date_time, renewal_date=renewal_date
    )
    return Response(status_code=status.HTTP_200_OK)
