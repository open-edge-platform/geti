# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import PropertyMock, patch

import pytest

from communication.controllers.optimization_controller import OptimizationController
from communication.exceptions import (
    ModelAlreadyOptimizedException,
    NotReadyForOptimizationException,
    ObsoleteModelOptimizationException,
)
from communication.views.job_rest_views import JobRestViews
from service.job_submission import ModelOptimizationJobSubmitter

from geti_types import ID
from sc_sdk.entities.model import Model
from sc_sdk.entities.model_template import ModelTemplate
from sc_sdk.repos import ConfigurableParametersRepo, ModelRepo, ProjectRepo

DUMMY_USER = ID("dummy_user")


class TestOptimizationController:
    def test_start_optimization_on_already_optimized_job(
        self,
        fxt_project,
        fxt_model_storage,
        fxt_model,
        fxt_optimized_model_1,
        fxt_optimized_model_2,
        fxt_pot_hyperparameters,
        fxt_ote_id,
        fxt_hyper_parameters_with_groups,
    ) -> None:
        project_id = fxt_project.id_
        model_storage_id = fxt_model_storage.id_
        model_id = fxt_optimized_model_1.id_
        fxt_optimized_model_2.configuration.configurable_parameters.pot_parameters = (
            fxt_pot_hyperparameters.data.pot_parameters
        )
        optimized_models = [fxt_optimized_model_2]
        optimize_job_1_id = fxt_ote_id(1)
        rest_view = {"job_ids": optimize_job_1_id}

        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project) as mock_get_project,
            patch.object(
                ModelRepo,
                "get_by_id",
                return_value=fxt_optimized_model_1,
            ) as mock_get_model,
            patch.object(
                ModelRepo,
                "get_optimized_models_by_trained_revision_id",
                return_value=optimized_models,
            ) as mock_get_optimized_models,
            patch.object(
                ModelOptimizationJobSubmitter, "execute", side_effect=optimize_job_1_id
            ) as mock_optimize_job_submit,
            patch.object(ModelRepo, "save") as mock_save,
            patch.object(JobRestViews, "job_id_to_rest", return_value=rest_view) as mock_job_ids_to_rest,
            patch.object(ModelTemplate, "entrypoints", new_callable=PropertyMock),
            patch.object(
                Model,
                "get_train_dataset",
                return_value=fxt_model.get_train_dataset(),
            ),
            pytest.raises(ModelAlreadyOptimizedException),
            patch.object(
                ConfigurableParametersRepo,
                "get_or_create_hyper_parameters",
                return_value=fxt_hyper_parameters_with_groups,
            ),
        ):
            optimization_controller = OptimizationController()
            optimization_controller.start_optimization(
                project_id=project_id,
                model_storage_id=model_storage_id,
                model_id=model_id,
                author=DUMMY_USER,
            )

        mock_get_project.assert_called_once_with(project_id)
        mock_get_model.assert_called_once_with(model_id)
        mock_optimize_job_submit.assert_not_called()
        mock_get_optimized_models.assert_called_once()
        mock_save.assert_not_called()
        mock_job_ids_to_rest.assert_not_called()

    def test_start_optimization_with_missing_testing_dataset(
        self,
        fxt_project,
        fxt_model_storage,
        fxt_model,
        fxt_dataset_training_subset_only,
        fxt_ote_id,
    ) -> None:
        project_id = fxt_project.id_
        model_storage_id = fxt_model_storage.id_
        model_id = fxt_model.id_

        optimize_job_1_id = fxt_ote_id(1)
        rest_view = {"job_id": optimize_job_1_id}
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project) as mock_get_project,
            patch.object(ModelRepo, "get_by_id", return_value=fxt_model) as mock_get_model,
            patch.object(
                ModelOptimizationJobSubmitter, "execute", side_effect=optimize_job_1_id
            ) as mock_optimize_job_submit,
            patch.object(ModelRepo, "save") as mock_save,
            patch.object(JobRestViews, "job_id_to_rest", return_value=rest_view) as mock_job_ids_to_rest,
            patch.object(
                fxt_model,
                "get_train_dataset",
                return_value=fxt_dataset_training_subset_only,
            ),
            pytest.raises(NotReadyForOptimizationException),
        ):
            optimization_controller = OptimizationController()
            optimization_controller.start_optimization(
                project_id=project_id,
                model_storage_id=model_storage_id,
                model_id=model_id,
                author=DUMMY_USER,
            )

        mock_get_project.assert_called_once_with(project_id)
        mock_get_model.assert_called_once_with(model_id)
        mock_optimize_job_submit.assert_not_called()
        mock_save.assert_not_called()
        mock_job_ids_to_rest.assert_not_called()

    def test_start_optimization_with_obsolete_model(
        self,
        fxt_project,
        fxt_model_storage,
        fxt_obsolete_model,
        fxt_ote_id,
    ) -> None:
        project_id = fxt_project.id_
        model_storage_id = fxt_model_storage.id_
        model_id = fxt_obsolete_model.id_

        optimize_job_1_id = fxt_ote_id(1)
        rest_view = {"job_id": optimize_job_1_id}
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project) as mock_get_project,
            patch.object(ModelRepo, "get_by_id", return_value=fxt_obsolete_model) as mock_get_model,
            patch.object(
                ModelOptimizationJobSubmitter, "execute", side_effect=optimize_job_1_id
            ) as mock_optimize_job_submit,
            patch.object(ModelRepo, "save") as mock_save,
            patch.object(JobRestViews, "job_id_to_rest", return_value=rest_view) as mock_job_ids_to_rest,
            pytest.raises(ObsoleteModelOptimizationException),
        ):
            optimization_controller = OptimizationController()
            optimization_controller.start_optimization(
                project_id=project_id,
                model_storage_id=model_storage_id,
                model_id=model_id,
                author=DUMMY_USER,
            )

        mock_get_project.assert_called_once_with(project_id)
        mock_get_model.assert_called_once_with(model_id)
        mock_optimize_job_submit.assert_not_called()
        mock_save.assert_not_called()
        mock_job_ids_to_rest.assert_not_called()
