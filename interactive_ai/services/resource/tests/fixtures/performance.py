# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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

import pytest

from sc_sdk.entities.metrics import (
    AnomalyLocalizationPerformance,
    ColorPalette,
    CurveMetric,
    LineChartInfo,
    LineMetricsGroup,
    Performance,
    ScoreMetric,
)


@pytest.fixture()
def fxt_project_performance():
    yield Performance(score=ScoreMetric(name="Project score", value=0.5))


@pytest.fixture
def fxt_training_performance():
    dashboard_metrics = [
        LineMetricsGroup(
            visualization_info=LineChartInfo(
                name="dummy_name",
                x_axis_label="x",
                y_axis_label="y",
                palette=ColorPalette.LABEL,
            ),
            metrics=[
                CurveMetric(
                    "dummy_label_name",
                    xs=[0, 1, 2],
                    ys=[1, 5, 8],
                )
            ],
        )
    ]
    yield Performance(
        score=ScoreMetric(name="accuracy", value=1),
        dashboard_metrics=dashboard_metrics,
    )


@pytest.fixture()
def fxt_anomaly_performance():
    yield AnomalyLocalizationPerformance(
        local_score=ScoreMetric(name="Dice coefficient", value=0.5),
        global_score=ScoreMetric(name="F1 score", value=0.75),
        dashboard_metrics=None,
    )


@pytest.fixture()
def fxt_project_performance_rest():
    yield {"score": 0.5}


@pytest.fixture()
def fxt_anomaly_performance_rest():
    yield {"local_score": 0.5, "global_score": 0.75}


@pytest.fixture()
def fxt_anomaly_reduced_performance_rest():
    yield {"score": 0.75}
