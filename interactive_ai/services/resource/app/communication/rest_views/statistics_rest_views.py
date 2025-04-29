# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import datetime
import logging

import numpy as np

from geti_telemetry_tools import unified_tracing
from sc_sdk.entities.label import Label
from sc_sdk.entities.metrics import (
    BarMetricsGroup,
    ColorPalette,
    CountMetric,
    CurveMetric,
    DateMetric,
    DurationMetric,
    LineMetricsGroup,
    MatrixMetric,
    MatrixMetricsGroup,
    MetricsGroup,
    NullMetric,
    ScoreMetric,
    StringMetric,
    TextMetricsGroup,
)

logger = logging.getLogger(__name__)


class StatisticsRESTViews:
    @staticmethod
    @unified_tracing
    def metrics_groups_to_rest(metrics_groups: list[MetricsGroup], labels: list[Label]) -> list[dict]:
        """
        For a list of MetricsGroup, checks the type of each metrics group and calls
        the correct to_rest function. Currently, text, line, matrix and bar charts are
        allowed.
        """
        metrics_groups_rest = []
        for metrics_group in metrics_groups:
            if NullMetric() in metrics_group.metrics:
                continue
            if isinstance(metrics_group, TextMetricsGroup):
                metrics_groups_rest.append(StatisticsRESTViews.text_chart_metrics_group_to_rest(metrics_group))
            elif isinstance(metrics_group, LineMetricsGroup):
                metrics_groups_rest.append(
                    StatisticsRESTViews.line_chart_metrics_group_to_rest(metrics_group=metrics_group, labels=labels)
                )
            elif isinstance(metrics_group, MatrixMetricsGroup):
                metrics_groups_rest.append(StatisticsRESTViews.matrix_chart_metrics_group_to_rest(metrics_group))
            elif isinstance(metrics_group, BarMetricsGroup):
                metrics_groups_rest.append(
                    StatisticsRESTViews.bar_chart_metrics_group_to_rest(metrics_group=metrics_group, labels=labels)
                )
            else:  # pragma: no cover
                raise ValueError(
                    f"Metric of instance {type(metrics_group)} is not suppported in metrics_groups_to_rest"
                )
        return metrics_groups_rest

    @staticmethod
    def text_chart_metrics_group_to_rest(metrics_group: TextMetricsGroup) -> dict:
        metric = metrics_group.metrics[0]
        value: str | float | int
        if isinstance(metric, DurationMetric):
            value = StatisticsRESTViews.duration_metric_to_rest(metric)
        elif isinstance(metric, DateMetric):
            value = StatisticsRESTViews.date_metric_to_rest(metric)
        elif isinstance(metric, ScoreMetric):
            value = StatisticsRESTViews.score_metric_to_rest(metric)
        elif isinstance(metric, CountMetric):
            value = StatisticsRESTViews.count_metric_to_rest(metric)
        else:
            value = StatisticsRESTViews.string_metric_to_rest(metric)
        return {
            "header": metrics_group.visualization_info.name,
            "type": metrics_group.visualization_info.type.name.lower(),
            "key": metrics_group.visualization_info.name,
            "value": value,
        }

    @staticmethod
    def bar_chart_metrics_group_to_rest(metrics_group: BarMetricsGroup, labels: list[Label]) -> dict:
        metric_values_rest = []
        for metric in metrics_group.metrics:
            if isinstance(metric, ScoreMetric):
                metric_value = StatisticsRESTViews.score_metric_to_rest(metric)
            elif isinstance(metric, CountMetric):
                metric_value = StatisticsRESTViews.count_metric_to_rest(metric)
            else:
                raise NotImplementedError("Bar chart only has a rest view for ScoreMetric or CountMetric")
            metric_rest = {
                "header": metric.name,
                "key": metric.name,
                "value": metric_value,
                "color": (
                    next(
                        (label.color.hex_str for label in labels if label.name == metric.name),
                        None,
                    )
                    if metrics_group.visualization_info.palette == ColorPalette.LABEL
                    else None
                ),
            }
            metric_values_rest.append(metric_rest)
        return {
            "header": metrics_group.visualization_info.name,
            "type": metrics_group.visualization_info.type.name.lower(),
            "key": metrics_group.visualization_info.name,
            "value": metric_values_rest,
        }

    @staticmethod
    def line_chart_metrics_group_to_rest(metrics_group: LineMetricsGroup, labels: list[Label]) -> dict:
        return {
            "header": metrics_group.visualization_info.name,
            "type": metrics_group.visualization_info.type.name.lower(),
            "key": metrics_group.visualization_info.name,
            "value": {
                "x_axis_label": metrics_group.visualization_info.x_axis_label,
                "y_axis_label": metrics_group.visualization_info.y_axis_label,
                "line_data": [
                    StatisticsRESTViews.curve_metric_to_rest(
                        metric=metric,
                        labels=labels,
                        per_label=metrics_group.visualization_info.palette == ColorPalette.LABEL,
                    )
                    for metric in metrics_group.metrics
                ],
            },
        }

    @staticmethod
    def matrix_chart_metrics_group_to_rest(
        metrics_group: MatrixMetricsGroup,
    ) -> dict:
        return {
            "header": metrics_group.visualization_info.name,
            "type": metrics_group.visualization_info.type.name.lower(),
            "key": metrics_group.visualization_info.name,
            "value": {
                "row_header": metrics_group.visualization_info.row_header,
                "column_header": metrics_group.visualization_info.column_header,
                "matrix_data": [StatisticsRESTViews.matrix_metric_to_rest(metric) for metric in metrics_group.metrics],
            },
        }

    @staticmethod
    def duration_metric_to_rest(metric: DurationMetric) -> str:
        """
        Returns the string representation of the duration.
        :example: Duration string of 1 hour 2 minute and 3 seconds returns '1:02:03'
        """
        return str(datetime.timedelta(hours=metric.hour, minutes=metric.minute, seconds=round(metric.second)))

    @staticmethod
    def date_metric_to_rest(metric: DateMetric) -> str:
        return metric.date.isoformat()

    @staticmethod
    def score_metric_to_rest(metric: ScoreMetric) -> float:
        return round(metric.value, 2)

    @staticmethod
    def count_metric_to_rest(metric: CountMetric) -> int:
        return metric.value

    @staticmethod
    def string_metric_to_rest(metric: StringMetric) -> str:
        return metric.value

    @staticmethod
    def curve_metric_to_rest(metric: CurveMetric, labels: list[Label], per_label: bool) -> dict:
        ys = np.asarray(metric.ys)
        if np.isnan(np.sum(ys)):
            logger.warning(f"A NaN value was detected in {metric.name}. Setting all NaN values to 0.0")
            ys[np.isnan(ys)] = 0.0
        return {
            "header": metric.name,
            "key": metric.name,
            "points": [{"x": x, "y": y, "type": "point"} for x, y in zip(metric.xs, ys)],
            "color": (
                next(
                    (label.color.hex_str for label in labels if label.name == metric.name),
                    None,
                )
                if per_label
                else None
            ),
        }

    @staticmethod
    def matrix_metric_to_rest(metric: MatrixMetric) -> dict:
        return {
            "header": metric.name,
            "key": metric.name,
            "row_names": metric.row_labels,
            "column_names": metric.column_labels,
            "matrix_values": metric.matrix_values.tolist(),
        }
