# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements REST mappers for Performance entities
"""

from typing import Any

from features.feature_flag_provider import FeatureFlag, FeatureFlagProvider

from iai_core.entities.metrics import AnomalyLocalizationPerformance, NullPerformance, Performance
from iai_core.entities.project_performance import (
    GlobalLocalTaskPerformance,
    ProjectPerformance,
    TaskPerformance,
    TaskPerformanceScore,
)

GLOBAL_SCORE = "global_score"
LOCAL_SCORE = "local_score"
METRIC_TYPE = "metric_type"
SCORE = "score"
TASK_ID = "task_id"
TASK_PERFORMANCES = "task_performances"
VALUE = "value"


class PerformanceRESTViews:
    """
    This class maps Performance and ProjectPerformance entities to their REST representation
    """

    @staticmethod
    def project_performance_to_rest(
        project_performance: ProjectPerformance,
    ) -> dict[str, Any]:
        """
        This method converts a ProjectPerformance to its REST representation
        """

        task_performances = [
            PerformanceRESTViews._task_performance_to_rest(task_performance)
            for task_performance in project_performance.task_performances.values()
        ]

        result = {
            SCORE: project_performance.score,
            TASK_PERFORMANCES: task_performances,
        }

        # TODO: CVS-118089
        # For backwards compatibility add global and local score values directly under
        # "performance" attribute for anomaly detection/segmentation projects. These type
        # of projects have only 1 task that has a global score in the task performance.
        if len(task_performances) == 1 and GLOBAL_SCORE in task_performances[0]:
            result[GLOBAL_SCORE] = task_performances[0][GLOBAL_SCORE][VALUE]
            result[LOCAL_SCORE] = (
                task_performances[0][LOCAL_SCORE][VALUE] if task_performances[0][LOCAL_SCORE] is not None else None
            )

        return result

    @staticmethod
    def _task_performance_to_rest(task_performance: TaskPerformance) -> dict[str, Any]:
        result = {
            TASK_ID: str(task_performance.task_node_id),
            SCORE: PerformanceRESTViews._task_performance_score_to_rest(task_performance.score),
        }

        is_anomaly_reduced = FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_ANOMALY_REDUCTION)
        if not is_anomaly_reduced and isinstance(task_performance, GlobalLocalTaskPerformance):
            result[GLOBAL_SCORE] = PerformanceRESTViews._task_performance_score_to_rest(task_performance.global_score)
            result[LOCAL_SCORE] = PerformanceRESTViews._task_performance_score_to_rest(task_performance.local_score)

        return result

    @staticmethod
    def _task_performance_score_to_rest(
        task_performance_score: TaskPerformanceScore | None,
    ) -> dict[str, Any] | None:
        if task_performance_score is None:
            return None
        return {
            VALUE: task_performance_score.value,
            METRIC_TYPE: task_performance_score.metric_type,
        }

    @staticmethod
    def performance_to_rest(performance: Performance) -> dict[str, Any]:
        """
        This method converts a Performance instance to its REST representation.
        """
        performance_dict: dict
        if isinstance(performance, AnomalyLocalizationPerformance):
            is_anomaly_reduced = FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_ANOMALY_REDUCTION)
            if is_anomaly_reduced:
                performance_dict = {SCORE: performance.global_score.value}
            else:
                local_score = performance.local_score.value if performance.local_score is not None else None
                performance_dict = {
                    LOCAL_SCORE: local_score,
                    GLOBAL_SCORE: performance.global_score.value,
                }
        elif isinstance(performance, NullPerformance):
            performance_dict = {SCORE: None}
        elif isinstance(performance, Performance):
            performance_dict = {SCORE: performance.score.value}
        else:
            raise NotImplementedError(f"Converting performance metrics '{performance}' to REST is not implemented.")
        return performance_dict
