# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import asyncio
import sys

from consumer import NotificationsHandler
from geti_logger_tools.logger_config import initialize_logger

from config import validate_config

logger = initialize_logger(__name__)

DONE = asyncio.Event()


async def run():  # noqa: ANN201
    """
    Send emails based on messages in the topic
    """
    if not validate_config():
        logger.error("Configuration errors detected, exiting.")
        sys.exit(42)

    NotificationsHandler()
    await DONE.wait()


if __name__ == "__main__":
    asyncio.run(run())
