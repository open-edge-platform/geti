#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

"""This module contains the deserializer for metrics related entities"""

from typing import ClassVar

import numpy as np
from geti_types import ID
from sc_sdk.entities.metrics import (
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
    ) -> (
        ScoreMetric | CountMetric | StringMetric | DateMetric | DurationMetric | CurveMetric | MatrixMetric | NullMetric
    ):
        metric_type = instance["type"]
        if metric_type == ScoreMetric.type():
            label_id = instance.get("label_id")
            return ScoreMetric(
                name=instance["name"],
                value=float(np.nan_to_num(instance["value"])),
                label_id=ID(label_id) if label_id else None,
            )
        if metric_type == NullScoreMetric.type():
            return NullScoreMetric()
        for metric_class in (
            CountMetric,
            StringMetric,
            DateMetric,
            DurationMetric,
        ):
            if metric_type == metric_class.type():
                value = instance["value"]
                if isinstance(value, float):
                    value = np.nan_to_num(value)
                return metric_class(name=instance["name"], value=value)
        if metric_type == CurveMetric.type():
            return CurveMetric(name=instance["name"], ys=instance["ys"], xs=instance.get("xs"))
        if metric_type == MatrixMetric.type():
            return MatrixMetric(
                name=instance["name"],
                matrix_values=NumpyDeserializer.backward(instance["matrix_values"]),
                row_labels=instance.get("row_labels"),
                column_labels=instance.get("column_labels"),
            )
        return NullMetric()


class VisualizationInfoDeserializer:
    """Deserializer for `VisualizationInfo` entities"""

    @staticmethod
    def backward(
        instance: dict,
    ) -> TextChartInfo | BarChartInfo | LineChartInfo | MatrixChartInfo:
        if instance is None:
            output = VisualizationInfo(name="Placeholder", visualisation_type=VisualizationType.TEXT)
        if instance["type"] == VisualizationType.TEXT.name:
            output = TextChartInfo(
                name=instance["name"],
            )
        elif instance["type"] in (
            VisualizationType.BAR.name,
            VisualizationType.RADIAL_BAR.name,
        ):
            output = BarChartInfo(
                name=instance["name"],
                palette=ColorPalette[instance.get("palette", "LABEL")],
                visualization_type=VisualizationType[instance["type"]],
            )
        elif instance["type"] == VisualizationType.LINE.name:
            output = LineChartInfo(
                name=instance["name"],
                x_axis_label=instance.get("x_axis_label"),
                y_axis_label=instance.get("y_axis_label"),
                palette=ColorPalette[instance.get("palette", "LABEL")],
            )
        elif instance["type"] == VisualizationType.MATRIX.name:
            output = MatrixChartInfo(
                name=instance["name"],
                header=instance.get("header"),
                row_header=instance.get("row_header"),
                column_header=instance.get("column_header"),
                palette=ColorPalette[instance.get("palette", "LABEL")],
            )
        else:
            raise ValueError(f"Visualization type {instance['type']} is currently not implemented.")
        return output


class MetricsGroupDeserializer:
    """Deserializer for `MetricsGroup` entities"""

    @staticmethod
    def backward(instance: dict) -> MetricsGroup:
        visualization_info = VisualizationInfoDeserializer.backward(instance.get("visualization_info", {}))
        metrics = [MetricDeserializer.backward(metric) for metric in instance["metrics"]]
        if visualization_info.type == VisualizationType.TEXT:
            metrics_group = TextMetricsGroup(metrics, visualization_info)
        elif visualization_info.type in (
            VisualizationType.BAR,
            VisualizationType.RADIAL_BAR,
        ):
            metrics_group = BarMetricsGroup(metrics, visualization_info)
        elif visualization_info.type == VisualizationType.LINE:
            metrics_group = LineMetricsGroup(metrics, visualization_info)
        elif visualization_info.type == VisualizationType.MATRIX:
            metrics_group = MatrixMetricsGroup(metrics, visualization_info)
        else:
            raise ValueError(f"Visualization type {visualization_info.type} is currently not implemented.")
        return metrics_group


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
            output_type = AnomalyLocalizationPerformance
            score_arguments = {
                "local_score": MetricDeserializer.backward(score["local_score"]),
                "global_score": MetricDeserializer.backward(score["global_score"]),
            }
        elif performance_type == PerformanceDeserializer.MULTI_SCORE_PERFORMANCE_TYPE:
            output_type = MultiScorePerformance
            score_arguments = {
                "primary_score": MetricDeserializer.backward(score["primary_score"]),
                "additional_scores": [
                    MetricDeserializer.backward(additional_score) for additional_score in score["additional_scores"]
                ],
            }
        else:
            output_type = Performance
            score_arguments = {"score": MetricDeserializer.backward(instance["score"])}

        # Validate that all score metrics are ScoreMetric instances. In the case of a
        # NullMetric, convert to a ScoreMetric with a zero score
        for score_name, score_metric in score_arguments.items():
            if isinstance(score_metric, list):
                score_entries: list[ScoreMetric] = []
                for score_entry in score_metric:
                    score_entries.append(PerformanceDeserializer._validate_score_metric(score_entry))
                score_arguments[score_name] = score_entries
            else:
                score_arguments[score_name] = PerformanceDeserializer._validate_score_metric(
                    score_metric, allow_optional=score_name == "local_score"
                )

        return output_type(
            **score_arguments,
            dashboard_metrics=[
                MetricsGroupDeserializer.backward(metric_group) for metric_group in instance["dashboard_metrics"]
            ],
        )

    @staticmethod
    def _validate_score_metric(
        score_metric: ScoreMetric | NullMetric, allow_optional: bool = False
    ) -> ScoreMetric | None:
        """
        Validate that a metric passed as a model or project score is of the correct
        type, and convert to the proper type otherwise

        :param score_metric: Metric to validate
        :raises ValueError: if the metric is not a ScoreMetric and cannot be converted
            to one
        :return: ScoreMetric. If a NullMetric is passed and 'allow_optional' is set to
            True, this method returns None
        """
        if isinstance(score_metric, NullMetric):
            score_metric = None if allow_optional else ScoreMetric(name="Null score", value=0)
        elif not isinstance(score_metric, ScoreMetric):
            raise ValueError(f"Expected ScoreMetric for Performance.score, but got {score_metric.type()} instead.")
        return score_metric
