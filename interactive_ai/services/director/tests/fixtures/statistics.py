# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

from tests.fixtures.values import DummyValues

from sc_sdk.entities.metrics import (
    BarChartInfo,
    BarMetricsGroup,
    ColorPalette,
    CountMetric,
    CurveMetric,
    DateMetric,
    DurationMetric,
    LineChartInfo,
    LineMetricsGroup,
    MatrixChartInfo,
    MatrixMetric,
    MatrixMetricsGroup,
    NullMetric,
    ScoreMetric,
    StringMetric,
    TextChartInfo,
    TextMetricsGroup,
    VisualizationType,
)


@pytest.fixture
def fxt_duration_metric():
    yield DurationMetric.from_seconds(
        name=DummyValues.METRICS_GROUP_NAME,
        seconds=DummyValues.DURATION_METRIC_AS_SECONDS,
    )


@pytest.fixture
def fxt_duration_metric_rest():
    yield DummyValues.DURATION_METRIC_AS_STRING


@pytest.fixture
def fxt_date_metric():
    yield DateMetric(name=DummyValues.DATE_METRIC_NAME, value=DummyValues.DATE_METRIC_AS_DATETIME)


@pytest.fixture
def fxt_date_metric_rest():
    yield DummyValues.DATE_METRIC_AS_STRING


@pytest.fixture
def fxt_text_metrics_group_with_duration(fxt_duration_metric):
    yield TextMetricsGroup(
        visualization_info=TextChartInfo(
            name=DummyValues.METRICS_GROUP_NAME,
        ),
        metrics=[fxt_duration_metric],
    )


@pytest.fixture
def fxt_text_metrics_group_with_duration_rest(fxt_duration_metric_rest):
    yield {
        "header": DummyValues.METRICS_GROUP_NAME,
        "type": VisualizationType.TEXT.name.lower(),
        "key": DummyValues.METRICS_GROUP_NAME,
        "value": fxt_duration_metric_rest,
    }


@pytest.fixture
def fxt_curve_metric():
    yield CurveMetric(
        DummyValues.CURVE_METRIC_NAME,
        xs=DummyValues.CURVE_METRIC_X_VALUES,
        ys=DummyValues.CURVE_METRIC_Y_VALUES,
    )


@pytest.fixture
def fxt_curve_metric_with_nan():
    yield CurveMetric(
        DummyValues.CURVE_METRIC_NAME,
        xs=DummyValues.CURVE_METRIC_X_VALUES,
        ys=DummyValues.CURVE_METRIC_Y_VALUES_WITH_NAN,
    )


@pytest.fixture
def fxt_curve_metric_per_label():
    yield CurveMetric(
        DummyValues.LABEL_NAME,
        xs=DummyValues.CURVE_METRIC_X_VALUES,
        ys=DummyValues.CURVE_METRIC_Y_VALUES,
    )


@pytest.fixture
def fxt_curve_metric_rest():
    yield {
        "header": DummyValues.CURVE_METRIC_NAME,
        "key": DummyValues.CURVE_METRIC_NAME,
        "points": [
            {"x": x, "y": y, "type": "point"}
            for x, y in zip(DummyValues.CURVE_METRIC_X_VALUES, DummyValues.CURVE_METRIC_Y_VALUES)
        ],
        "color": None,
    }


@pytest.fixture
def fxt_curve_metric_after_nan_rest():
    yield {
        "header": DummyValues.CURVE_METRIC_NAME,
        "key": DummyValues.CURVE_METRIC_NAME,
        "points": [
            {"x": x, "y": y, "type": "point"}
            for x, y in zip(
                DummyValues.CURVE_METRIC_X_VALUES,
                DummyValues.CURVE_METRIC_Y_VALUES_AFTER_NAN,
            )
        ],
        "color": None,
    }


@pytest.fixture
def fxt_curve_metric_rest_per_label():
    yield {
        "header": DummyValues.LABEL_NAME,
        "key": DummyValues.LABEL_NAME,
        "points": [
            {"x": x, "y": y, "type": "point"}
            for x, y in zip(DummyValues.CURVE_METRIC_X_VALUES, DummyValues.CURVE_METRIC_Y_VALUES)
        ],
        "color": DummyValues.LABEL_COLOR.hex_str,
    }


@pytest.fixture
def fxt_line_chart_metric_group(fxt_curve_metric):
    yield LineMetricsGroup(
        visualization_info=LineChartInfo(name=DummyValues.METRICS_GROUP_NAME, x_axis_label="x", y_axis_label="y"),
        metrics=[fxt_curve_metric],
    )


@pytest.fixture
def fxt_line_chart_metric_group_with_nan(fxt_curve_metric_with_nan):
    yield LineMetricsGroup(
        visualization_info=LineChartInfo(name=DummyValues.METRICS_GROUP_NAME, x_axis_label="x", y_axis_label="y"),
        metrics=[fxt_curve_metric_with_nan],
    )


@pytest.fixture
def fxt_line_chart_metric_group_per_label(fxt_curve_metric_per_label):
    yield LineMetricsGroup(
        visualization_info=LineChartInfo(
            name=DummyValues.METRICS_GROUP_NAME,
            x_axis_label="x",
            y_axis_label="y",
            palette=ColorPalette.LABEL,
        ),
        metrics=[fxt_curve_metric_per_label],
    )


@pytest.fixture
def fxt_line_chart_metric_group_rest(fxt_curve_metric_rest):
    yield {
        "header": DummyValues.METRICS_GROUP_NAME,
        "type": VisualizationType.LINE.name.lower(),
        "key": DummyValues.METRICS_GROUP_NAME,
        "value": {
            "x_axis_label": "x",
            "y_axis_label": "y",
            "line_data": [fxt_curve_metric_rest],
        },
    }


