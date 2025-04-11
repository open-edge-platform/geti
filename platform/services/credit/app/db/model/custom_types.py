# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from datetime import datetime

from sqlalchemy import BigInteger
from sqlalchemy.types import TypeDecorator

from utils.time import datetime_to_unix_milliseconds, validate_credit_system_timestamp


class UnixTimestampInMilliseconds(TypeDecorator):
    impl = BigInteger
    cache_ok = True

    # convert datetime object to unix timestamp in milliseconds when inserting data to database
    def process_bind_param(self, value, dialect) -> int | None:  # noqa
        if isinstance(value, datetime):
            try:
                return datetime_to_unix_milliseconds(dt=value)
            except Exception as e:
                raise ValueError("Could not convert datetime to unix timestamp in milliseconds.") from e
        if value is not None:
            validate_credit_system_timestamp(value=value)
            return value
        return None
