# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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

import logging

from communication.exceptions import FailedHealthCheck
from communication.kafka_handlers.annotation_kafka_handler import AnnotationKafkaHandler
from communication.kafka_handlers.miscellaneous_kafka_handler import MiscellaneousKafkaHandler
from communication.kafka_handlers.thumb_video_kafka_handler import ThumbVideoKafkaHandler

from geti_kafka_tools import EventProducer
from sc_sdk.repos.base.database_client import DatabaseClient

logger = logging.getLogger(__name__)


def health_check(mongodb_check: bool, kafka_check: bool) -> None:
    """
    Check the health of the requested services.

    Raise an exception if any of the services are not reachable.

    :param kafka_check: Check if Kafka is available
    :param mongodb_check: Check if MongoDB is available
    """
    checks = []
    if kafka_check:
        if AnnotationKafkaHandler().event_consumer is None:
            checks.append("Annotation kafka handler is not connected to the microservice.")
        if MiscellaneousKafkaHandler().event_consumer is None:
            checks.append("Miscellaneous kafka handler is not connected to the microservice.")
        if ThumbVideoKafkaHandler().event_consumer is None:
            checks.append("Thumb video kafka handler is not connected to the microservice.")
        try:
            check = EventProducer().health_check()
            if not check:
                raise RuntimeError("Could not reach the Kafka event producer")
        except Exception:
            logger.exception("Failed to connect to Kafka")
            checks.append("Kafka event producer is not connected to the microservice.")

    if mongodb_check and not DatabaseClient().is_running():
        checks.append("MongoDB is not connected to the microservice.")

    if checks:
        raise FailedHealthCheck("\n".join(checks))
