# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module contains the DatasetIEKafkaHandler base class, which is responsible for
handling incoming Kafka events in the dataset ie MS.
"""

import logging

from application.file_object_management import FileObjectManager
from communication.helpers.job_helper import IMPORT_JOBS, JobType

from geti_kafka_tools import BaseKafkaHandler, KafkaRawMessage, TopicSubscription
from geti_types import ID, Singleton
from iai_core_py.session.session_propagation import setup_session_kafka

logger = logging.getLogger(__name__)


class DatasetIEKafkaHandler(BaseKafkaHandler, metaclass=Singleton):
    """KafkaHandler for dataset-ie-related workflows without a well-defined use case"""

    def __init__(self) -> None:
        super().__init__(group_id="dataset_ie_consumer")

    @property
    def topics_subscriptions(self) -> list[TopicSubscription]:
        return [
            TopicSubscription(topic="on_job_finished", callback=self.on_job_finished),
            TopicSubscription(topic="on_job_cancelled", callback=self.on_job_cancelled),
        ]

    @setup_session_kafka
    def on_job_finished(self, raw_message: KafkaRawMessage) -> None:
        value: dict = raw_message.value
        logger.debug(f"Job finished event received: {value}")
        job_type = value.get("job_type")
        if job_type in [JobType.PERFORM_IMPORT_TO_NEW_PROJECT, JobType.PERFORM_IMPORT_TO_EXISTING_PROJECT]:
            job_payload: dict = value["job_payload"]
            # remove metadata
            try:
                import_id = ID(job_payload["import_id"])
                FileObjectManager().metadata_repo.delete_by_id(import_id)
                logger.info(f"Deleted file medatata for import_id `{str(import_id)}`")
            except Exception as e:
                logger.exception(
                    f"Exception raised while deleting file medata for import_id `{str(import_id)}`, exception: {str(e)}"
                )

    @setup_session_kafka
    def on_job_cancelled(self, raw_message: KafkaRawMessage) -> None:
        value: dict = raw_message.value
        logger.debug(f"Job cancelled event received: {value}")
        job_type = value.get("job_type")
        if job_type in IMPORT_JOBS:
            job_payload: dict = value["job_payload"]
            # remove temporary files in s3 storage and metadata
            try:
                import_id = ID(job_payload["import_id"])
                FileObjectManager().delete_file(import_id)
                logger.info(f"Deleted file medatata and tempoary files for import_id `{str(import_id)}`.")
            except Exception as e:
                logger.exception(
                    "Exception raised while deleting file medata and temporary files "
                    f"for import_id `{str(import_id)}`, exception: {str(e)}"
                )
