# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from datetime import datetime, timezone


def now() -> datetime:
    """
    Return the current UTC creation_date and time up to a millisecond accuracy.

    This function is preferable over the Python datetime.datetime.now() function
    because it uses the same accuracy (milliseconds) as MongoDB rather than microsecond accuracy.

    :return: Date and time up to a millisecond precision.
    """
    date = datetime.now(timezone.utc)
    return date.replace(microsecond=(date.microsecond // 1000) * 1000)
