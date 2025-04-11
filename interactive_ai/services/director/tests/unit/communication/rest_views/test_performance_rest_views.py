# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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

from communication.views.performance_rest_views import PerformanceRESTViews
from features.feature_flag_provider import FeatureFlag

from sc_sdk.entities.project_performance import (
    GlobalLocalTaskPerformance,
    ProjectPerformance,
    TaskPerformance,
    TaskPerformanceScore,
)


@pytest.fixture()
def fxt_task_performance_normal(fxt_mongo_id) -> TaskPerformance:
    return TaskPerformance(
        task_node_id=fxt_mongo_id(0),
        score=TaskPerformanceScore(value=0.5, metric_type="f-measure"),
    )


@pytest.fixture()
def fxt_task_performance_global(fxt_mongo_id) -> GlobalLocalTaskPerformance:
    return GlobalLocalTaskPerformance(
        task_node_id=fxt_mongo_id(1),
        global_score=TaskPerformanceScore(value=0.9, metric_type="accuracy"),
        local_score=TaskPerformanceScore(value=0.2, metric_type="dice_average"),
    )


class TestPerformanceRESTViews:
    def test_performance_to_rest_chain(
        self,
        fxt_task_performance_normal,
        fxt_task_performance_global,
    ) -> None:
        # Arrange
        project_performance = ProjectPerformance(
            task_performances=[
                fxt_task_performance_normal,
                fxt_task_performance_global,
            ],
            score=0.4,
        )
        expected_result = {
            "score": 0.4,
            "task_performances": [
                {
                    "task_id": "60d31793d5f1fb7e6e3c1a4f",
                    "score": {
                        "value": 0.5,
                        "metric_type": "f-measure",
                    },
                },
                {
                    "task_id": "60d31793d5f1fb7e6e3c1a50",
                    "score": {
                        "value": 0.9,
                        "metric_type": "accuracy",
                    },
                    "global_score": {
                        "value": 0.9,
                        "metric_type": "accuracy",
                    },
                    "local_score": {
                        "value": 0.2,
                        "metric_type": "dice_average",
                    },
                },
            ],
        }

        # Act
        result = PerformanceRESTViews.project_performance_to_rest(project_performance=project_performance)

        # Assert
        assert result == expected_result

    def test_performance_to_rest_global(
        self,
        fxt_task_performance_global,
    ) -> None:
        # Arrange
        project_performance = ProjectPerformance(task_performances=[fxt_task_performance_global], score=0.9)
        expected_result = {
            "score": 0.9,
            "global_score": 0.9,
            "local_score": 0.2,
            "task_performances": [
                {
                    "task_id": "60d31793d5f1fb7e6e3c1a50",
                    "score": {
                        "value": 0.9,
                        "metric_type": "accuracy",
                    },
                    "global_score": {
                        "value": 0.9,
                        "metric_type": "accuracy",
                    },
                    "local_score": {
                        "value": 0.2,
                        "metric_type": "dice_average",
                    },
                },
            ],
        }

        # Act
        result = PerformanceRESTViews.project_performance_to_rest(project_performance=project_performance)

        # Assert
        assert result == expected_result

    def test_performance_to_rest_global_reduced_anomaly(
        self,
        fxt_task_performance_global,
        fxt_enable_feature_flag_name,
    ) -> None:
        fxt_enable_feature_flag_name(FeatureFlag.FEATURE_FLAG_ANOMALY_REDUCTION.name)
        # Arrange
        project_performance = ProjectPerformance(task_performances=[fxt_task_performance_global], score=0.9)
        expected_result = {
            "score": 0.9,
            "task_performances": [
                {
                    "task_id": "60d31793d5f1fb7e6e3c1a50",
                    "score": {
                        "value": 0.9,
                        "metric_type": "accuracy",
                    },
                },
            ],
        }

        # Act
        result = PerformanceRESTViews.project_performance_to_rest(project_performance=project_performance)

        # Assert
        assert result == expected_result
