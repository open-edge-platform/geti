#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

"""This module contains the deserializer for metrics related entities"""

from typing import ClassVar

import numpy as np
from geti_types import ID
from iai_core.entities.metrics import (
    AnomalyLocalizationPerformance,
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
    MetricEntity,
    MetricsGroup,
    MultiScorePerformance,
    NullMetric,
    NullPerformance,
    NullScoreMetric,
    Performance,
    ScoreMetric,
    StringMetric,
    TextChartInfo,
    TextMetricsGroup,
    VisualizationInfo,
    VisualizationType,
)


class NumpyDeserializer:
    """Deserializer for `np.ndarray`"""

    @staticmethod
    def backward(instance: dict) -> np.ndarray:
        array_values = np.asarray(instance["array_values"])
        array_shape = instance["array_shape"]
        return array_values.reshape(array_shape)


class MetricDeserializer:
    """Deserializer for `Metric` entities"""

    @staticmethod
    def backward(
        instance: dict,
    ) -> MetricEntity:
        metric_type = instance["type"]
        result: MetricEntity = NullMetric()
        if metric_type == ScoreMetric.type():
            label_id = instance.get("label_id")
            result = ScoreMetric(
                name=instance["name"],
                value=float(np.nan_to_num(instance["value"])),
                label_id=ID(label_id) if label_id else None,
            )
        elif metric_type == NullScoreMetric.type():
            result = NullScoreMetric()
        elif metric_type == DurationMetric.type():
            result = DurationMetric(
                name=instance["name"],
                hour=instance["hour"],
                minute=instance["minute"],
                second=instance["second"],
            )
        elif metric_type == CurveMetric.type():
            result = CurveMetric(name=instance["name"], ys=instance["ys"], xs=instance.get("xs"))
        elif metric_type == MatrixMetric.type():
            result = MatrixMetric(
                name=instance["name"],
                matrix_values=NumpyDeserializer.backward(instance["matrix_values"]),
                row_labels=instance.get("row_labels"),
                column_labels=instance.get("column_labels"),
            )
        else:
            for metric_class in (
                CountMetric,
                StringMetric,
                DateMetric,
            ):
                if metric_type == metric_class.type():
                    value = instance["value"]
                    if isinstance(value, float):
                        value = np.nan_to_num(value)
                    result = metric_class(name=instance["name"], value=value)
        return result


class VisualizationInfoDeserializer:
    """Deserializer for `VisualizationInfo` entities"""

    @staticmethod
    def backward(
        instance: dict,
    ) -> TextChartInfo | BarChartInfo | LineChartInfo | MatrixChartInfo:
        if instance is None:
            return VisualizationInfo(name="Placeholder", visualisation_type=VisualizationType.TEXT)
        if instance["type"] == VisualizationType.TEXT.name:
            return TextChartInfo(
                name=instance["name"],
            )
        if instance["type"] in (
            VisualizationType.BAR.name,
            VisualizationType.RADIAL_BAR.name,
        ):
            return BarChartInfo(
                name=instance["name"],
                palette=ColorPalette[instance.get("palette", "LABEL")],
                visualization_type=VisualizationType[instance["type"]],
            )
        if instance["type"] == VisualizationType.LINE.name:
            return LineChartInfo(
                name=instance["name"],
                x_axis_label=instance.get("x_axis_label"),
                y_axis_label=instance.get("y_axis_label"),
                palette=ColorPalette[instance.get("palette", "LABEL")],
            )
        if instance["type"] == VisualizationType.MATRIX.name:
            return MatrixChartInfo(
                name=instance["name"],
                header=instance.get("header"),
                row_header=instance.get("row_header"),
                column_header=instance.get("column_header"),
                palette=ColorPalette[instance.get("palette", "LABEL")],
            )

        raise ValueError(f"Visualization type {instance['type']} is currently not implemented.")


