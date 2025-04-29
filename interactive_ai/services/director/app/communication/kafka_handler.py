# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module contains the kafka handlers for model job events and project lifecycle, which is responsible for
handling incoming Kafka events in the director MS.
"""

import logging
import os
from datetime import datetime
from typing import TYPE_CHECKING

from communication.exceptions import MissingJobPayloadAttribute
from metrics.instruments import (
    ModelTrainingDurationAttributes,
    TrainingDurationCounterJobStatus,
    training_duration_counter,
)
from service.job_submission.job_creation_helpers import JobType
from service.project_service import ProjectService

from geti_kafka_tools import BaseKafkaHandler, KafkaRawMessage, TopicSubscription
from geti_telemetry_tools import unified_tracing
from geti_types import CTX_SESSION_VAR, ID, ProjectIdentifier, Singleton
from sc_sdk.entities.model_storage import ModelStorageIdentifier
from sc_sdk.entities.model_test_result import TestState
from sc_sdk.repos import ModelRepo, ModelStorageRepo, ModelTestResultRepo, TaskNodeRepo
from sc_sdk.session.session_propagation import setup_session_kafka
from sc_sdk.utils.deletion_helpers import DeletionHelpers
from sc_sdk.utils.type_helpers import str2bool

if TYPE_CHECKING:
    from sc_sdk.entities.model import Model

logger = logging.getLogger(__name__)


class JobKafkaHandler(BaseKafkaHandler, metaclass=Singleton):
    """KafkaHandler for model job workflows"""

    def __init__(self) -> None:
        super().__init__(group_id="model_job_events_consumer")

    @property
    def topics_subscriptions(self) -> list[TopicSubscription]:
        return [
            TopicSubscription(topic="on_job_finished", callback=self.on_job_finished),
            TopicSubscription(topic="on_job_failed", callback=self.on_job_failed),
            TopicSubscription(topic="on_job_cancelled", callback=self.on_job_cancelled),
        ]

    @setup_session_kafka
    @unified_tracing
    def on_job_finished(self, raw_message: KafkaRawMessage) -> None:
        value: dict = raw_message.value
        job_id = ID(raw_message.key.decode())
        job_type = value.get("job_type")
        job_payload: dict = value["job_payload"]
        workspace_id = ID(value["workspace_id"])
        payload_project_id = value["job_payload"].get("project_id", None)
        project_id = ID(payload_project_id) if payload_project_id else None

        if not project_id:
            raise MissingJobPayloadAttribute(attribute="project_id")

        if job_type:
            ProjectService.unlock(job_type=job_type, project_id=project_id)

        if job_type == JobType.TRAIN:
            task_node_id = ID(job_payload["task_id"])
            model_metadata: dict = value["job_metadata"]["trained_model"]
            model_storage_id = ID(model_metadata["model_storage_id"])
            model_id = ID(model_metadata["model_id"])
            start_time = datetime.fromisoformat(value["start_time"])
            end_time = datetime.fromisoformat(value["end_time"])
            model_storage_identifier = ModelStorageIdentifier(
                workspace_id=workspace_id, project_id=project_id, model_storage_id=model_storage_id
            )

            duration = (end_time - start_time).total_seconds()
            model_repo = ModelRepo(model_storage_identifier)
            model = model_repo.get_by_id(model_id)
            base_model: Model = model.get_base_model()
            optimized_models = model_repo.get_optimized_models_by_base_model_id(base_model.id_)
            all_models = [*list(optimized_models), base_model]
            for model in all_models:
                model_repo.update_training_job_duration(model=model, training_job_duration=duration)
            _report_training_duration(
                job_id=job_id,
                project_id=project_id,
                task_node_id=task_node_id,
                model_architecture="",
                model_storage_id=model_storage_id,
                model_id=model_id,
                start_time=start_time,
                end_time=end_time,
                job_status=TrainingDurationCounterJobStatus.SUCCEEDED,
            )

    @setup_session_kafka
    @unified_tracing
    def on_job_failed(self, raw_message: KafkaRawMessage) -> None:
        session = CTX_SESSION_VAR.get()
        value: dict = raw_message.value
        job_type = value.get("job_type")
        job_payload: dict = value["job_payload"]
        job_metadata: dict = value["job_metadata"]
        payload_project_id = value["job_payload"].get("project_id", None)
        project_id = ID(payload_project_id) if payload_project_id else None
        logger.debug(f"Job failed event received: {value}")

        if not project_id:
            raise MissingJobPayloadAttribute(attribute="project_id")

        if job_type:
            ProjectService.unlock(job_type=job_type, project_id=project_id)

        match job_type:
            case JobType.MODEL_TEST:
                model_test_result_id = ID(job_payload["model_test_result_id"])
                project_identifier = ProjectIdentifier(workspace_id=session.workspace_id, project_id=project_id)
                model_test_result_repo = ModelTestResultRepo(project_identifier)
                model_test_result = model_test_result_repo.get_by_id(model_test_result_id)

                logger.debug(
                    f"Model testing has failed, setting model test result {model_test_result_id} state to FAILED"
                )
                model_test_result.state = TestState.FAILED
                model_test_result_repo.save(model_test_result)
            case JobType.OPTIMIZE_POT:
                deleted_model_ids = self._delete_optimize_job_models(
                    workspace_id=session.workspace_id,
                    project_id=project_id,
                    job_metadata=job_metadata,
                )
                if deleted_model_ids:
                    job_id = ID(raw_message.key.decode())
                    logger.info(
                        f"Optimized job failed (job_id: `{job_id}`): "
                        f"the following models have been deleted as a result - {deleted_model_ids}.",
                    )
            case JobType.TRAIN:
                self._process_failed_or_canceled_train_job(
                    raw_message=raw_message, training_duration_status=TrainingDurationCounterJobStatus.FAILED
                )

    @setup_session_kafka
    @unified_tracing
    def on_job_cancelled(self, raw_message: KafkaRawMessage) -> None:
        session = CTX_SESSION_VAR.get()
        value: dict = raw_message.value
        job_type = value.get("job_type")
        job_payload: dict = value["job_payload"]
        job_metadata: dict = value["job_metadata"]
        payload_project_id = value["job_payload"].get("project_id", None)
        project_id = ID(payload_project_id) if payload_project_id else None

        if not project_id:
            raise MissingJobPayloadAttribute(attribute="project_id")

        if job_type:
            ProjectService.unlock(job_type=job_type, project_id=project_id)

        match job_type:
            case JobType.MODEL_TEST:
                project_identifier = ProjectIdentifier(workspace_id=session.workspace_id, project_id=project_id)
                model_test_result_id = ID(job_payload["model_test_result_id"])
                model_test_result = ModelTestResultRepo(project_identifier).get_by_id(model_test_result_id)
                DeletionHelpers.delete_model_test_result(
                    project_identifier=project_identifier, model_test_result=model_test_result
                )
                logger.info(
                    "Deleted model test result with ID `%s` after cancelling its model test job.", model_test_result_id
                )
            case JobType.OPTIMIZE_POT:
                deleted_model_ids = self._delete_optimize_job_models(
                    workspace_id=session.workspace_id,
                    project_id=project_id,
                    job_metadata=job_metadata,
                )
                if deleted_model_ids:
                    job_id = ID(raw_message.key.decode())
                    logger.info(
                        f"Optimized job cancellation (job_id: `{job_id}`): "
                        f"the following models have been deleted as a result - {deleted_model_ids}.",
                    )
            case JobType.TRAIN:
                self._process_failed_or_canceled_train_job(
                    raw_message=raw_message, training_duration_status=TrainingDurationCounterJobStatus.CANCELLED
                )

    @staticmethod
    def _delete_optimize_job_models(workspace_id: ID, project_id: ID, job_metadata: dict) -> list[ID]:
        """
        Delete models created during the optimization job if the job has failed or been canceled.

        :param workspace_id: Workspace ID
        :param project_id: Project ID
        :param job_metadata: Job metadata
        :return: List of deleted model IDs
        """
        # Optimized model ID might not be present if the job failed before the optimization step
        if "optimized_model_id" not in job_metadata:
            return []
        model_storage_id = ID(job_metadata["model_storage_id"])
        optimized_model_id = ID(job_metadata["optimized_model_id"])
        model_storage_identifier = ModelStorageIdentifier(
            workspace_id=workspace_id, project_id=project_id, model_storage_id=model_storage_id
        )
        model_repo = ModelRepo(model_storage_identifier)
        optimize_model = model_repo.get_by_id(optimized_model_id)
        model_repo.delete_by_id(optimize_model.previous_revision_id)
        model_repo.delete_by_id(optimized_model_id)
        return [optimize_model.previous_revision_id, optimized_model_id]

    @staticmethod
    def _process_failed_or_canceled_train_job(
        raw_message: KafkaRawMessage, training_duration_status: TrainingDurationCounterJobStatus
    ) -> None:
        """
        Process failed or canceled training job events. Specifically, report training duration and delete the models if
        they have been not activated.

        :param raw_message: Kafka raw message
        :param training_duration_status: Training duration status
        """
        if training_duration_status not in [
            TrainingDurationCounterJobStatus.FAILED,
            TrainingDurationCounterJobStatus.CANCELLED,
        ]:
            raise ValueError(f"Invalid training duration status: {training_duration_status}")

        value: dict = raw_message.value
        job_id = ID(raw_message.key.decode())
        job_payload: dict = value["job_payload"]
        job_metadata: dict = value["job_metadata"]
        project_id = ID(value["job_payload"]["project_id"])

        task_node_id = ID(job_payload["task_id"])
        model_template_id = job_metadata["task"]["model_template_id"]
        trained_model = job_metadata.get("trained_model", {})
        model_storage_id = trained_model.get("model_storage_id")
        trained_base_model_id = trained_model.get("model_id")
        trained_model_activated = trained_model.get("model_activated")
        start_time = datetime.fromisoformat(value["start_time"])
        end_time = datetime.fromisoformat(value.get("end_time") or value["cancel_time"])
        _report_training_duration(
            job_id=job_id,
            project_id=project_id,
            task_node_id=task_node_id,
            model_architecture=model_template_id,
            model_storage_id=model_storage_id,
            model_id=trained_base_model_id,
            start_time=start_time,
            end_time=end_time,
            job_status=training_duration_status,
        )
        # Having a flag for keeping failed models can be useful for debugging purposes
        keep_failed_models = str2bool(os.environ.get("KEEP_FAILED_MODELS", "false").lower())
        if keep_failed_models:
            logger.warning("KEEP_FAILED_MODELS is set to True, not deleting failed models.")
        elif model_storage_id and trained_base_model_id and not trained_model_activated:
            logger.info(
                f"Model training has {training_duration_status.name} (job_id: `{job_id}`), "
                f"deleting models by base model ID {trained_base_model_id}"
            )
            DeletionHelpers.delete_models_by_base_model_id(
                project_id=project_id,
                model_storage_id=ID(model_storage_id),
                base_model_id=ID(trained_base_model_id),
            )


class ProjectKafkaHandler(BaseKafkaHandler, metaclass=Singleton):
    """KafkaHandler for project lifecycle events"""

    def __init__(self) -> None:
        super().__init__(group_id="project_lifecycle_events_consumer")

    @property
    def topics_subscriptions(self) -> list[TopicSubscription]:
        return [
            TopicSubscription(topic="project_creations", callback=self.on_project_created),
            TopicSubscription(topic="project_deletions", callback=self.on_project_deleted),
        ]

    @setup_session_kafka
    @unified_tracing
    def on_project_deleted(self, raw_message: KafkaRawMessage) -> None:
        value: dict = raw_message.value
        workspace_id = ID(value["workspace_id"])
        project_id = ID(value["project_id"])
        dataset_storage_id = ID(value["training_dataset_storage_id"])
        ProjectService.delete_entities(workspace_id, project_id, dataset_storage_id)

    @staticmethod
    @setup_session_kafka
    @unified_tracing
    def on_project_created(raw_message: KafkaRawMessage) -> None:
        value: dict = raw_message.value
        ProjectService.init_configuration(project_id=ID(value["project_id"]))


def _report_training_duration(  # noqa: PLR0913
    job_id: ID,
    project_id: ID,
    task_node_id: ID,
    model_architecture: str,
    model_storage_id: ID | None,
    model_id: ID | None,
    start_time: datetime,
    end_time: datetime,
    job_status: TrainingDurationCounterJobStatus,
) -> None:
    """
    Report training duration to Grafana

    :param job_id: The ID of the job
    :param project_id: The ID of the project
    :param task_node_id: The ID of the task node
    :param model_storage_id: model storage id
    :param model_id: trained model id, not necessarily base model
    :param start_time: training job start time
    :param end_time: training job end time
    :param job_status: Status of job, SUCCEEDED, CANCELLED or FAILED
    """
    session = CTX_SESSION_VAR.get()
    project_identifier = ProjectIdentifier(workspace_id=session.workspace_id, project_id=project_id)
    training_job_duration = (end_time - start_time).total_seconds()
    task_node = TaskNodeRepo(project_identifier).get_by_id(task_node_id)
    task_type_str = task_node.task_properties.task_type.name

    # The following variables are set to actual values only if information about the model is available
    training_duration: int = 0
    dataset_size: int = 0

    if model_id is not None and model_storage_id is not None:
        model_storage_identifier = ModelStorageIdentifier(
            workspace_id=session.workspace_id, project_id=project_id, model_storage_id=model_storage_id
        )
        model_storage_repo = ModelStorageRepo(project_identifier)
        model_storage = model_storage_repo.get_by_id(model_storage_id)
        model_architecture = model_storage.model_template.model_template_id
        model_repo = ModelRepo(model_storage_identifier)
        model = model_repo.get_by_id(model_id)
        dataset_size = len(model.get_train_dataset())
        training_duration = int(
            model.training_duration if model.training_duration else (end_time - model.creation_date).total_seconds()
        )

    attributes = ModelTrainingDurationAttributes(
        job_id=job_id,
        model_architecture=model_architecture,
        task_type=task_type_str,
        job_status=job_status.name,
        organization_id=str(session.organization_id),
        training_job_duration=training_job_duration,
        dataset_size=dataset_size,
    )
    training_duration_counter.add(amount=training_duration, attributes=attributes.to_dict())
    logger.debug(
        "Reported training duration of %s seconds for the job with attributes: %s",
        training_duration,
        attributes,
    )
