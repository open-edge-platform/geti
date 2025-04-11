# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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


from active_learning.usecases import ActiveScoresUpdateUseCase

from geti_kafka_tools import BaseKafkaHandler, KafkaRawMessage, TopicSubscription
from geti_telemetry_tools import unified_tracing
from geti_types import ID, MediaType, Singleton
from sc_sdk.session.session_propagation import setup_session_kafka
from sc_sdk.utils.identifier_factory import IdentifierFactory


class ActiveLearningKafkaHandler(BaseKafkaHandler, metaclass=Singleton):
    """KafkaHandler for active learning use cases"""

    def __init__(self) -> None:
        super().__init__(group_id="active_learning_consumer")

    @property
    def topics_subscriptions(self) -> list[TopicSubscription]:
        return [
            TopicSubscription(topic="media_deletions", callback=self.on_media_deleted),
            TopicSubscription(topic="media_uploads", callback=self.on_media_uploaded),
            TopicSubscription(topic="predictions_and_metadata_created", callback=self.on_new_predictions_and_metadata),
            TopicSubscription(topic="project_deletions", callback=self.on_project_deleted),
        ]

    @staticmethod
    @setup_session_kafka
    @unified_tracing
    def on_media_uploaded(raw_message: KafkaRawMessage) -> None:
        value: dict = raw_message.value
        workspace_id = ID(value["workspace_id"])
        project_id = ID(value["project_id"])
        dataset_storage_id = ID(value["dataset_storage_id"])
        media_id = ID(value["media_id"])
        media_type = MediaType[value["media_type"].upper()]
        media_identifier = IdentifierFactory.identifier_from_tuple((media_type, media_id))

        # TODO 'on_media_uploaded' can process multiple media in a single call;
        #  after AL MS is ready (CVS-86210), batch the events for performance.
        ActiveScoresUpdateUseCase.on_media_uploaded(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
            media_identifiers=(media_identifier,),
            # synchronous because the handler is lightweight
            asynchronous=False,
        )

    @staticmethod
    @setup_session_kafka
    @unified_tracing
    def on_media_deleted(raw_message: KafkaRawMessage) -> None:
        value: dict = raw_message.value
        workspace_id = ID(value["workspace_id"])
        project_id = ID(value["project_id"])
        dataset_storage_id = ID(value["dataset_storage_id"])
        media_id = ID(value["media_id"])
        media_type = MediaType[value["media_type"].upper()]
        media_identifier = IdentifierFactory.identifier_from_tuple((media_type, media_id))

        # TODO 'on_media_deleted' can process multiple media in a single call;
        #  after AL MS is ready (CVS-86210), batch the events for performance.
        ActiveScoresUpdateUseCase.on_media_deleted(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
            media_identifiers=(media_identifier,),
            # async to avoid race conditions (updates serialized in the mapper)
            asynchronous=True,
        )

    @staticmethod
    @setup_session_kafka
    @unified_tracing
    def on_new_predictions_and_metadata(raw_message: KafkaRawMessage) -> None:
        value: dict = raw_message.value
        workspace_id = ID(value["workspace_id"])
        project_id = ID(value["project_id"])
        dataset_storage_id = ID(value["dataset_storage_id"])
        task_node_id = ID(value["task_node_id"])
        model_storage_id = ID(value["model_storage_id"])
        model_id = ID(value["model_id"])
        annotated_dataset_id = ID(value["annotated_dataset_id"])
        train_dataset_with_predictions_id = ID(value["train_dataset_with_predictions_id"])
        unannotated_dataset_with_predictions_id = ID(value["unannotated_dataset_with_predictions_id"])

        ActiveScoresUpdateUseCase.on_output_datasets_and_metadata_created(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
            task_node_id=task_node_id,
            model_storage_id=model_storage_id,
            model_id=model_id,
            annotated_dataset_id=annotated_dataset_id,
            train_dataset_with_predictions_id=train_dataset_with_predictions_id,
            unannotated_dataset_with_predictions_id=unannotated_dataset_with_predictions_id,
            # async because operation is long and event consumer single-threaded
            asynchronous=True,
        )

    @staticmethod
    @setup_session_kafka
    @unified_tracing
    def on_project_deleted(raw_message: KafkaRawMessage) -> None:
        value: dict = raw_message.value
        workspace_id = ID(value["workspace_id"])
        project_id = ID(value["project_id"])
        dataset_storage_id = ID(value["training_dataset_storage_id"])

        ActiveScoresUpdateUseCase.on_project_deleted(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
            # async to avoid race conditions (updates serialized in the mapper)
            asynchronous=True,
        )
