# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import time
from datetime import date, datetime, timezone
from datetime import time as datetime_time

from utils.enums import CreditSystemTimeBoundaries


def get_current_milliseconds_timestamp() -> int:
    """Returns current time in epoch milliseconds"""
    return time.time_ns() // 1_000_000


def get_current_day() -> int:
    """Returns current day's number"""
    return datetime.now(tz=timezone.utc).day


def get_current_date() -> date:
    """Returns current date in %Y-%m-%d format"""
    return datetime.now(tz=timezone.utc).date()


def get_current_datetime() -> datetime:
    """Returns current date and time"""
    return datetime.now(tz=timezone.utc)


def datetime_to_unix_milliseconds(dt: datetime) -> int:
    """
    Converts a datetime object dt into a Unix timestamp in milliseconds.
    """
    unix_timestamp_seconds = dt.timestamp()
    return int(unix_timestamp_seconds * 1_000)


def date_to_unix_milliseconds(dt: date) -> int:
    """
    Converts a date object dt into a Unix timestamp in milliseconds.
    """
    return datetime_to_unix_milliseconds(datetime.combine(dt, datetime.min.time(), tzinfo=timezone.utc))


def unix_milliseconds_to_datetime(milliseconds: int) -> datetime:
    """
    Converts a Unix timestamp in milliseconds to a datetime object.
    """
    seconds = milliseconds / 1000.0  # Convert milliseconds to seconds
    return datetime.fromtimestamp(seconds, timezone.utc)


def unix_milliseconds_to_date(milliseconds: int) -> date:
    """
    Converts a Unix timestamp in milliseconds to a date object.
    """
    return unix_milliseconds_to_datetime(milliseconds).date()


def get_current_month_start_timestamp() -> int:
    """Returns the time of the current month beginning, in milliseconds timestamp format"""
    current_date = get_current_date()
    first_day_of_month = current_date.replace(day=1)
    month_beginning_datetime = datetime.combine(first_day_of_month, datetime_time.min, tzinfo=timezone.utc)
    return datetime_to_unix_milliseconds(month_beginning_datetime)


def validate_credit_system_timestamp(value: int) -> None:
    """
    Validates if the provided integer value, representing a Unix timestamp in milliseconds,
    falls within the predefined credit system timeframe. Raises a ValueError if the value
    is not an integer or if it falls outside the expected range.
    """
    if not isinstance(value, int):
        raise ValueError(f"Value must be an integer, not {type(value)}")
    credit_system_start = CreditSystemTimeBoundaries.START.value
    credit_system_end = CreditSystemTimeBoundaries.END.value
    if credit_system_start > value or credit_system_end < value:
        raise ValueError(
            f"Value must be between {credit_system_start} and {credit_system_end}. Received value: {value}"
        )
