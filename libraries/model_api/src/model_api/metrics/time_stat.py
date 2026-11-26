#
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

from time import perf_counter
from typing import Any

MS_IN_SECOND = 1000.0

_DEFAULT_TOKEN = object()


class TimeStat:
    """
    A class to represent a statistical time metric.
    """

    def __init__(self):
        """
        Initializes the TimeStat object.
        """
        self.time = 0.0
        self.durations = []
        self.count = 0
        self._active_tokens: dict[Any, float] = {}

    def __add__(self, other):
        """
        Adds two TimeStat objects.

        Returns:
            TimeStat: A new TimeStat object representing the sum of the two.
        """
        if not isinstance(other, TimeStat):
            return NotImplemented

        new_stat = TimeStat()
        new_stat.time = self.time + other.time
        new_stat.durations = self.durations + other.durations
        new_stat.count = self.count + other.count
        return new_stat

    def update(self, token: Any | None = None) -> Any:
        """
        Updates the statistics with the latest duration.

        Args:
            token: Identifier for asynchronous measurements.

        Returns:
            Any: The token associated with the current timing segment.
        """

        key = token if token is not None else _DEFAULT_TOKEN
        time = perf_counter()
        start_time = self._active_tokens.pop(key, None)
        if start_time is None:
            self._active_tokens[key] = time
            return key

        diff = (time - start_time) * MS_IN_SECOND
        self.time += diff
        self.durations.append(diff)
        self.count += 1
        return key

    def reset(self) -> None:
        """
        Resets the statistics to their initial state.
        """
        self.time = 0.0
        self.durations = []
        self.count = 0
        self._active_tokens.clear()

    def mean(self) -> float:
        """
        Calculates the mean of the recorded durations.

        Returns:
            float: The mean of the recorded durations.
        """
        return self.time / self.count if self.count != 0 else 0.0

    def stddev(self) -> float:
        """
        Calculates the standard deviation of the recorded durations.

        Returns:
            float: The standard deviation of the recorded durations.
        """
        if self.count == 0:
            return 0.0
        mean = self.mean()
        variance = sum((x - mean) ** 2 for x in self.durations) / self.count
        return variance**0.5
