# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.
"""Test progress utils"""

from unittest.mock import ANY, patch

import pytest

from job.utils.progress_utils import ProgressReporter, WeightedProgressReporter


@pytest.mark.JobsComponent
class TestProgressUtils:
    def test_progress_reporter(self):
        # Arrange
        steps_count = 3
        step_index = 0
        start_message = "Starting step"
        finish_message = "Step completed"
        processing_message = "Step in progress"
        reporter = ProgressReporter(step_count=steps_count, step_index=step_index, step_message="Step")

        # Act & Assert
        with patch("job.utils.progress_utils.report_task_step_progress") as mock_report_task_step_progress:
            reporter.start_step()
            mock_report_task_step_progress.assert_called_with(
                step_index=0, steps_count=steps_count, step_progress=0, step_message=ANY
            )
            reporter.start_step(start_message)
            mock_report_task_step_progress.assert_called_with(
                step_index=0, steps_count=steps_count, step_progress=0, step_message=start_message
            )

        # Act & Assert
        with patch("job.utils.progress_utils.report_task_step_progress") as mock_report_task_step_progress:
            reporter.finish_step()
            mock_report_task_step_progress.assert_called_with(
                step_index=0, steps_count=steps_count, step_progress=100, step_message=ANY
            )
            reporter.finish_step(finish_message)
            mock_report_task_step_progress.assert_called_with(
                step_index=0, steps_count=steps_count, step_progress=100, step_message=finish_message
            )

        # Act & Assert
        with patch("job.utils.progress_utils.report_task_step_progress") as mock_report_task_step_progress:
            reporter._report(50, processing_message)
            mock_report_task_step_progress.assert_called_with(
                step_index=0, steps_count=steps_count, step_progress=50, step_message=processing_message
            )

        # Act & Assert
        step_message = "Step 2"
        with (
            patch("job.utils.progress_utils.MIN_INTERVAL_IN_SEC", 1),
            patch("job.utils.progress_utils.report_task_step_progress") as mock_report_task_step_progress,
        ):
            reporter.reset_step(1, step_message, interval_in_percent=0)
            reporter.report(50, 100)
            mock_report_task_step_progress.assert_not_called()

        # Act & Assert
        with (
            patch("job.utils.progress_utils.MIN_INTERVAL_IN_SEC", 0),
            patch("job.utils.progress_utils.report_task_step_progress") as mock_report_task_step_progress,
        ):
            reporter.reset_step(1, step_message, interval_in_percent=0)
            reporter.report(50, 100)
            mock_report_task_step_progress.assert_called_with(
                step_index=1, steps_count=steps_count, step_progress=50, step_message=step_message
            )

    def test_progress_reporter_with_error(self):
        # Arrange
        message = "message"

        # Act & Assert
        with pytest.raises(ValueError) as e:
            reporter = ProgressReporter(step_count=0, step_index=0, step_message=message)
            assert "Step count must be greater than 0." == str(e.value)

        reporter = ProgressReporter(step_count=2, step_index=0, step_message=message)

        # Act & Assert
        with pytest.raises(ValueError) as e:
            reporter.reset_step(step_index=-1, step_message=message)
            assert "Step index is out of the valid range." == str(e.value)

        # Act & Assert
        with pytest.raises(ValueError) as e:
            reporter._report(-1, message)
            assert "Progress value must be in range [0, 100]." == str(e.value)

        # Act & Assert
        with pytest.raises(ValueError) as e:
            reporter._report(101, message)
            assert "Progress value must be in range [0, 100]." == str(e.value)

    def test_weighted_progress_reporter(self):
        # Arrange
        steps_ratio = [0.3, 0.2, 0.5]
        step_index = 0
        start_message = "Starting step"
        finish_message = "Step completed"
        processing_message = "Step in progress"
        reporter = WeightedProgressReporter(steps_ratio=steps_ratio, step_index=step_index, step_message="Step")

        # Act & Assert
        with patch("job.utils.progress_utils.report_progress") as mock_report_progress:
            reporter.start_step()
            mock_report_progress.assert_called_with(progress=0, message=ANY)
            reporter.start_step(start_message)
            mock_report_progress.assert_called_with(progress=0, message=start_message)

        # Act & Assert
        with patch("job.utils.progress_utils.report_progress") as mock_report_progress:
            reporter.finish_step()
            mock_report_progress.assert_called_with(progress=30, message=ANY)
            reporter.finish_step(finish_message)
            mock_report_progress.assert_called_with(progress=30, message=finish_message)

        # Act & Assert
        with patch("job.utils.progress_utils.report_progress") as mock_report_progress:
            reporter._report(50, processing_message)
            mock_report_progress.assert_called_with(progress=15, message=processing_message)

        # Act & Assert
        step_message = "Step 2"
        with (
            patch("job.utils.progress_utils.MIN_INTERVAL_IN_SEC", 1),
            patch("job.utils.progress_utils.report_progress") as mock_report_progress,
        ):
            reporter.reset_step(1, step_message, interval_in_percent=0)
            reporter.report(50, 100)
            mock_report_progress.assert_not_called()

        # Act & Assert
        with (
            patch("job.utils.progress_utils.MIN_INTERVAL_IN_SEC", 0),
            patch("job.utils.progress_utils.report_progress") as mock_report_progress,
        ):
            reporter.reset_step(1, step_message, interval_in_percent=0)
            reporter.report(50, 100)
            mock_report_progress.assert_called_with(progress=40, message=step_message)

    def test_weighted_progress_reporter_with_error(self):
        # Arrange
        message = "message"

        # Act & Assert
        with pytest.raises(ValueError) as e:
            reporter = WeightedProgressReporter(steps_ratio=[], step_index=0, step_message=message)
            assert "There must be at least one step or more." == str(e.value)

        # Act & Assert
        with pytest.raises(ValueError) as e:
            reporter = WeightedProgressReporter(steps_ratio=[0.0, 0.0], step_index=0, step_message=message)
            assert "The sum of the step_ratio cannot be zero." == str(e.value)

        # Act & Assert
        with pytest.raises(ValueError) as e:
            reporter = WeightedProgressReporter(steps_ratio=[-0.2, 0.3], step_index=0, step_message=message)
            assert "The progress ratio for each step must be positive." == str(e.value)

        reporter = WeightedProgressReporter(steps_ratio=[0.2, 0.3, 0.5], step_index=0, step_message=message)

        # Act & Assert
        with pytest.raises(ValueError) as e:
            reporter.reset_step(step_index=-1, step_message=message)
            assert "Step index is out of the valid range." == str(e.value)

        # Act & Assert
        with pytest.raises(ValueError) as e:
            reporter._report(-1, message)
            assert "Progress value must be in range [0, 100]." == str(e.value)

        # Act & Assert
        with pytest.raises(ValueError) as e:
            reporter._report(101, message)
            assert "Progress value must be in range [0, 100]." == str(e.value)
