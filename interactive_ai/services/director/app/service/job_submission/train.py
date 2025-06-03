# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from features.feature_flag_provider import FeatureFlag, FeatureFlagProvider
from service.configuration_service import ConfigurationService
from service.job_submission.base import JobParams, ModelJobSubmitter
from service.job_submission.job_creation_helpers import (
    TRAIN_JOB_PRIORITY,
    TRAIN_JOB_REQUIRED_GPUS,
    JobDuplicatePolicy,
    TrainTaskJobData,
    get_model_storage_for_task,
)

from geti_types import ID
from grpc_interfaces.job_submission.pb.job_service_pb2 import SubmitJobRequest
from iai_core.configuration.elements.component_parameters import ComponentType
from iai_core.configuration.elements.dataset_manager_parameters import DatasetManagementConfig
from iai_core.entities.model_storage import ModelStorage
from iai_core.entities.project import Project
from iai_core.entities.task_node import TaskNode
from iai_core.repos import ConfigurableParametersRepo


class ModelTrainingJobSubmitter(ModelJobSubmitter):
    def prepare_data(  # type: ignore  # noqa: PLR0913
        self,
        project: Project,
        task_node: TaskNode,
        author: ID,
        max_training_dataset_size: int | None = None,
        model_storage: ModelStorage | None = None,
        from_scratch: bool = False,
        activate_model_storage: bool = True,
        hyper_parameters_id: ID | None = None,
        reshuffle_subsets: bool = False,
    ) -> JobParams:
        """
        Creates a K8s task training job and submits it to the jobs client.

        :param project: project containing model and dataset storage
        :param task_node: Task to train
        :param author: ID of the user submitting the job
        :param max_training_dataset_size: Maximum size of the dataset to train. This equals the cost of the job.
        :param model_storage: ModelStorage to use for training.
        :param from_scratch: Whether to train the task from scratch.
        :param activate_model_storage: bool indicating if model storage should be
            activated upon successful training.
        :param hyper_parameters_id: ID of the hyper-parameters configuration to use for
            this job, if customized by the user. If None, then the job uses the active
            configuration (hyper-parameters) of the model storage
        :param reshuffle_subsets: Whether to reassign/shuffle all the items to subsets including Test set from scratch
        :return: ID of the training job that has been submitted.
        :raises JobCreationFailedException: if the job can't be created
        """
        config_repo = ConfigurableParametersRepo(project.identifier)
        dataset_manager_config = config_repo.get_or_create_component_parameters(
            data_instance_of=DatasetManagementConfig,
            component=ComponentType.PIPELINE_DATASET_MANAGER,
            task_id=None,
        )
        model_storage = get_model_storage_for_task(
            project_identifier=project.identifier,
            model_storage=model_storage,
            task_node_id=task_node.id_,
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

        keep_mlflow_artifacts = FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_RETAIN_TRAINING_ARTIFACTS)

        full_training_configuration = ConfigurationService.get_full_training_configuration(
            project_identifier=project.identifier,
            task_id=task_node.id_,
            model_manifest_id=model_storage.model_template.model_template_id,
            strict_validation=False,
        )

        train_job_data = TrainTaskJobData(
            model_storage=model_storage,
            project=project,
            task_node=task_node,
            activate_model_storage=activate_model_storage,
            from_scratch=from_scratch,
            workspace_id=project.workspace_id,
            dataset_storage=project.get_training_dataset_storage(),
            training_configuration=full_training_configuration,
            hyper_parameters_id=hyper_parameters_id,
            max_training_dataset_size=max_training_dataset_size,
            min_annotation_size=min_annotation_size,
            max_number_of_annotations=max_number_of_annotations,
            reshuffle_subsets=reshuffle_subsets,
            keep_mlflow_artifacts=keep_mlflow_artifacts,
        )
        train_cost = None
        if FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_CREDIT_SYSTEM):
            if max_training_dataset_size is None:
                raise ValueError("max_training_dataset_size is required to start a train job.")
            train_cost = [SubmitJobRequest.CostRequest(unit="images", amount=max_training_dataset_size)]
        return JobParams(
            priority=TRAIN_JOB_PRIORITY,
            job_name=train_job_data.job_name,
            job_type=train_job_data.job_type,
            key=train_job_data.create_key(),
            payload=train_job_data.create_payload(),
            metadata=train_job_data.create_metadata(),
            duplicate_policy=JobDuplicatePolicy.REJECT.name.lower(),
            author=author,
            project_id=project.id_,
            gpu_num_required=TRAIN_JOB_REQUIRED_GPUS,
            cost=train_cost,
            cancellable=True,
        )
