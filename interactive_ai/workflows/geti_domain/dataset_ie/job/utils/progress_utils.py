# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements progress reporting utilities
"""

import logging
import sys
import time

from jobs_common.tasks.utils.progress import report_progress, report_task_step_progress

logger = logging.getLogger(__name__)


MIN_INTERVAL_IN_SEC = 1  # minimum interval to avoid frequent progress update
INTERVAL_IN_SECONDS = 10  # default interval.
# In the UI, progress is displayed without decimal places,
# but it can be checked through the REST API,
# so to monitor the progress of large datasets,
# ensure that reporting is done at least every 10 seconds.

EPSILON = sys.float_info.epsilon


class ProgressReporter:
    """
    A class for reporting progress on individual steps within dataset import/export tasks.

    This class provides functionality to report the start, progress, and completion of steps
    within a task, with the ability to specify reporting intervals in both percentage and time.
    """

    def __init__(
        self,
        step_count: int,
        step_index: int,
        step_message: str,
        interval_in_percent: float = 0,
    ):
        """
        Initializes a new ProgressReporter instance with the given parameters.

        :param step_count: Total number of steps in the task.
        :param step_index: Index of the current step to be reported on.
        :param step_message: Message describing the current step.
        :param interval_in_percent: Frequency at which to report progress as a percentage
                                    of the current step's completion. Defaults to a value
                                    that represents 1% of the total progress if set to 0.
        :raises ValueError: If the step_count is less than or equal to 0.
        """
        if step_count <= 0:
            raise ValueError("Step count must be greater than 0.")

        # Initialize class variables
        self._step_count = step_count
        self._last_reported_time: float = 0
        self._last_reported_progress: float = 0

        # Initialize other class variables by calling reset_step
        self.reset_step(
            step_index=step_index,
            step_message=step_message,
            interval_in_percent=interval_in_percent,
        )

    def reset_step(
        self,
        step_index: int,
        step_message: str,
        interval_in_percent: float = 0,
    ) -> None:
        """
        Reinitializes the progress reporter to track a new step in the task.

        :param step_index: Index of the new step to be reported.
        :param step_message: A message describing the new step.
        :param interval_in_percent: Frequency of progress reporting in percent.
                                    See __init__ for more details.
        :raises ValueError: If the provided step_index is out of the valid range.
        """
        if not (0 <= step_index < self._step_count):
            raise ValueError("Step index is out of the valid range.")
        self._step_index = step_index
        self._step_message = step_message
        if interval_in_percent > EPSILON:
            self._interval_in_percent = interval_in_percent
        else:
            # <step_count>% in step progress == 1% in total progress
            self._interval_in_percent = float(self._step_count)
        self._update_last_reported(progress=0)

    def start_step(self, message: str = "") -> None:
        """
        Reports the initial progress as 0% and logs a start message for the step.

        :param message: Optional custom message to log when the step starts. If not provided,
                        a default message formatted as "<current_step_message> started" is used.
        """
        if not message:
            message = f"{self._step_message} started"
        self._report(progress=0, message=message)

    def finish_step(self, message: str = "") -> None:
        """
        Reports the final progress as 100% and logs a completion message for the step.

        :param message: Optional custom message to log upon step completion. If not provided,
                        a default message formatted as "<current_step_message> completed" is used.
        """
        if not message:
            message = f"{self._step_message} completed"
        self._report(progress=100, message=message)

    def _update_last_reported(self, progress: float) -> None:
        """
        Updates the last reported progress and the time at which it was reported.

        :param progress: The current progress percentage to be updated.
        """
        self._last_reported_time = time.time()
        self._last_reported_progress = progress

    def _report(self, progress: float, message: str) -> None:
        """
        Reports the current progress along with a message.

        :param progress: The current progress percentage to report.
        :param message: The message to accompany the progress report.
        :raises ValueError: If the progress is not within the range [0, 100].
        """
        if not (0 <= progress <= 100):
            raise ValueError("Progress value must be in range [0, 100].")
        report_task_step_progress(
            step_index=self._step_index, steps_count=self._step_count, step_progress=progress, step_message=message
        )
        self._update_last_reported(progress=progress)

    def report(self, processed: int, total: int) -> None:
        """
        Calculates and reports the progress based on the number of items processed.

        This method determines the current progress as a percentage of the total and
        reports it if the time since the last report exceeds the specified interval or
        if the progress has increased by the specified percentage interval.

        :param processed: The number of items that have been processed so far.
        :param total: The total number of items to process.
        """
        time_diff = time.time() - self._last_reported_time
        if time_diff < MIN_INTERVAL_IN_SEC:
            return  # avoid frequent report for small dataset
        progress = 100 * processed / total
        if time_diff >= INTERVAL_IN_SECONDS or (progress - self._last_reported_progress) >= self._interval_in_percent:
            self._report(progress=progress, message=self._step_message)


class WeightedProgressReporter(ProgressReporter):
    """
    A class that extends the 'ProgressReporter' class.

    While the ProgressReport divides progress equally among each steps,
    the WeightedProgressReporter allows individual steps to have different amounts of progress.
    """

    def __init__(
        self,
        steps_ratio: list[float],
        step_index: int,
        step_message: str,
        interval_in_percent: float = 0,
    ):
        """
        Initializes a new WeightedProgressReporter instance with the given parameters.

        :param steps_ratio: The ratio that each step occupies in the progress.
                            If the sum is not 1, it will be normalized to 1.
        :param step_index: Index of the current step to be reported on.
        :param step_message: Message describing the current step.
        :param interval_in_percent: Frequency at which to report progress as a percentage
                                    of the current step's completion. Defaults to a value
                                    that represents 1% of the total progress if set to 0.
        :raises ValueError: If the steps_ratio is wrong.
        """
        if not steps_ratio:
            raise ValueError("There must be at least one step or more.")
        total = sum(steps_ratio)
        if total == 0:
            raise ValueError("The sum of the step_ratio cannot be zero.")
        normalized_ratio: list[float] = []
        for ratio in steps_ratio:
            if ratio <= 0:
                raise ValueError("The progress ratio for each step must be positive.")
            normalized_ratio.append(ratio / total)
        self._steps_ratio = normalized_ratio

        # Initialize class variables
        self._last_reported_time: float = 0
        self._last_reported_progress: float = 0

        # Initialize other class variables by calling reset_step
        self.reset_step(
            step_index=step_index,
            step_message=step_message,
            interval_in_percent=interval_in_percent,
        )

    def reset_step(
        self,
        step_index: int,
        step_message: str,
        interval_in_percent: float = 0,
    ) -> None:
        """
        Reinitializes the progress reporter to track a new step in the task.

        :param step_index: Index of the new step to be reported.
        :param step_message: A message describing the new step.
        :param interval_in_percent: Frequency of progress reporting in percent.
                                    See __init__ for more details.
        :raises ValueError: If the provided step_index is out of the valid range.
        """
        if not (0 <= step_index < len(self._steps_ratio)):
            raise ValueError("Step index is out of the valid range.")
        self._step_index = step_index
        self._step_message = step_message
        if interval_in_percent > EPSILON:
            self._interval_in_percent = interval_in_percent
        else:
            # 1% in total progress
            self._interval_in_percent = 1 / self._steps_ratio[step_index]
        self._update_last_reported(progress=0)
        self._completed_progress = sum(self._steps_ratio[:step_index]) * 100

    def _report(self, progress: float, message: str) -> None:
        """
        Reports the current progress along with a message.

        :param progress: The current progress percentage to report.
        :param message: The message to accompany the progress report.
        :raises ValueError: If the progress is not within the range [0, 100].
        """
        if not (0 <= progress <= 100):
            raise ValueError("Progress value must be in range [0, 100].")
        total_progress = self._completed_progress + progress * self._steps_ratio[self._step_index]
        report_progress(progress=total_progress, message=message)
        self._update_last_reported(progress=progress)
