#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

"""This module contains the MongoDB mapper for metrics related entities"""

from typing import Any, ClassVar

import numpy as np

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
from sc_sdk.repos.mappers.mongodb_mapper_interface import IMapperSimple
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from sc_sdk.repos.mappers.mongodb_mappers.primitive_mapper import NumpyToMongo


class MetricToMongo(IMapperSimple[MetricEntity, dict]):
    """MongoDB mapper for `Metric` entities"""

    @staticmethod
    def forward(instance: MetricEntity) -> dict:
        output: dict[str, Any]
        if isinstance(
            instance,
            ScoreMetric | CountMetric | DateMetric | StringMetric | NullScoreMetric,
        ):
            output = {
                "name": instance.name,
                "value": instance.value,
                "type": instance.type(),
            }
            if isinstance(instance, ScoreMetric):
                output["label_id"] = IDToMongo.forward(instance.label_id) if instance.label_id else None
        elif isinstance(instance, DurationMetric):
            output = {
                "name": instance.name,
                "hour": instance.hour,
                "minute": instance.minute,
                "second": instance.second,
            }
        elif isinstance(instance, CurveMetric):
            output = {
                "name": instance.name,
                "ys": [float(y) for y in instance.ys],
                "type": instance.type(),
            }
            if instance.xs is not None:
                output["xs"] = [float(x) for x in instance.xs]
        elif isinstance(instance, MatrixMetric):
            output = {
                "name": instance.name,
                "matrix_values": NumpyToMongo.forward(instance.matrix_values),
                "type": instance.type(),
            }
            if instance.row_labels is not None:
                output["row_labels"] = list(instance.row_labels)
            if instance.column_labels is not None:
                output["column_labels"] = list(instance.column_labels)
        else:
            output = {"name": "NullMetric()", "type": "null"}
        return output

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
                label_id=IDToMongo.backward(label_id) if label_id else None,
            )
        elif metric_type == NullScoreMetric.type():
            result = NullScoreMetric()
        elif metric_type == DurationMetric.type():
            result = DurationMetric(
                name=instance["name"], hour=instance["hour"], minute=instance["minute"], second=instance["second"]
            )
        elif metric_type == CurveMetric.type():
            result = CurveMetric(name=instance["name"], ys=instance["ys"], xs=instance.get("xs"))
        elif metric_type == MatrixMetric.type():
            result = MatrixMetric(
                name=instance["name"],
                matrix_values=NumpyToMongo.backward(instance["matrix_values"]),
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


class VisualizationInfoToMongo(IMapperSimple[VisualizationInfo, dict]):
    """MongoDB mapper for `VisualizationInfo` entities"""

    @staticmethod
    def forward(instance: VisualizationInfo) -> dict:
        output = {
            "name": instance.name,
            "type": instance.type.name,
            "palette": instance.palette.name,
        }
        if isinstance(instance, LineChartInfo):
            output["x_axis_label"] = instance.x_axis_label
            output["y_axis_label"] = instance.y_axis_label
        elif isinstance(instance, MatrixChartInfo):
            output["header"] = instance.header
            output["row_header"] = instance.row_header
            output["column_header"] = instance.column_header
        return output

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
            output = BarChartInfo(  # type: ignore
                name=instance["name"],
                palette=ColorPalette[instance.get("palette", "LABEL")],
                visualization_type=VisualizationType[instance["type"]],
            )
        elif instance["type"] == VisualizationType.LINE.name:
            output = LineChartInfo(  # type: ignore
                name=instance["name"],
                x_axis_label=instance.get("x_axis_label"),
                y_axis_label=instance.get("y_axis_label"),
                palette=ColorPalette[instance.get("palette", "LABEL")],
            )
        elif instance["type"] == VisualizationType.MATRIX.name:
            output = MatrixChartInfo(  # type: ignore
                name=instance["name"],
                header=instance.get("header"),
                row_header=instance.get("row_header"),
                column_header=instance.get("column_header"),
                palette=ColorPalette[instance.get("palette", "LABEL")],
            )
        else:
            raise ValueError(f"Visualization type {instance['type']} is currently not implemented.")
        return output


class MetricsGroupToMongo(IMapperSimple[MetricsGroup, dict]):
    """MongoDB mapper for `MetricsGroup` entities"""

    @staticmethod
    def forward(instance: MetricsGroup) -> dict:
        return {
            "visualization_info": VisualizationInfoToMongo.forward(instance.visualization_info),
            "metrics": [MetricToMongo.forward(metric) for metric in instance.metrics],
        }

    @staticmethod
    def backward(instance: dict) -> MetricsGroup:
        visualization_info = VisualizationInfoToMongo.backward(instance.get("visualization_info", {}))
        metrics = [MetricToMongo.backward(metric) for metric in instance["metrics"]]
        if visualization_info.type == VisualizationType.TEXT:
            metrics_group = TextMetricsGroup(metrics, visualization_info)  # type: ignore
        elif visualization_info.type in (
            VisualizationType.BAR,
            VisualizationType.RADIAL_BAR,
        ):
            metrics_group = BarMetricsGroup(metrics, visualization_info)  # type: ignore
        elif visualization_info.type == VisualizationType.LINE:
            metrics_group = LineMetricsGroup(metrics, visualization_info)  # type: ignore
        elif visualization_info.type == VisualizationType.MATRIX:
            metrics_group = MatrixMetricsGroup(metrics, visualization_info)  # type: ignore
        else:
            raise ValueError(f"Visualization type {visualization_info.type} is currently not implemented.")
        return metrics_group


class PerformanceToMongo(IMapperSimple[Performance, dict]):
    """MongoDB mapper for`Performance` entities"""

    ANOMALY_PERFORMANCE_TYPE: ClassVar[str] = "AnomalyLocalizationPerformance"
    MULTI_SCORE_PERFORMANCE_TYPE: ClassVar[str] = "MultiScorePerformance"
    PERFORMANCE_TYPE: ClassVar[str] = "Performance"

    @staticmethod
    def forward(instance: Performance) -> dict:
        if instance is None or isinstance(instance, NullPerformance):
            return {}
        score: dict[str, Any]
        if isinstance(instance, AnomalyLocalizationPerformance):
            score = {
                "local_score": MetricToMongo.forward(instance.local_score),  # type: ignore
                "global_score": MetricToMongo.forward(instance.global_score),
            }
            performance_type = PerformanceToMongo.ANOMALY_PERFORMANCE_TYPE
        elif isinstance(instance, MultiScorePerformance):
            score = {
                "primary_score": MetricToMongo.forward(instance.primary_score),
                "additional_scores": [
                    MetricToMongo.forward(additional_score) for additional_score in instance.additional_scores
                ],
            }
            performance_type = PerformanceToMongo.MULTI_SCORE_PERFORMANCE_TYPE
        elif isinstance(instance, Performance):
            score = MetricToMongo.forward(instance.score)
            performance_type = PerformanceToMongo.PERFORMANCE_TYPE
        else:
            raise NotImplementedError(f"MongoMapper for Performance of type {type(instance)} is not implemented.")

        return {
            "score": score,
            "dashboard_metrics": [
                MetricsGroupToMongo.forward(metrics_group) for metrics_group in instance.dashboard_metrics
            ],
            "type": performance_type,
        }

    @staticmethod
    def backward(instance: dict) -> Performance:
        if instance is None or len(instance) == 0:
            return NullPerformance()

        performance_type = instance.get("type", PerformanceToMongo.PERFORMANCE_TYPE)
        score = instance["score"]
        if performance_type == PerformanceToMongo.ANOMALY_PERFORMANCE_TYPE:
            output_type = AnomalyLocalizationPerformance
            score_arguments = {
                "local_score": MetricToMongo.backward(score["local_score"]),
                "global_score": MetricToMongo.backward(score["global_score"]),
            }
        elif performance_type == PerformanceToMongo.MULTI_SCORE_PERFORMANCE_TYPE:
            output_type = MultiScorePerformance  # type: ignore
            score_arguments = {
                "primary_score": MetricToMongo.backward(score["primary_score"]),
                "additional_scores": [  # type: ignore
                    MetricToMongo.backward(additional_score) for additional_score in score["additional_scores"]
                ],
            }
        else:
            output_type = Performance  # type: ignore
            score_arguments = {"score": MetricToMongo.backward(instance["score"])}

        # Validate that all score metrics are ScoreMetric instances. In the case of a
        # NullMetric, convert to a ScoreMetric with a zero score
        for score_name, score_metric in score_arguments.items():
            if isinstance(score_metric, list):
                score_entries: list[ScoreMetric] = []
                for score_entry in score_metric:
                    score_entries.append(PerformanceToMongo._validate_score_metric(score_entry))  # type: ignore
                score_arguments[score_name] = score_entries  # type: ignore
            else:
                score_arguments[score_name] = PerformanceToMongo._validate_score_metric(  # type: ignore
                    score_metric,  # type: ignore
                    allow_optional=score_name == "local_score",  # type: ignore
                )

        return output_type(
            **score_arguments,  # type: ignore
            dashboard_metrics=[
                MetricsGroupToMongo.backward(metric_group) for metric_group in instance["dashboard_metrics"]
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
            score_metric = None if allow_optional else ScoreMetric(name="Null score", value=0)  # type: ignore
        elif not isinstance(score_metric, ScoreMetric):
            raise ValueError(f"Expected ScoreMetric for Performance.score, but got {score_metric.type()} instead.")
        return score_metric  # type: ignore
