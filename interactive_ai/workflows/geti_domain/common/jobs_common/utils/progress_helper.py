# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module defines helpers used to construct progress callback functions"""

from collections.abc import Callable


def noop_progress_callback(progress: float, message: str) -> None:
    """
    No-op progress callback which does nothing (default implementation)
    """


def create_bounded_progress_callback(
    progress_callback: Callable[[float, str], None], start: float = 0, end: float = 100
) -> Callable[[float, str], None]:
    """
    Returns a new progress callback function that interpolates progress value from [0, 100] to [start, end].
    This can be helpful when progress must be reported by multiple sub-tasks.

    Example task progress with 2 sub-tasks:
        - sub-task 1 reports [0, 100] -> [0, 50]
        - sub-task 2 reports [0, 100] -> [50, 100]

    :param progress_callback: The original progress callback function
    :param start: The start value of the progress range
    :param end: The end value of the progress range
    :return: The bounded progress callback function
    """
    start = min(max(start, 0), 100)
    end = min(max(end, start), 100)

    def _bounded_callback(progress: float, message: str):
        # interpolate progress from [0, 100] to [start, end]
        progress = min(max(progress, 0), 100)
        scale = (end - start) / 100
        return progress_callback(int(start + progress * scale), message)

    return _bounded_callback
