# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from typing import TYPE_CHECKING
from unittest.mock import patch

from tests.utils.test_helpers import (
    generate_inference_dataset_of_all_media_in_project,
    generate_training_dataset_of_all_annotated_media_in_project,
)

from usecases.update_project_performance_usecase import UpdateProjectPerformanceUseCase

from sc_sdk.entities.evaluation_result import EvaluationPurpose, EvaluationResult
from sc_sdk.entities.metrics import Performance, ScoreMetric
from sc_sdk.repos import EvaluationResultRepo, ProjectRepo

if TYPE_CHECKING:
    from sc_sdk.entities.model import Model
    from sc_sdk.entities.project import Project


class TestIntegrationUpdateProjectPerformanceUseCase:
    def test_update_project_performance(
        self,
        request,
        fxt_db_project_service,
        fxt_performance,
    ) -> None:
        project: Project = fxt_db_project_service.create_annotated_detection_project()
        model: Model = fxt_db_project_service.create_and_save_model()
        assert project.performance.score is None
        task_performance = next(iter(project.performance.task_performances.values()))
        task_node_id = task_performance.task_node_id
        assert task_performance.score is None

        with patch.object(EvaluationResultRepo, "get_performance_by_model_ids", return_value=fxt_performance):
            UpdateProjectPerformanceUseCase.update_project_performance(
                project_id=project.id_, task_node_id=task_node_id, inference_model_id=model.id_
            )

        project_repo: ProjectRepo = ProjectRepo()
        updated_project = project_repo.get_by_id(project.id_)
        assert updated_project.performance.score == 1
        task_performance = updated_project.performance.task_performances[task_node_id]
        assert task_performance.task_node_id == task_node_id
        assert task_performance.score is not None
        assert task_performance.score.value == 1
        assert task_performance.score.metric_type == "score"

        # simulate changing the active model by saving a new evaluation result and fetching it.
        dataset_storage = project.get_training_dataset_storage()
        _, train_dataset = generate_training_dataset_of_all_annotated_media_in_project(project)
        analyse_dataset = generate_inference_dataset_of_all_media_in_project(project)
        test_performance = Performance(score=ScoreMetric(value=0.7, name="score"))
        test_result_set = EvaluationResult(
            id_=EvaluationResultRepo.generate_id(),
            project_identifier=updated_project.identifier,
            model_storage_id=model.model_storage.id_,
            model_id=model.id_,
            dataset_storage_id=dataset_storage.id_,
            ground_truth_dataset=train_dataset.id_,
            prediction_dataset=analyse_dataset.id_,
            performance=test_performance,
            purpose=EvaluationPurpose.TEST,
        )
        # save an EVALUATION result with a different performance, if this is retrieved then the test will fail.
        eval_performance = Performance(score=ScoreMetric(value=0.0, name="score"))
        eval_result_set = EvaluationResult(
            id_=EvaluationResultRepo.generate_id(),
            project_identifier=updated_project.identifier,
            model_storage_id=model.model_storage.id_,
            model_id=model.id_,
            dataset_storage_id=dataset_storage.id_,
            ground_truth_dataset=train_dataset.id_,
            prediction_dataset=analyse_dataset.id_,
            performance=eval_performance,
            purpose=EvaluationPurpose.VALIDATION,
        )
        evaluation_result_repo = EvaluationResultRepo(project_identifier=updated_project.identifier)
        evaluation_result_repo.save(test_result_set)
        evaluation_result_repo.save(eval_result_set)
        request.addfinalizer(lambda: evaluation_result_repo.delete_all())

        UpdateProjectPerformanceUseCase.update_project_performance(
            project_id=project.id_, task_node_id=task_node_id, inference_model_id=model.id_
        )
        updated_project = project_repo.get_by_id(project.id_)
        assert updated_project.performance.score == 0.7
        task_performance = updated_project.performance.task_performances[task_node_id]
        assert task_performance.task_node_id == task_node_id
        assert task_performance.score is not None
        assert task_performance.score.value == 0.7
        assert task_performance.score.metric_type == "score"
