# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import patch

from usecases.update_project_performance_usecase import UpdateProjectPerformanceUseCase

from iai_core.entities.evaluation_result import EvaluationPurpose
from iai_core.entities.project_performance import (
    GlobalLocalTaskPerformance,
    ProjectPerformance,
    TaskPerformance,
    TaskPerformanceScore,
)
from iai_core.repos import EvaluationResultRepo, ProjectRepo


@patch(
    "iai_core.repos.project_repo.ProjectRepo.__init__",
    return_value=None,
)
@patch(
    "iai_core.repos.evaluation_result_repo.EvaluationResultRepo.__init__",
    return_value=None,
)
class TestUpdateProjectPerformanceUseCase:
    def test_update_project_performance_anomaly(
        self,
        patched_project_repo,
        patched_evaluation_result_repo,
        fxt_project,
        fxt_optimized_model,
        fxt_anomaly_performance,
    ) -> None:
        # Arrange
        task_node_id = fxt_project.get_trainable_task_nodes()[0].id_
        task_performance = fxt_project.performance.task_performances[task_node_id]
        assert not isinstance(task_performance, GlobalLocalTaskPerformance)
        assert task_performance.task_node_id == task_node_id
        assert task_performance.score is None
        assert fxt_project.performance.score is None

        with (
            patch.object(
                ProjectRepo,
                "get_by_id",
                return_value=fxt_project,
            ) as mock_get_project,
            patch.object(ProjectRepo, "update_project_performance", return_value=None) as mock_update_performance,
            patch.object(
                EvaluationResultRepo,
                "get_performance_by_model_ids",
                return_value=fxt_anomaly_performance,
            ) as mock_get_model_performance,
        ):
            # Act
            UpdateProjectPerformanceUseCase.update_project_performance(
                project_id=fxt_project.id_,
                task_node_id=task_node_id,
                inference_model_id=fxt_optimized_model.id_,
            )

        # Assert
        task_performance = fxt_project.performance.task_performances[task_node_id]
        assert isinstance(task_performance, GlobalLocalTaskPerformance)
        assert task_performance.task_node_id == task_node_id
        assert task_performance.score == TaskPerformanceScore(value=0.75, metric_type="F1 score")
        assert task_performance.global_score == TaskPerformanceScore(value=0.75, metric_type="F1 score")
        assert task_performance.local_score == TaskPerformanceScore(value=0.5, metric_type="Dice coefficient")
        assert fxt_project.performance.score == 0.75
        mock_get_project.assert_called_once_with(fxt_project.id_)
        mock_get_model_performance.assert_called_once_with(
            equivalent_model_ids=[fxt_optimized_model.id_],
            purpose=EvaluationPurpose.TEST,
        )
        mock_update_performance.assert_called_once()

    def test_update_project_performance_task_chain(
        self,
        patched_project_repo,
        patched_evaluation_result_repo,
        fxt_detection_segmentation_chain_project,
        fxt_optimized_model,
        fxt_performance,
    ) -> None:
        # Arrange
        project = fxt_detection_segmentation_chain_project
        task_node_id_1 = project.get_trainable_task_nodes()[0].id_
        task_node_id_2 = project.get_trainable_task_nodes()[1].id_
        project._performance = ProjectPerformance(
            score=0.2,
            task_performances=[
                TaskPerformance(
                    task_node_id=task_node_id_1,
                    score=TaskPerformanceScore(value=0.3, metric_type="f-measure"),
                ),
                GlobalLocalTaskPerformance(
                    task_node_id=task_node_id_2,
                    global_score=TaskPerformanceScore(
                        value=0.1,
                        metric_type="f-measure",
                    ),
                    local_score=TaskPerformanceScore(
                        value=0.9,
                        metric_type="dice_average",
                    ),
                ),
            ],
        )

        with (
            patch.object(
                ProjectRepo,
                "get_by_id",
                return_value=project,
            ) as mock_get_project,
            patch.object(ProjectRepo, "update_project_performance", return_value=None) as mock_update_performance,
            patch.object(
                EvaluationResultRepo,
                "get_performance_by_model_ids",
                return_value=fxt_performance,
            ) as mock_get_model_performance,
        ):
            # Act
            UpdateProjectPerformanceUseCase.update_project_performance(
                project_id=project.id_,
                task_node_id=task_node_id_1,
                inference_model_id=fxt_optimized_model.id_,
            )

        # Assert
        task_performance_1 = project.performance.task_performances[task_node_id_1]
        assert task_performance_1.task_node_id == task_node_id_1
        assert task_performance_1.score == TaskPerformanceScore(value=1, metric_type="score")

        task_performance_2 = project.performance.task_performances[task_node_id_2]
        assert task_performance_2.task_node_id == task_node_id_2
        assert task_performance_2.global_score == TaskPerformanceScore(
            value=0.1,
            metric_type="f-measure",
        )
        assert task_performance_2.local_score == TaskPerformanceScore(
            value=0.9,
            metric_type="dice_average",
        )

        assert project.performance.score == 0.55

        mock_get_project.assert_called_once_with(project.id_)
        mock_get_model_performance.assert_called_once_with(
            equivalent_model_ids=[fxt_optimized_model.id_],
            purpose=EvaluationPurpose.TEST,
        )
        mock_update_performance.assert_called_once()
