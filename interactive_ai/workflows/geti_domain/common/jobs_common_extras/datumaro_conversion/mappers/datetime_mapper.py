# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains the mapper for datetime."""

import datetime


class DatetimeMapper:
    """This class maps a `datetime.datetime` entity to a string, and vice versa."""

    @staticmethod
    def forward(instance: datetime.datetime) -> str:
        """Serializes datetime to str."""

        return instance.strftime("%Y-%m-%dT%H:%M:%S.%f")
