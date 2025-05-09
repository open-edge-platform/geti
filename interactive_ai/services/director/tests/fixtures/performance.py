# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

from iai_core.entities.metrics import (
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
