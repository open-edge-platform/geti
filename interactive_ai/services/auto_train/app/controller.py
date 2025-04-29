# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains the core logic of the auto-train controller"""

import logging
from datetime import datetime, timedelta

from grpc import RpcError

from entities import AutoTrainActivationRequest, FeatureFlag, NullAutoTrainActivationRequest
from exceptions import InvalidAutoTrainRequestError, JobSubmissionError
from job_creation_helpers import TRAIN_JOB_PRIORITY, TRAIN_JOB_REQUIRED_GPUS, JobDuplicatePolicy, TrainTaskJobData
from repo import SessionBasedAutoTrainActivationRepo

from geti_telemetry_tools import unified_tracing
from geti_types import CTX_SESSION_VAR, ID, DatasetStorageIdentifier, session_context
from grpc_interfaces.job_submission.client import GRPCJobsClient
from grpc_interfaces.job_submission.pb.job_service_pb2 import SubmitJobRequest
from sc_sdk.configuration.elements.component_parameters import ComponentType
from sc_sdk.configuration.elements.dataset_manager_parameters import DatasetManagementConfig
from sc_sdk.entities.model_storage import NullModelStorage
from sc_sdk.entities.model_template import ModelTemplateDeprecationStatus
from sc_sdk.entities.project import NullProject
from sc_sdk.repos import ConfigurableParametersRepo, DatasetRepo, ModelStorageRepo, ProjectRepo
from sc_sdk.repos.dataset_entity_repo import PipelineDatasetRepo
from sc_sdk.utils.feature_flags import FeatureFlagProvider
from sc_sdk.utils.time_utils import now

logger = logging.getLogger(__name__)

AUTO_TRAIN_AUTHOR = ID("geti")
last_job_submission_time: dict[ID, datetime] = {}  # dict[task_id, last_job_submission]


