# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import time

from model_api.metrics import PerformanceMetrics, TimeStat

# --- TimeStat ---


def test_timestat_init():
    ts = TimeStat()
    assert ts.time == 0.0
    assert ts.count == 0
    assert ts.durations == []


def test_timestat_update():
    ts = TimeStat()
    # Start
    token = ts.update()
    time.sleep(0.01)
    # Stop
    ts.update(token)
    assert ts.count == 1
    assert ts.time > 0
    assert len(ts.durations) == 1


def test_timestat_update_default_token():
    ts = TimeStat()
    ts.update()  # start with default token
    time.sleep(0.01)
    ts.update()  # stop with default token
    assert ts.count == 1


def test_timestat_reset():
    ts = TimeStat()
    ts.update()
    time.sleep(0.01)
    ts.update()
    ts.reset()
    assert ts.time == 0.0
    assert ts.count == 0
    assert ts.durations == []


def test_timestat_mean():
    ts = TimeStat()
    assert ts.mean() == 0.0
    ts.time = 100.0
    ts.count = 4
    assert ts.mean() == 25.0


def test_timestat_stddev_empty():
    ts = TimeStat()
    assert ts.stddev() == 0.0


def test_timestat_stddev():
    ts = TimeStat()
    ts.durations = [10.0, 10.0, 10.0, 10.0]
    ts.count = 4
    ts.time = 40.0
    assert ts.stddev() == 0.0

    ts2 = TimeStat()
    ts2.durations = [10.0, 20.0]
    ts2.count = 2
    ts2.time = 30.0
    assert ts2.stddev() > 0


def test_timestat_add():
    ts1 = TimeStat()
    ts1.time = 10.0
    ts1.durations = [5.0, 5.0]
    ts1.count = 2

    ts2 = TimeStat()
    ts2.time = 20.0
    ts2.durations = [10.0, 10.0]
    ts2.count = 2

    ts3 = ts1 + ts2
    assert ts3.time == 30.0
    assert ts3.count == 4
    assert len(ts3.durations) == 4


def test_timestat_add_not_implemented():
    ts = TimeStat()
    result = ts.__add__("not a TimeStat")
    assert result is NotImplemented


# --- PerformanceMetrics ---


def test_perf_metrics_init():
    pm = PerformanceMetrics()
    assert isinstance(pm.load_time, TimeStat)
    assert isinstance(pm.inference_time, TimeStat)


def test_perf_metrics_getters():
    pm = PerformanceMetrics()
    assert pm.get_load_time() is pm.load_time
    assert pm.get_preprocess_time() is pm.preprocess_time
    assert pm.get_inference_time() is pm.inference_time
    assert pm.get_postprocess_time() is pm.postprocess_time
    assert pm.get_total_time() is pm.total_time


def test_perf_metrics_total_frames():
    pm = PerformanceMetrics()
    assert pm.get_total_frames() == 0
    pm.total_time.durations = [1.0, 2.0, 3.0]
    assert pm.get_total_frames() == 3


def test_perf_metrics_fps():
    pm = PerformanceMetrics()
    assert pm.get_fps() == 0.0
    pm.total_time.time = 1000.0  # 1 second
    pm.total_time.durations = [100.0] * 10
    assert pm.get_fps() == 10.0


def test_perf_metrics_total_time_min_max():
    pm = PerformanceMetrics()
    assert pm.get_total_time_min() == 0.0
    assert pm.get_total_time_max() == 0.0
    pm.total_time.durations = [5.0, 10.0, 15.0]
    assert pm.get_total_time_min() == 5.0
    assert pm.get_total_time_max() == 15.0


def test_perf_metrics_reset():
    pm = PerformanceMetrics()
    pm.load_time.time = 10.0
    pm.load_time.count = 1
    pm.preprocess_time.time = 5.0
    pm.preprocess_time.count = 1
    pm.reset()
    assert pm.preprocess_time.time == 0.0
    assert pm.load_time.time == 10.0  # not reset by default


def test_perf_metrics_reset_with_load():
    pm = PerformanceMetrics()
    pm.load_time.time = 10.0
    pm.load_time.count = 1
    pm.reset(include_load_time=True)
    assert pm.load_time.time == 0.0


def test_perf_metrics_add():
    pm1 = PerformanceMetrics()
    pm1.inference_time.time = 10.0
    pm1.inference_time.count = 1

    pm2 = PerformanceMetrics()
    pm2.inference_time.time = 20.0
    pm2.inference_time.count = 2

    pm3 = pm1 + pm2
    assert pm3.inference_time.time == 30.0
    assert pm3.inference_time.count == 3


def test_perf_metrics_add_not_implemented():
    pm = PerformanceMetrics()
    result = pm.__add__("not metrics")
    assert result is NotImplemented


def test_perf_metrics_log(caplog):
    import logging

    pm = PerformanceMetrics()
    pm.total_time.durations = [10.0]
    pm.total_time.time = 10.0
    pm.total_time.count = 1
    pm.preprocess_time.time = 2.0
    pm.preprocess_time.count = 1
    pm.preprocess_time.durations = [2.0]
    pm.inference_time.time = 5.0
    pm.inference_time.count = 1
    pm.inference_time.durations = [5.0]
    pm.postprocess_time.time = 3.0
    pm.postprocess_time.count = 1
    pm.postprocess_time.durations = [3.0]
    pm.load_time.time = 100.0
    pm.load_time.count = 1
    pm.load_time.durations = [100.0]
    with caplog.at_level(logging.INFO, logger="model_api.metrics.performance"):
        pm.log_metrics()
    assert "PERFORMANCE METRICS REPORT" in caplog.text
