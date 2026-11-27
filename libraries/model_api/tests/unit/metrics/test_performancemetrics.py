#
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

import unittest
from unittest.mock import MagicMock, patch

from model_api.metrics import PerformanceMetrics, TimeStat


class TestPerformanceMetrics(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.metrics = PerformanceMetrics()

    def test_initial_state(self):
        """Test that PerformanceMetrics initializes with correct default state."""
        assert isinstance(self.metrics.load_time, TimeStat)
        assert isinstance(self.metrics.preprocess_time, TimeStat)
        assert isinstance(self.metrics.inference_time, TimeStat)
        assert isinstance(self.metrics.postprocess_time, TimeStat)
        assert isinstance(self.metrics.total_time, TimeStat)

        assert self.metrics.load_time.time == 0.0
        assert self.metrics.preprocess_time.time == 0.0
        assert self.metrics.inference_time.time == 0.0
        assert self.metrics.postprocess_time.time == 0.0
        assert self.metrics.total_time.time == 0.0
        assert self.metrics.get_total_frames() == 0
        assert self.metrics.get_fps() == 0.0

    def test_reset(self):
        """Test that reset method resets all time statistics."""
        # Simulate some time measurements by directly setting values
        self.metrics.load_time.time = 1.0
        self.metrics.preprocess_time.time = 2.0
        self.metrics.inference_time.time = 3.0
        self.metrics.postprocess_time.time = 4.0
        self.metrics.total_time.time = 5.0

        self.metrics.load_time.durations = [1.0]
        self.metrics.preprocess_time.durations = [2.0]
        self.metrics.inference_time.durations = [3.0]
        self.metrics.postprocess_time.durations = [4.0]
        self.metrics.total_time.durations = [5.0]

        # Reset and verify all are back to initial state
        self.metrics.reset()

        assert self.metrics.load_time.time == 1.0
        assert self.metrics.preprocess_time.time == 0.0
        assert self.metrics.inference_time.time == 0.0
        assert self.metrics.postprocess_time.time == 0.0
        assert self.metrics.total_time.time == 0.0
        assert self.metrics.get_total_frames() == 0
        assert self.metrics.get_fps() == 0.0
        assert self.metrics.get_total_time_min() == 0.0
        assert self.metrics.get_total_time_max() == 0.0

        assert self.metrics.load_time.durations == [1.0]
        assert self.metrics.preprocess_time.durations == []
        assert self.metrics.inference_time.durations == []
        assert self.metrics.postprocess_time.durations == []
        assert self.metrics.total_time.durations == []

    def test_reset_including_load_time(self):
        """Test reset clears load time when requested."""
        self.metrics.load_time.time = 5.0
        self.metrics.load_time.durations = [5.0]

        self.metrics.reset(include_load_time=True)

        assert self.metrics.load_time.time == 0.0
        assert self.metrics.load_time.durations == []

    def test_get_load_time(self):
        """Test get_load_time method returns the correct TimeStat object."""
        self.metrics.load_time.time = 1.23
        load_time = self.metrics.get_load_time()
        assert load_time is self.metrics.load_time
        assert isinstance(load_time, TimeStat)
        assert load_time.time == 1.23

    def test_get_preprocess_time(self):
        """Test get_preprocess_time method returns the correct TimeStat object."""
        self.metrics.preprocess_time.time = 2.34
        preprocess_time = self.metrics.get_preprocess_time()
        assert preprocess_time is self.metrics.preprocess_time
        assert isinstance(preprocess_time, TimeStat)
        assert preprocess_time.time == 2.34

    def test_get_inference_time(self):
        """Test get_inference_time method returns the correct TimeStat object."""
        self.metrics.inference_time.time = 3.45
        inference_time = self.metrics.get_inference_time()
        assert inference_time is self.metrics.inference_time
        assert isinstance(inference_time, TimeStat)
        assert inference_time.time == 3.45

    def test_get_postprocess_time(self):
        """Test get_postprocess_time method returns the correct TimeStat object."""
        self.metrics.postprocess_time.time = 4.56
        postprocess_time = self.metrics.get_postprocess_time()
        assert postprocess_time is self.metrics.postprocess_time
        assert isinstance(postprocess_time, TimeStat)
        assert postprocess_time.time == 4.56

    def test_get_total_time(self):
        """Test get_total_time returns the total TimeStat object."""
        total_time = self.metrics.get_total_time()
        assert total_time is self.metrics.total_time

    def test_get_total_frames_empty(self):
        """Test get_total_frames returns 0 when no frames processed."""
        assert self.metrics.get_total_frames() == 0

    def test_get_total_frames_with_data(self):
        """Test get_total_frames returns correct count when frames are processed."""
        self.metrics.total_time.durations = [1.0, 2.0, 3.0]
        assert self.metrics.get_total_frames() == 3

    def test_get_fps_no_data(self):
        """Test get_fps returns 0.0 when no frames processed."""
        assert self.metrics.get_fps() == 0.0

    def test_get_fps_with_data(self):
        """Test get_fps calculates correctly when frames are processed."""
        self.metrics.total_time.durations = [1.0, 2.0, 3.0]
        self.metrics.total_time.time = 6.0
        expected_fps = 3 / (6.0 / 1000.0)
        assert abs(self.metrics.get_fps() - expected_fps) < 1e-7

    def test_get_fps_zero_total_time(self):
        """Test get_fps returns 0.0 when total time is zero."""
        self.metrics.total_time.durations = [0.0, 0.0]
        assert self.metrics.get_fps() == 0.0

    def test_add_valid_metrics(self):
        metrics1 = PerformanceMetrics()
        metrics2 = PerformanceMetrics()

        # Set up some mock data
        metrics1.load_time.time = 1.0
        metrics1.load_time.durations = [1.0]
        metrics1.preprocess_time.time = 2.0
        metrics1.preprocess_time.durations = [2.0]
        metrics1.inference_time.time = 3.0
        metrics1.inference_time.durations = [3.0]
        metrics1.postprocess_time.time = 4.0
        metrics1.postprocess_time.durations = [4.0]

        metrics2.load_time.time = 0.5
        metrics2.load_time.durations = [0.5]
        metrics2.preprocess_time.time = 1.5
        metrics2.preprocess_time.durations = [1.5]
        metrics2.inference_time.time = 2.5
        metrics2.inference_time.durations = [2.5]
        metrics2.postprocess_time.time = 3.5
        metrics2.postprocess_time.durations = [3.5]
        metrics1.total_time.time = 6.0
        metrics1.total_time.durations = [6.0]
        metrics2.total_time.time = 4.0
        metrics2.total_time.durations = [4.0]

        result = metrics1 + metrics2

        assert isinstance(result, PerformanceMetrics)
        assert result.load_time.time == 1.5
        assert result.preprocess_time.time == 3.5
        assert result.inference_time.time == 5.5
        assert result.postprocess_time.time == 7.5
        assert result.total_time.time == 10.0
        assert result.load_time.durations == [1.0, 0.5]
        assert result.preprocess_time.durations == [2.0, 1.5]
        assert result.inference_time.durations == [3.0, 2.5]
        assert result.postprocess_time.durations == [4.0, 3.5]
        assert result.total_time.durations == [6.0, 4.0]

    def test_add_invalid_type(self):
        """Test adding PerformanceMetrics with invalid type returns NotImplemented."""
        result = self.metrics.__add__(42)
        assert result == NotImplemented

        result = self.metrics.__add__("invalid")
        assert result == NotImplemented

        result = self.metrics.__add__(None)
        assert result == NotImplemented

    @patch("model_api.metrics.performance.logger")
    def test_log_metrics_empty(self, mock_logger):
        """Test log_metrics with empty metrics."""
        self.metrics.log_metrics()

        # Verify logger.info was called once
        mock_logger.info.assert_called_once()

        # Get the logged content and verify it contains expected metrics
        logged_content = mock_logger.info.call_args[0][0]

        assert "🚀 PERFORMANCE METRICS REPORT 🚀" in logged_content
        assert "Load Time: 0.00 ms" in logged_content
        assert "Preprocess:  0.00 ms ± 0.00 ms" in logged_content
        assert "Inference:   0.00 ms ± 0.00 ms" in logged_content
        assert "Postprocess: 0.00 ms ± 0.00 ms" in logged_content
        assert "Mean:  0.00 ms ± 0.00 ms" in logged_content
        assert "Min:   0.00 ms" in logged_content
        assert "Max:   0.00 ms" in logged_content
        assert "Total Frames: 0" in logged_content
        assert "FPS:          0.00" in logged_content

    @patch("model_api.metrics.performance.logger")
    def test_log_metrics_with_data(self, mock_logger):
        """Test log_metrics with actual data."""
        self.metrics.load_time.mean = MagicMock(return_value=1.234)
        self.metrics.preprocess_time.mean = MagicMock(return_value=2.345)
        self.metrics.preprocess_time.stddev = MagicMock(return_value=0.123)
        self.metrics.inference_time.mean = MagicMock(return_value=3.456)
        self.metrics.inference_time.stddev = MagicMock(return_value=0.234)
        self.metrics.postprocess_time.mean = MagicMock(return_value=4.567)
        self.metrics.postprocess_time.stddev = MagicMock(return_value=0.345)
        self.metrics.total_time.mean = MagicMock(return_value=10.123)
        self.metrics.total_time.stddev = MagicMock(return_value=0.456)
        self.metrics.total_time.durations = [1.0, 2.0, 3.0]  # 3 frames

        with patch.object(self.metrics, "get_fps", return_value=12.34):
            self.metrics.log_metrics()

        # Verify logger.info was called once
        mock_logger.info.assert_called_once()

        # Get the logged content and verify it contains expected metrics
        logged_content = mock_logger.info.call_args[0][0]

        assert "🚀 PERFORMANCE METRICS REPORT 🚀" in logged_content
        assert "Load Time: 1.23 ms" in logged_content
        assert "Preprocess:  2.35 ms ± 0.12 ms" in logged_content
        assert "Inference:   3.46 ms ± 0.23 ms" in logged_content
        assert "Postprocess: 4.57 ms ± 0.34 ms" in logged_content  # 0.345 rounds to 0.34
        assert "Mean:  10.12 ms ± 0.46 ms" in logged_content
        assert "Min:   1.00 ms" in logged_content
        assert "Max:   3.00 ms" in logged_content
        assert "Total Frames: 3" in logged_content
        assert "FPS:          12.34" in logged_content

    def test_integration_with_timestat(self):
        """Test integration with actual TimeStat operations."""
        metrics = PerformanceMetrics()

        metrics.load_time.update()
        metrics.load_time.update()
        metrics.preprocess_time.update()
        metrics.preprocess_time.update()

        assert len(metrics.load_time.durations) == 1
        assert len(metrics.preprocess_time.durations) == 1
        assert metrics.load_time.time > 0
        assert metrics.preprocess_time.time > 0
