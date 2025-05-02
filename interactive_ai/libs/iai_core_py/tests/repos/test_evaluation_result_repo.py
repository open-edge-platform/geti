# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import copy

import pytest

from iai_core.entities.evaluation_result import EvaluationPurpose, EvaluationResult, NullEvaluationResult
from iai_core.entities.metrics import NullPerformance, Performance, ScoreMetric
from iai_core.entities.model import Model, NullModel
from iai_core.repos import DatasetRepo, EvaluationResultRepo, ModelRepo
from iai_core.services.model_service import ModelService
from tests.test_helpers import (
    empty_model_configuration,
    generate_inference_dataset_of_all_media_in_project,
    generate_random_annotated_project,
    generate_training_dataset_of_all_annotated_media_in_project,
    register_model_template,
)

from geti_types import ID


@pytest.fixture
def fxt_evaluation_result(fxt_empty_project, fxt_mongo_id, fxt_dataset) -> EvaluationResult:
    ground_truth_dataset = copy.deepcopy(fxt_dataset)
    ground_truth_dataset.id_ = fxt_mongo_id(5)
    prediction_dataset = copy.deepcopy(fxt_dataset)
    prediction_dataset.id_ = fxt_mongo_id(6)
    return EvaluationResult(
        id_=fxt_mongo_id(1),
        project_identifier=fxt_empty_project.identifier,
        model_storage_id=fxt_mongo_id(2),
        model_id=fxt_mongo_id(3),
        dataset_storage_id=fxt_mongo_id(4),
        ground_truth_dataset=ground_truth_dataset,
        prediction_dataset=prediction_dataset,
        performance=NullPerformance(),
        purpose=EvaluationPurpose.VALIDATION,
    )