@pytest.fixture
def fxt_line_chart_metric_after_nan_group_rest(fxt_curve_metric_after_nan_rest):
    yield {
        "header": DummyValues.METRICS_GROUP_NAME,
        "type": VisualizationType.LINE.name.lower(),
        "key": DummyValues.METRICS_GROUP_NAME,
        "value": {
            "x_axis_label": "x",
            "y_axis_label": "y",
            "line_data": [fxt_curve_metric_after_nan_rest],
        },
    }


@pytest.fixture
def fxt_line_chart_metric_group_rest_per_label(fxt_curve_metric_rest_per_label):
    yield {
        "header": DummyValues.METRICS_GROUP_NAME,
        "type": VisualizationType.LINE.name.lower(),
        "key": DummyValues.METRICS_GROUP_NAME,
        "value": {
            "x_axis_label": "x",
            "y_axis_label": "y",
            "line_data": [fxt_curve_metric_rest_per_label],
        },
    }


@pytest.fixture
def fxt_matrix_metric():
    yield MatrixMetric(
        name=DummyValues.MATRIX_METRIC_NAME,
        matrix_values=DummyValues.MATRIX_METRIC_VALUES,
        row_labels=DummyValues.MATRIX_METRIC_ROWS,
        column_labels=DummyValues.MATRIX_METRIC_COLS,
    )


@pytest.fixture
def fxt_matrix_metric_rest():
    yield {
        "header": DummyValues.MATRIX_METRIC_NAME,
        "key": DummyValues.MATRIX_METRIC_NAME,
        "row_names": DummyValues.MATRIX_METRIC_ROWS,
        "column_names": DummyValues.MATRIX_METRIC_COLS,
        "matrix_values": DummyValues.MATRIX_METRIC_VALUES.tolist(),
    }


@pytest.fixture
def fxt_matrix_metrics_group(fxt_matrix_metric):
    yield MatrixMetricsGroup(
        visualization_info=MatrixChartInfo(name=DummyValues.METRICS_GROUP_NAME, row_header="row", column_header="col"),
        metrics=[fxt_matrix_metric],
    )


@pytest.fixture
def fxt_matrix_metrics_group_rest(fxt_matrix_metric_rest):
    yield {
        "header": DummyValues.METRICS_GROUP_NAME,
        "type": VisualizationType.MATRIX.name.lower(),
        "key": DummyValues.METRICS_GROUP_NAME,
        "value": {
            "row_header": "row",
            "column_header": "col",
            "matrix_data": [fxt_matrix_metric_rest],
        },
    }


@pytest.fixture
def fxt_bar_metrics_group(fxt_score_metric):
    yield BarMetricsGroup(
        visualization_info=BarChartInfo(
            name=DummyValues.METRICS_GROUP_NAME,
        ),
        metrics=[fxt_score_metric],
    )


@pytest.fixture
def fxt_bar_metrics_group_per_label(fxt_score_metric_per_label):
    yield BarMetricsGroup(
        visualization_info=BarChartInfo(name=DummyValues.METRICS_GROUP_NAME, palette=ColorPalette.LABEL),
        metrics=[fxt_score_metric_per_label],
    )


@pytest.fixture
def fxt_bar_metrics_group_rest():
    yield {
        "header": DummyValues.METRICS_GROUP_NAME,
        "type": VisualizationType.BAR.name.lower(),
        "key": DummyValues.METRICS_GROUP_NAME,
        "value": [
            {
                "header": DummyValues.SCORE_METRIC_NAME,
                "key": DummyValues.SCORE_METRIC_NAME,
                "value": DummyValues.SCORE_METRIC_VALUE,
                "color": None,
            }
        ],
    }


@pytest.fixture
def fxt_bar_metrics_group_per_label_rest():
    yield {
        "header": DummyValues.METRICS_GROUP_NAME,
        "type": VisualizationType.BAR.name.lower(),
        "key": DummyValues.METRICS_GROUP_NAME,
        "value": [
            {
                "header": DummyValues.LABEL_NAME,
                "key": DummyValues.LABEL_NAME,
                "value": DummyValues.SCORE_METRIC_VALUE,
                "color": DummyValues.LABEL_COLOR.hex_str,
            }
        ],
    }


@pytest.fixture
def fxt_score_metric():
    yield ScoreMetric(name=DummyValues.SCORE_METRIC_NAME, value=DummyValues.SCORE_METRIC_VALUE)


@pytest.fixture
def fxt_score_metric_per_label():
    yield ScoreMetric(name=DummyValues.LABEL_NAME, value=DummyValues.SCORE_METRIC_VALUE)


@pytest.fixture
def fxt_score_metric_rest():
    yield round(DummyValues.SCORE_METRIC_VALUE, 2)


@pytest.fixture
def fxt_count_metric():
    yield CountMetric(name=DummyValues.COUNT_METRIC_NAME, value=DummyValues.COUNT_METRIC_VALUE)


@pytest.fixture
def fxt_count_metric_rest():
    yield DummyValues.COUNT_METRIC_VALUE


@pytest.fixture
def fxt_string_metric():
    yield StringMetric(name=DummyValues.STRING_METRIC_NAME, value=DummyValues.STRING_METRIC_VALUE)


@pytest.fixture
def fxt_string_metric_rest():
    yield DummyValues.STRING_METRIC_VALUE


@pytest.fixture
def fxt_null_metric_group(fxt_curve_metric):
    yield LineMetricsGroup(
        visualization_info=LineChartInfo(name=DummyValues.METRICS_GROUP_NAME, x_axis_label="x", y_axis_label="y"),
        metrics=[NullMetric()],
    )
