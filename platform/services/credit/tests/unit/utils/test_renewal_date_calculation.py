# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from datetime import date

import pytest

from utils.renewal_date_calculation import get_next_renewal_date, get_prev_renewal_date, get_renewal_days
from utils.time import date_to_unix_milliseconds


@pytest.mark.parametrize(
    "start_date, end_date, expected_result",
    [
        (
            date_to_unix_milliseconds(date(year=2024, month=3, day=15)),
            date_to_unix_milliseconds(date(year=2024, month=3, day=21)),
            [15, 16, 17, 18, 19, 20],
        ),
        (
            date_to_unix_milliseconds(date(year=2025, month=2, day=28)),
            date_to_unix_milliseconds(date(year=2025, month=3, day=5)),
            [28, 29, 30, 31, 1, 2, 3, 4],
        ),
        (
            date_to_unix_milliseconds(date(year=2024, month=6, day=30)),
            date_to_unix_milliseconds(date(year=2024, month=7, day=5)),
            [30, 31, 1, 2, 3, 4],
        ),
        (
            date_to_unix_milliseconds(date(year=2023, month=6, day=25)),
            date_to_unix_milliseconds(date(year=2023, month=6, day=30)),
            [25, 26, 27, 28, 29],
        ),
    ],
)
def test_get_renewal_days(start_date, end_date, expected_result):
    result = get_renewal_days(start_date, end_date)
    assert sorted(result) == sorted(expected_result)


@pytest.mark.parametrize(
    "renewal_day, current_date, next_renewal_date",
    [
        (1, date(year=2024, month=3, day=1), date(year=2024, month=4, day=1)),
        (5, date(year=2024, month=12, day=10), date(year=2025, month=1, day=5)),
        (30, date(year=2024, month=1, day=31), date(year=2024, month=2, day=29)),
        (30, date(year=2023, month=1, day=31), date(year=2023, month=2, day=28)),
    ],
)
def test_get_next_renewal_date(renewal_day, current_date, next_renewal_date):
    assert get_next_renewal_date(renewal_day, current_date) == date_to_unix_milliseconds(next_renewal_date)


@pytest.mark.parametrize(
    "renewal_day, current_date, prev_renewal_date",
    [
        (10, date(year=2024, month=3, day=15), date(year=2024, month=3, day=10)),
        (31, date(year=2024, month=1, day=30), date(year=2023, month=12, day=31)),
        (31, date(year=2024, month=3, day=30), date(year=2024, month=2, day=29)),
        (31, date(year=2023, month=3, day=30), date(year=2023, month=2, day=28)),
    ],
)
def test_get_prev_renewal_date(renewal_day, current_date, prev_renewal_date):
    assert get_prev_renewal_date(renewal_day, current_date) == date_to_unix_milliseconds(prev_renewal_date)