class MetricsGroupDeserializer:
    """Deserializer for `MetricsGroup` entities"""

    @staticmethod
    def backward(instance: dict) -> MetricsGroup:
        visualization_info = VisualizationInfoDeserializer.backward(instance.get("visualization_info", {}))
        metrics = [MetricDeserializer.backward(metric) for metric in instance["metrics"]]
        if isinstance(visualization_info, TextChartInfo):
            return MetricsGroupDeserializer.backward_text_metrics(metrics, visualization_info)
        if isinstance(visualization_info, BarChartInfo):
            return MetricsGroupDeserializer.backward_bar_metrics(metrics, visualization_info)
        if isinstance(visualization_info, LineChartInfo):
            return MetricsGroupDeserializer.backward_line_metrics(metrics, visualization_info)
        if isinstance(visualization_info, MatrixChartInfo):
            return MetricsGroupDeserializer.backward_matrix_metrics(metrics, visualization_info)

        raise ValueError(f"Visualization type {visualization_info.type} is currently not implemented.")

    @staticmethod
    def backward_text_metrics(metrics: list[MetricEntity], visualization_info: TextChartInfo) -> TextMetricsGroup:
        filtered_metrics = []
        for metric in metrics:
            if isinstance(
                metric,
                ScoreMetric | CountMetric | StringMetric | DateMetric | DurationMetric,
            ):
                filtered_metrics.append(metric)
            else:
                raise ValueError(f"Metric type {type(metric)} is not supported for text visualization.")
        return TextMetricsGroup(filtered_metrics, visualization_info)

    @staticmethod
    def backward_bar_metrics(metrics: list[MetricEntity], visualization_info: BarChartInfo) -> BarMetricsGroup:
        filtered_metrics = []
        for metric in metrics:
            if isinstance(metric, ScoreMetric | CountMetric):
                filtered_metrics.append(metric)
            else:
                raise ValueError(f"Metric type {type(metric)} is not supported for bar visualization.")
        return BarMetricsGroup(filtered_metrics, visualization_info)

    @staticmethod
    def backward_line_metrics(metrics: list[MetricEntity], visualization_info: LineChartInfo) -> LineMetricsGroup:
        filtered_metrics = []
        for metric in metrics:
            if isinstance(metric, CurveMetric):
                filtered_metrics.append(metric)
            else:
                raise ValueError(f"Metric type {type(metric)} is not supported for line visualization.")
        return LineMetricsGroup(filtered_metrics, visualization_info)

    @staticmethod
    def backward_matrix_metrics(metrics: list[MetricEntity], visualization_info: MatrixChartInfo) -> MatrixMetricsGroup:
        filtered_metrics = []
        for metric in metrics:
            if isinstance(metric, MatrixMetric):
                filtered_metrics.append(metric)
            else:
                raise ValueError(f"Metric type {type(metric)} is not supported for matrix visualization.")
        return MatrixMetricsGroup(filtered_metrics, visualization_info)


class PerformanceDeserializer:
    """Deserializer for`Performance` entities"""

    ANOMALY_PERFORMANCE_TYPE: ClassVar[str] = "AnomalyLocalizationPerformance"
    MULTI_SCORE_PERFORMANCE_TYPE: ClassVar[str] = "MultiScorePerformance"
    PERFORMANCE_TYPE: ClassVar[str] = "Performance"

    @staticmethod
    def backward(instance: dict) -> Performance:
        if instance is None or len(instance) == 0:
            return NullPerformance()

        performance_type = instance.get("type", PerformanceDeserializer.PERFORMANCE_TYPE)
        score = instance["score"]
        if performance_type == PerformanceDeserializer.ANOMALY_PERFORMANCE_TYPE:
            return PerformanceDeserializer.backward_anomaly_performance(instance, score)
        if performance_type == PerformanceDeserializer.MULTI_SCORE_PERFORMANCE_TYPE:
            return PerformanceDeserializer.backward_multi_score_performance(instance, score)

        return PerformanceDeserializer.backward_score(instance, score)

    @staticmethod
    def backward_score(instance: dict, score: dict) -> Performance:
        return Performance(
            score=PerformanceDeserializer._validate_score_metric(MetricDeserializer.backward(score)),
            dashboard_metrics=[
                MetricsGroupDeserializer.backward(metric_group) for metric_group in instance["dashboard_metrics"]
            ],
        )

    @staticmethod
    def backward_multi_score_performance(instance: dict, score: dict) -> Performance:
        return MultiScorePerformance(
            primary_score=PerformanceDeserializer._validate_score_metric(
                MetricDeserializer.backward(score["primary_score"])
            ),
            additional_scores=[
                PerformanceDeserializer._validate_score_metric(MetricDeserializer.backward(additional_score))
                for additional_score in score["additional_scores"]
            ],
            dashboard_metrics=[
                MetricsGroupDeserializer.backward(metric_group) for metric_group in instance["dashboard_metrics"]
            ],
        )

    @staticmethod
    def backward_anomaly_performance(instance: dict, score: dict) -> Performance:
        return AnomalyLocalizationPerformance(
            local_score=PerformanceDeserializer._validate_optional_score_metric(
                MetricDeserializer.backward(score["local_score"])
            ),
            global_score=PerformanceDeserializer._validate_score_metric(
                MetricDeserializer.backward(score["global_score"])
            ),
            dashboard_metrics=[
                MetricsGroupDeserializer.backward(metric_group) for metric_group in instance["dashboard_metrics"]
            ],
        )

    @staticmethod
    def _validate_score_metric(score_metric: MetricEntity) -> ScoreMetric:
        """
        Validate that a metric passed as a model or project score is of the correct
        type, and convert to a dummy score if not.

        :param score_metric: Metric to validate
        :raises ValueError: if the metric is not a ScoreMetric and cannot be converted
            to one
        :return: The validated score metric
        """
        if isinstance(score_metric, NullMetric):
            return ScoreMetric(name="Null score", value=0)
        if not isinstance(score_metric, ScoreMetric):
            raise ValueError(f"Expected ScoreMetric for Performance.score, but got {score_metric.type()} instead.")
        return score_metric

    @staticmethod
    def _validate_optional_score_metric(
        score_metric: MetricEntity,
    ) -> ScoreMetric | None:
        """
        Validate that a metric passed as a model or project score is of the correct
        type, and convert to a dummy score if not.

        :param score_metric: Metric to validate
        :raises ValueError: if the metric is not a ScoreMetric and cannot be converted
            to one
        :return: ScoreMetric. If a NullMetric is passed this method returns None
        """
        if isinstance(score_metric, NullMetric):
            return None

        return PerformanceDeserializer._validate_score_metric(score_metric)