class AutoTrainController:
    """
    The AutoTrainController is responsible for submitting train jobs for the tasks
    that meet the conditions required for auto-training.

    :param debouncing_period: Debouncing interval in seconds
    :param jobs_grpc_client_address: Address of the gRPC client for submitting the auto-train jobs
    :param job_submission_cooldown: Number of seconds in which jobs cannot be resubmitted for a task
    """

    def __init__(
        self,
        debouncing_period: int,
        jobs_grpc_client_address: str,
        job_submission_cooldown: int,
    ):
        self.debounce_period = debouncing_period
        self.jobs_grpc_client_address = jobs_grpc_client_address
        self._jobs_client: GRPCJobsClient | None = None  # initialized lazily
        self.job_submission_cooldown = job_submission_cooldown

    @property
    def jobs_client(self) -> GRPCJobsClient:
        """Initialize and/or get the gRPC client to submit jobs"""
        if self._jobs_client is None:
            self._jobs_client = GRPCJobsClient(
                grpc_address=self.jobs_grpc_client_address,
                metadata_getter=lambda: CTX_SESSION_VAR.get().as_tuple(),
            )
        return self._jobs_client

    def find_ready_request(self) -> AutoTrainActivationRequest:
        """
        Find an auto-train request with following conditions:
            - has the flag 'ready' set to True
            - timestamp older than the current one minus the debouncing period (only if debouncer is NOT bypassed)
            - corresponding task is not in 'cooldown' phase (last job submission is not too recent)

        :return: AutoTrainActivationRequest if a request is found, NullAutoTrainActivationRequest otherwise.
        """
        repo = SessionBasedAutoTrainActivationRepo()
        query_timestamp = now() - timedelta(seconds=self.debounce_period)
        logger.debug(
            "Searching for ready requests with timestamp earlier than %s",
            query_timestamp,
        )
        request = repo.get_one_ready(latest_timestamp=query_timestamp)
        if not isinstance(request, NullAutoTrainActivationRequest):
            last_submission = last_job_submission_time.get(request.task_node_id)
            within_cooldown = (
                last_submission is not None and (now() - last_submission).seconds < self.job_submission_cooldown
            )
            if within_cooldown:
                logger.info(
                    "Auto-train request ignored. Job for task with ID `%s` was submitted less than %s seconds ago.",
                    request.task_node_id,
                    self.job_submission_cooldown,
                )
                # Remove the request since it's most likely spurious, created shortly after the last job submission
                self.remove_request_by_task(task_node_id=request.task_node_id)
                return NullAutoTrainActivationRequest()
            logger.info(
                "Found auto-train ready request for task with ID `%s`.",
                request.task_node_id,
            )
        return request

    @unified_tracing
    def submit_train_job(self, auto_train_request: AutoTrainActivationRequest) -> None:
        """
        Submit a training job for the task specified in the request

        :param auto_train_request: Auto-train activation request object
        :raises InvalidAutoTrainRequestError:
           - If the project specified in the auto-train request does not exist
           - If the task specified in the auto-train request is not contained within the project
           - If the request is missing the model storage ID
           - If the model storage cannot be found
        :raises JobSubmissionError:
           - If a problem occurs when submitting the job to the jobs client
        """
        with session_context(session=auto_train_request.session):
            config_repo = ConfigurableParametersRepo(project_identifier=auto_train_request.project_identifier)
            model_storage_repo = ModelStorageRepo(project_identifier=auto_train_request.project_identifier)
            project_repo = ProjectRepo()

            dataset_manager_config = config_repo.get_or_create_component_parameters(
                data_instance_of=DatasetManagementConfig,
                component=ComponentType.PIPELINE_DATASET_MANAGER,
            )
            project = project_repo.get_by_id(auto_train_request.project_id)
            if isinstance(project, NullProject):
                raise InvalidAutoTrainRequestError(
                    f"Auto-train request cannot be processed: the project {auto_train_request.project_id} "
                    f"cannot not be found; this may happen if that project was deleted."
                )
            task_node = project.get_trainable_task_node_by_id(task_id=auto_train_request.task_node_id)
            if task_node is None:
                raise InvalidAutoTrainRequestError(
                    f"Auto-train request cannot be processed: the task with ID `{auto_train_request.task_node_id}` "
                    f"was not found within the project with ID `{auto_train_request.project_id}`."
                )
            model_storage_id = auto_train_request.model_storage_id
            if model_storage_id is None:
                raise InvalidAutoTrainRequestError(
                    f"Auto-train request cannot be processed: missing model storage ID in the request "
                    f"relative to task node {auto_train_request.task_node_id}."
                )
            model_storage = model_storage_repo.get_by_id(model_storage_id)
            if isinstance(model_storage, NullModelStorage):
                raise InvalidAutoTrainRequestError(
                    f"Auto-train request cannot be processed: the model storage {auto_train_request.model_storage_id} "
                    f"cannot not be found; this may happen if that project was deleted."
                )
            if model_storage.model_template.model_status is ModelTemplateDeprecationStatus.OBSOLETE:
                raise InvalidAutoTrainRequestError(
                    f"Auto-train request cannot be processed: the model storage {auto_train_request.model_storage_id} "
                    f"uses an obsolete model template '{model_storage.model_template.model_template_id}'."
                )

            num_dataset_items = self.get_num_dataset_items(
                dataset_storage_identifier=DatasetStorageIdentifier(
                    workspace_id=auto_train_request.workspace_id,
                    project_id=auto_train_request.project_id,
                    dataset_storage_id=project.training_dataset_storage_id,
                ),
                task_node_id=auto_train_request.task_node_id,
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

            train_job_data = TrainTaskJobData(
                model_storage=model_storage,
                project=project,
                task_node=task_node,
                activate_model_storage=True,
                from_scratch=False,
                hyper_parameters_id=None,
                workspace_id=auto_train_request.workspace_id,
                dataset_storage=project.get_training_dataset_storage(),
                max_training_dataset_size=num_dataset_items,
                min_annotation_size=min_annotation_size,
                max_number_of_annotations=max_number_of_annotations,
                reshuffle_subsets=False,
                keep_mlflow_artifacts=keep_mlflow_artifacts,
            )

            train_cost = None
            if FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_CREDIT_SYSTEM):
                train_cost = [SubmitJobRequest.CostRequest(unit="images", amount=num_dataset_items)]

            try:
                job_id = self.jobs_client.submit(
                    priority=TRAIN_JOB_PRIORITY,
                    job_name=train_job_data.job_name,
                    job_type=train_job_data.job_type,
                    key=train_job_data.create_key(),
                    payload=train_job_data.create_payload(),
                    metadata=train_job_data.create_metadata(),
                    duplicate_policy=JobDuplicatePolicy.REPLACE.name.lower(),
                    author=AUTO_TRAIN_AUTHOR,
                    project_id=auto_train_request.project_id,
                    gpu_num_required=TRAIN_JOB_REQUIRED_GPUS,
                    cost=train_cost,
                    cancellable=True,
                )
            except ValueError as exc:
                raise JobSubmissionError("Failed to prepare training job") from exc
            except RpcError as rpc_error:
                raise JobSubmissionError("Failed to submit training job") from rpc_error
            logger.info("Submitted job with ID `%s`.", job_id)
            last_job_submission_time[auto_train_request.task_node_id] = now()

    @staticmethod
    def get_num_dataset_items(dataset_storage_identifier: DatasetStorageIdentifier, task_node_id: ID) -> int:
        """
        Get the number of dataset items in the training dataset of the given dataset storage

        :param dataset_storage_identifier: Identifier of the dataset storage containing the items
        :param task_node_id: ID of the task node to train
        :return: Number of dataset items
        """
        pipeline_dataset_entity = PipelineDatasetRepo(dataset_storage_identifier).get_one()
        task_dataset_entity = pipeline_dataset_entity.task_datasets[task_node_id]
        return DatasetRepo(dataset_storage_identifier).count_items(dataset_id=task_dataset_entity.dataset_id)

    @staticmethod
    @unified_tracing
    def remove_request_by_task(task_node_id: ID) -> None:
        """
        Remove any auto-train activation job request relative to the given task

        :param task_node_id: ID of the task node
        """
        repo = SessionBasedAutoTrainActivationRepo()
        repo.delete_by_task_node_id(task_node_id=task_node_id)
        logger.info("Removed request for task with ID `%s`.", task_node_id)

    def shutdown(self) -> None:
        """Performs a graceful shutdown of the jobs client connection."""
        if self._jobs_client is not None:
            self._jobs_client.close()
        self.cleanup_last_job_submission_time()

    def cleanup_last_job_submission_time(self) -> None:
        """cleanup last_job_submission_time by deleting expired items"""
        current_timestamp = now()
        expired_tasks = [
            task_id
            for task_id, last_submission in last_job_submission_time.items()
            if (current_timestamp - last_submission).seconds > self.job_submission_cooldown
        ]
        for task_id in expired_tasks:
            del last_job_submission_time[task_id]
        n_remaining = len(last_job_submission_time)
        if n_remaining > 100:
            logging.warning(
                "Deleted %s expired items from `last_job_submission_time` but %s still remaining.",
                len(expired_tasks),
                n_remaining,
            )
