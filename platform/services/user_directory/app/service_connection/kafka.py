# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
import os

from confluent_kafka import Producer

logger = logging.getLogger(__name__)


def _sasl_conf():
    sasl_conf = {"sasl.mechanism": "PLAIN", "security.protocol": "SASL_PLAINTEXT"}

    sasl_conf.update(
        {"sasl.username": os.environ.get("KAFKA_USERNAME", ""), "sasl.password": os.environ.get("KAFKA_PASSWORD", "")}
    )

    return sasl_conf


def _delivery_report(err, msg):  # noqa: ANN001
    """Called once for each message produced to indicate delivery result.
    Triggered by poll() or flush()."""
    if err is not None:
        logger.error(f"Message delivery failed: {err}")
    else:
        logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}]")


def send_message(message: str) -> None:
    """Send message to kafka"""
    producer_conf = {"bootstrap.servers": f"{os.environ.get('KAFKA_ADDRESS', '')}"}
    producer_conf.update(_sasl_conf())
    p = Producer(producer_conf)
    topic = f"{os.environ.get('KAFKA_TOPIC_PREFIX', '')}{os.environ.get('GETI_NOTIFICATION_TOPIC', '')}"
    logger.info("producing message to kafka")
    p.produce(topic, message.encode("utf-8"), callback=_delivery_report)
    p.flush()
