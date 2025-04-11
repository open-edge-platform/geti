# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import logging
from calendar import monthrange
from datetime import date, datetime, timedelta, timezone

from dateutil.relativedelta import relativedelta

from utils.time import date_to_unix_milliseconds, get_current_date, unix_milliseconds_to_datetime

logger = logging.getLogger(__name__)


def get_renewal_days(start_timestamp: int, end_timestamp: int) -> list[int]:
    """
    Returns a list of days between provided dates.
    If the start date is the last day of the month and the month has fewer than 31 days,
    the result will also include the list of remaining days (e.g., if the date's 28.02.2025 -> [..., 28, 29, 30, 31])
    """
    start_date, end_date = unix_milliseconds_to_datetime(start_timestamp), unix_milliseconds_to_datetime(end_timestamp)
    renewal_days = set()
    current_date = start_date
    while current_date < end_date:
        renewal_days.add(current_date.day)
        current_date += timedelta(days=1)

    # if the dates span across two months, make sure 29, 30, and 31 are added
    if start_date.month != end_date.month:
        for day in [29, 30, 31]:
            if day > start_date.day:
                renewal_days.add(day)

    return sorted(renewal_days)


def get_next_renewal_date(renewal_day: int, current_date: date | None = None) -> int:
    """
    Calculates the nearest upcoming renewal date in relation to the current date

    :param renewal_day: the day of month when a subscription is renewed
    :param current_date: the reference date used for calculating the next renewal date
    :return: the date when the next subscription cycle starts.
    """

    if current_date is None:
        current_date = get_current_date()
    (_, num_days_in_month) = monthrange(current_date.year, current_date.month)
    next_date = datetime(
        year=current_date.year, month=current_date.month, day=min(num_days_in_month, renewal_day), tzinfo=timezone.utc
    ).date()

    if next_date <= current_date:
        next_date = next_date + relativedelta(months=1)
        (_, num_days_in_month) = monthrange(next_date.year, next_date.month)
        next_date = next_date.replace(day=min(num_days_in_month, renewal_day))

    logger.debug(f"Calculated next renewal date: {next_date}")
    return date_to_unix_milliseconds(next_date)


def get_prev_renewal_date(renewal_day: int, current_date: date | None = None) -> int:
    """
    Calculates the renewal date for the current subscription cycle in relation to the current date.

    :param renewal_day: the day of month when a subscription is renewed
    :param current_date: the reference date used for calculating the previous renewal date
    :return: the date when the current subscription cycle started.
    """

    if current_date is None:
        current_date = get_current_date()
    (_, num_days_in_month) = monthrange(current_date.year, current_date.month)
    prev_date = datetime(
        year=current_date.year, month=current_date.month, day=min(num_days_in_month, renewal_day), tzinfo=timezone.utc
    ).date()

    if prev_date > current_date:
        prev_date = prev_date - relativedelta(months=1)
        (_, num_days_in_month) = monthrange(prev_date.year, prev_date.month)
        prev_date = prev_date.replace(day=min(num_days_in_month, renewal_day))

    logger.debug(f"Calculated previous renewal date: {prev_date}")
    return date_to_unix_milliseconds(prev_date)
