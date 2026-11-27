#
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

import unittest

from model_api.metrics import TimeStat


class TestTimeStat(unittest.TestCase):
    def test_initial_state(self):
        stat = TimeStat()
        assert stat.time == 0.0
        assert stat.durations == []
        assert stat.count == 0
        assert stat.mean() == 0.0
        assert stat.stddev() == 0.0

    def test_update_increments(self):
        stat = TimeStat()
        stat.update()
        assert len(stat.durations) == 0
        stat.update()
        assert len(stat.durations) == 1
        assert abs(stat.time - stat.durations[0]) < 1e-7

    def test_reset(self):
        stat = TimeStat()
        stat.update()
        stat.reset()
        assert stat.time == 0.0
        assert stat.durations == []
        assert stat.count == 0

    def test_mean(self):
        stat = TimeStat()
        for _ in range(3):
            stat.update()
        expected_mean = stat.time / stat.count
        assert abs(stat.mean() - expected_mean) < 1e-7

    def test_stddev(self):
        stat = TimeStat()
        for _ in range(5):
            stat.update()
        assert stat.stddev() >= 0.0

    def test_add(self):
        stat1 = TimeStat()
        stat2 = TimeStat()
        for _ in range(2):
            stat1.update()
        for _ in range(3):
            stat2.update()
        stat3 = stat1 + stat2
        assert stat3.time == stat1.time + stat2.time
        assert stat3.count == stat1.count + stat2.count

    def test_add_invalid(self):
        stat = TimeStat()
        assert stat.__add__(42) == NotImplemented
