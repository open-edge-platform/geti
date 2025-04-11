# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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

from typing import TYPE_CHECKING, cast

from service.job_submission.base import JobParams, ModelJobSubmitter
from service.job_submission.job_creation_helpers import OPTIMIZE_JOB_PRIORITY, JobDuplicatePolicy, OptimizationJobData

from geti_types import ID
from sc_sdk.configuration.elements.component_parameters import ComponentType
from sc_sdk.configuration.elements.dataset_manager_parameters import DatasetManagementConfig
from sc_sdk.entities.model import Model, ModelOptimizationType
from sc_sdk.entities.project import Project
from sc_sdk.repos import ConfigurableParametersRepo

if TYPE_CHECKING:
    from sc_sdk.configuration.elements.optimization_parameters import POTOptimizationParameters


class ModelOptimizationJobSubmitter(ModelJobSubmitter):
    def prepare_data(  # type: ignore
        self, project: Project, model: Model, optimization_type: ModelOptimizationType, author: ID
    ) -> JobParams:
        """
        Prepares data for an optimize job submission.

        :param project: project containing model and dataset storage
        :param model: model to perform optimization on
        :param optimization_type: Optimization type to optimize the model with
        :param author: ID of the user submitting the job
        :return: ID of the optimization job that has been submitted.
        """
        optimization_params = self._get_model_optimization_parameters(model=model)
        config_repo = ConfigurableParametersRepo(project.identifier)
        dataset_manager_config = config_repo.get_or_create_component_parameters(
            data_instance_of=DatasetManagementConfig,
            component=ComponentType.PIPELINE_DATASET_MANAGER,
        )
        min_annotation_size = (
            None
            if dataset_manager_config.minimum_annotation_size == -1
            else dataset_manager_config.minimum_annotation_size
        )
        max_number_of_annotations = (
            None
            if dataset_manager_config.maximum_number_of_annotations == -1
            else dataset_manager_config.maximum_number_of_annotations
        )

        optimization_job_data = OptimizationJobData(
            workspace_id=project.workspace_id,
            project=project,
            training_dataset_storage=project.get_training_dataset_storage(),
            model=model,
            optimization_type=optimization_type,
            optimization_parameters=optimization_params,
            min_annotation_size=min_annotation_size,
            max_number_of_annotations=max_number_of_annotations,
        )
        return JobParams(
            priority=OPTIMIZE_JOB_PRIORITY,
            job_name=optimization_job_data.job_name,
            job_type=optimization_job_data.job_type,
            key=optimization_job_data.create_key(),
            payload=optimization_job_data.create_payload(),
            metadata=optimization_job_data.create_metadata(),
            duplicate_policy=JobDuplicatePolicy.REJECT.name.lower(),
            author=author,
            project_id=project.id_,
            gpu_num_required=optimization_job_data.gpu_num_required,
            cancellable=True,
        )

    @staticmethod
    def _get_model_optimization_parameters(model: Model) -> dict:
        """
        Return the model optimization parameters as a dict.

        :param model: the model to extract the optimization parameters from
        :returns: the optimization parameters for the model
        """
        pot_parameters = cast(
            "POTOptimizationParameters",
            model.configuration.configurable_parameters.pot_parameters,  # type: ignore[attr-defined]
        )

        return {"stat_subset_size": pot_parameters.stat_subset_size}
