# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains the OptimizationController"""

from collections.abc import Sequence
from typing import cast

from communication.exceptions import (
    ModelAlreadyOptimizedException,
    NotReadyForOptimizationException,
    ObsoleteModelOptimizationException,
    PurgedModelException,
)
from communication.jobs_client import JobsClient
from communication.views.job_rest_views import JobRestViews
from service.job_submission import ModelOptimizationJobSubmitter

from geti_fastapi_tools.exceptions import ModelNotFoundException, ProjectNotFoundException
from geti_types import ID
from iai_core_py.configuration.elements.optimization_parameters import POTOptimizationParameters
from iai_core_py.entities.model import Model, ModelDeprecationStatus, ModelOptimizationType, NullModel
from iai_core_py.entities.model_storage import ModelStorageIdentifier
from iai_core_py.entities.project import NullProject, Project
from iai_core_py.entities.subset import Subset
from iai_core_py.repos import ConfigurableParametersRepo, ModelRepo, ProjectRepo


class OptimizationController:
    """
    Controls logic for optimization of models.
    """

    def start_optimization(
        self,
        project_id: ID,
        model_storage_id: ID,
        model_id: ID,
        author: ID,
    ) -> dict:
        """
        Creates a data class from the optimization config which contains parameters that
        will be used to then start an optimization job.

        :param project_id: ID of project that contains the model that will be optimized
        :param model_storage_id: ID of the model storage containing the model that will be optimized
        :param model_id: ID of the model to optimize
        :param author: the user submitting the job
        :return:
        """
        project = ProjectRepo().get_by_id(project_id)
        if isinstance(project, NullProject):
            raise ProjectNotFoundException(project_id)
        model_storage_identifier = ModelStorageIdentifier(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            model_storage_id=model_storage_id,
        )
        model = ModelRepo(model_storage_identifier).get_by_id(model_id)
        if isinstance(model, NullModel):
            raise ModelNotFoundException(model_id=model_id)

        if model.model_deprecation_status == ModelDeprecationStatus.OBSOLETE:
            raise ObsoleteModelOptimizationException(model_id=model.id_)

        if model.purge_info.is_purged:
            raise PurgedModelException("Can not optimize an archived model since its weights are deleted.")

        if len(model.get_train_dataset()) == 0 or not any(
            item.subset for item in model.get_train_dataset() if item.subset == Subset.TESTING
        ):
            raise NotReadyForOptimizationException(
                reason="Optimization is not possible at this moment because too much of the "
                "dataset that was used to train this model has been deleted."
            )

        base_model_id = (
            model.id_ if model.optimization_type == ModelOptimizationType.NONE else model.previous_trained_revision_id
        )

        optimized_models = ModelRepo(model.model_storage_identifier).get_optimized_models_by_trained_revision_id(
            trained_revision_id=base_model_id,
        )
        job_id = self._optimize_pot(
            project=project,
            author=author,
            model=model,
            optimized_models=optimized_models,
        )
        return JobRestViews.job_id_to_rest(job_id=job_id)

    @staticmethod
    def _optimize_pot(
        project: Project,
        author: ID,
        model: Model,
        optimized_models: Sequence[Model] | None,
    ) -> ID | None:
        """
        Submits a POT optimization job. The POT parameters are retrieved from the database.

        :param project: the project that contains the model to optimize
        :param author: the user submitting the job
        :param model: model instance to be optimized
        :param optimized_models: the related optimized models
        :return: ID for the submitted optimization job
        :raises: ModelAlreadyOptimizedException if model is already optimized with POT
        """
        config_params_repo = ConfigurableParametersRepo(project.identifier)
        repo_config_data = config_params_repo.get_or_create_hyper_parameters(model_storage=model.model_storage).data
        if hasattr(repo_config_data, "pot_parameters"):
            repo_pot_parameters = cast(
                "POTOptimizationParameters",
                repo_config_data.pot_parameters,  # type: ignore[attr-defined]
            )
        else:
            repo_pot_parameters = POTOptimizationParameters()

        # Check if model is already POT optimized with same parameter
        if optimized_models is not None:
            for opt_model in optimized_models:
                if opt_model.optimization_type != ModelOptimizationType.POT:
                    continue
                pot_setting = cast(
                    "POTOptimizationParameters",
                    opt_model.configuration.configurable_parameters.pot_parameters,  # type: ignore[attr-defined]
                )
                if pot_setting.stat_subset_size == repo_pot_parameters.stat_subset_size:
                    raise ModelAlreadyOptimizedException(
                        model_id=model.id_,
                        optimization_type=ModelOptimizationType.POT,
                    )

        model.configuration.configurable_parameters.pot_parameters = repo_pot_parameters  # type: ignore[attr-defined]
        job_submitter = ModelOptimizationJobSubmitter(JobsClient().jobs_client)
        return job_submitter.execute(
            project=project, model=model, optimization_type=ModelOptimizationType.POT, author=author
        )