class TestEvaluationResultRepo:
    def test_evaluation_result_repo(self, request, project_empty, fxt_mongo_id, fxt_training_framework) -> None:
        """
        <b>Description:</b>
        Check that EvaluationResultRepo's are generated correctly.

        <b>Input data:</b>
        Randomly annotated project
        Dataset split into Train and Analyse

        <b>Expected results:</b>
        This test succeeds if the EvaluationResult can be added to the EvaluationResultRepo
        and can be retrieved unchanged

        <b>Steps</b>
        1. Set up the repository with a model and a train and evaluation dataset
        2. Create evaluation results and save them to the EvaluationResultRepo
        3. Check that the evaluation results are correctly saved and retrieved from the repository.
        """
        model_template = register_model_template(request, type(None), "counting", "COUNTING", trainable=True)
        project = generate_random_annotated_project(
            test_case=request,
            name="__Test MongoDB mapper ",
            description="test_evaluation_result_mapper()",
            model_template_id=model_template,
        )[0]

        dataset_storage = project.get_training_dataset_storage()
        _, train_dataset = generate_training_dataset_of_all_annotated_media_in_project(project)
        analyse_dataset = generate_inference_dataset_of_all_media_in_project(project)

        dataset_repo = DatasetRepo(dataset_storage.identifier)
        dataset_repo.save_deep(train_dataset)
        dataset_repo.save_deep(analyse_dataset)

        request.addfinalizer(lambda: dataset_repo.delete_by_id(train_dataset.id_))
        request.addfinalizer(lambda: dataset_repo.delete_by_id(analyse_dataset.id_))

        task_node = project.tasks[1]
        assert task_node.task_properties.is_trainable

        # Create a new evaluation result
        model_storage = ModelService.get_active_model_storage(
            project_identifier=project.identifier,
            task_node_id=task_node.id_,
        )
        model = Model(
            project=project,
            model_storage=model_storage,
            train_dataset=train_dataset,
            configuration=empty_model_configuration(),
            id_=ModelRepo.generate_id(),
            previous_trained_revision=NullModel(),
            data_source_dict={"test_data": b""},
            training_framework=fxt_training_framework,
        )

        ModelRepo(model_storage.identifier).save(model)

        performance = Performance(score=ScoreMetric(value=1.0, name="name"))
        evaluation_result1 = EvaluationResult(
            id_=EvaluationResultRepo.generate_id(),
            project_identifier=project.identifier,
            model_storage_id=model.model_storage.id_,
            model_id=model.id_,
            dataset_storage_id=dataset_storage.id_,
            ground_truth_dataset=train_dataset.id_,
            prediction_dataset=analyse_dataset.id_,
            performance=performance,
            purpose=EvaluationPurpose.VALIDATION,
        )

        evaluation_result2 = EvaluationResult(
            id_=EvaluationResultRepo.generate_id(),
            project_identifier=project.identifier,
            model_storage_id=model.model_storage.id_,
            model_id=model.id_,
            dataset_storage_id=dataset_storage.id_,
            ground_truth_dataset=train_dataset.id_,
            prediction_dataset=analyse_dataset.id_,
            performance=performance,
            purpose=EvaluationPurpose.TEST,
        )

        evaluation_result_repo = EvaluationResultRepo(project_empty.identifier)
        evaluation_result_repo.save(evaluation_result1)
        evaluation_result_repo.save(evaluation_result2)

        # Retrieve one evaluation result by ID
        result = evaluation_result_repo.get_by_id(evaluation_result1.id_)
        assert evaluation_result1.id_ == result.id_, "Expected the two ID to match"

        # Get the latest result associated with any (equivalent) model
        result = evaluation_result_repo.get_latest_by_model_ids(
            equivalent_model_ids=[model.id_, fxt_mongo_id(0), fxt_mongo_id(1)]
        )
        assert evaluation_result2.id_ == result.id_, "Expected the two ID to match"

        # Get the latest result associated with the model
        result = evaluation_result_repo.get_latest_by_model_ids([model.id_])
        assert evaluation_result2.id_ == result.id_, "Expected the two ID to match"

        # Get the latest evaluation result associated with the model
        result = evaluation_result_repo.get_latest_by_model_ids([model.id_], purpose=EvaluationPurpose.VALIDATION)
        assert evaluation_result1.id_ == result.id_, "Expected the two ID to match"

        assert len(list(evaluation_result_repo.get_all())) == 2

        # Get the score for the latest model
        performance = evaluation_result_repo.get_performance_by_model_ids([model.id_, fxt_mongo_id(2)])
        assert performance is not None and evaluation_result1 is not None
        assert evaluation_result1.performance is not None
        assert performance.score == evaluation_result1.performance.score

        # Check if updating work
        evaluation_result1.purpose = EvaluationPurpose.PREEVALUATION
        evaluation_result_repo.save(evaluation_result1)
        result = evaluation_result_repo.get_by_id(evaluation_result1.id_)
        assert evaluation_result1.purpose == result.purpose, "Expected the two ID to match"

        # Check if delete work
        evaluation_result_repo.delete_by_id(evaluation_result1.id_)
        result = evaluation_result_repo.get_by_id(evaluation_result1.id_)
        assert NullEvaluationResult() == result, "Expected the evaluation result to be null"

    def test_delete_all(self, fxt_project_identifier) -> None:
        """Test method `delete_all`."""
        evaluation_result1 = EvaluationResult(
            id_=EvaluationResultRepo.generate_id(),
            project_identifier=fxt_project_identifier,
            model_storage_id=ID(),
            model_id=ID(),
            dataset_storage_id=ID(),
            ground_truth_dataset=ID(),
            prediction_dataset=ID(),
            performance=NullPerformance(),
            purpose=EvaluationPurpose.VALIDATION,
        )
        evaluation_result2 = EvaluationResult(
            id_=EvaluationResultRepo.generate_id(),
            project_identifier=fxt_project_identifier,
            model_storage_id=ID(),
            model_id=ID(),
            dataset_storage_id=ID(),
            ground_truth_dataset=ID(),
            prediction_dataset=ID(),
            performance=NullPerformance(),
            purpose=EvaluationPurpose.TEST,
        )
        evaluation_result_repo = EvaluationResultRepo(fxt_project_identifier)
        evaluation_result_repo.save(evaluation_result1)
        evaluation_result_repo.save(evaluation_result2)
        assert len(list(evaluation_result_repo.get_all())) == 2

        evaluation_result_repo.delete_all()

        assert not list(evaluation_result_repo.get_all())

    def test_delete_all_by_model_id(self, request, fxt_project_identifier, fxt_ote_id) -> None:
        """Test method `delete_all_by_model_id`."""
        target_model_id = fxt_ote_id(41)
        other_model_id = fxt_ote_id(42)
        evaluation_result1 = EvaluationResult(
            id_=EvaluationResultRepo.generate_id(),
            project_identifier=fxt_project_identifier,
            model_storage_id=ID(),
            model_id=target_model_id,
            dataset_storage_id=ID(),
            ground_truth_dataset=ID(),
            prediction_dataset=ID(),
            performance=NullPerformance(),
            purpose=EvaluationPurpose.VALIDATION,
        )
        evaluation_result2 = EvaluationResult(
            id_=EvaluationResultRepo.generate_id(),
            project_identifier=fxt_project_identifier,
            model_storage_id=ID(),
            model_id=other_model_id,
            dataset_storage_id=ID(),
            ground_truth_dataset=ID(),
            prediction_dataset=ID(),
            performance=NullPerformance(),
            purpose=EvaluationPurpose.TEST,
        )
        evaluation_result_repo = EvaluationResultRepo(fxt_project_identifier)
        request.addfinalizer(lambda: evaluation_result_repo.delete_all())
        evaluation_result_repo.save(evaluation_result1)
        evaluation_result_repo.save(evaluation_result2)
        assert len(list(evaluation_result_repo.get_all())) == 2

        evaluation_result_repo.delete_all_by_model_id(evaluation_result1.model_id)

        remaining_eval_results = list(evaluation_result_repo.get_all())
        assert len(remaining_eval_results) == 1
        assert remaining_eval_results[0].model_id == other_model_id
