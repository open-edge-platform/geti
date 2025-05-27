# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


import pytest

from communication.views.performance_rest_views import PerformanceRESTViews

from iai_core.entities.project_performance import (
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
