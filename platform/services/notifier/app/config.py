# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Configuration management
"""

import logging
import os

KAFKA_ADDRESS = [address.strip() for address in os.getenv("KAFKA_ADDRESS", "").split(",")]
KAFKA_USERNAME = os.getenv("KAFKA_USERNAME")
KAFKA_PASSWORD = os.getenv("KAFKA_PASSWORD")

GETI_NOTIFICATION_TOPIC = os.getenv("GETI_NOTIFICATION_TOPIC", "")

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_LOGIN = os.getenv("SMTP_LOGIN", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
USE_START_TLS_ENV = os.getenv("USE_START_TLS", "undefined").lower()
if USE_START_TLS_ENV == "undefined":
    USE_START_TLS = SMTP_PORT != 465
else:
    USE_START_TLS = USE_START_TLS_ENV != "false"

VERIFY_HTTPS = os.getenv("INSECURE_SKIP_HTTPS_VALIDATION", "false").lower() != "true"

logger = logging.getLogger(__name__)


def validate_config() -> bool:
    """
    Validate required config values.
    If any errors are found log those and exit.
    """
    all_ok = True

    if not KAFKA_USERNAME:
        logger.error("Environment variable KAFKA_USERNAME must be set.")
        all_ok = False

    if not KAFKA_PASSWORD:
        logger.error("Environment variable KAFKA_PASSWORD must be set.")
        all_ok = False

    if not KAFKA_ADDRESS:
        logger.error("Environment variable KAFKA_ADDRESS must be set.")
        all_ok = False

    if not GETI_NOTIFICATION_TOPIC:
        logger.error("Environment variable GETI_NOTIFICATION_TOPIC must be set.")
        all_ok = False

    if not SMTP_HOST:
        logger.error("Environment variable SMTP_HOST must be set.")
        all_ok = False

    if not SMTP_PORT:
        logger.error("Environment variable SMTP_PORT must be set.")
        all_ok = False

    return all_ok
