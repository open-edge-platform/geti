"""
Configuration of base logger for the entire platform.
Logger parameters are stored in a config map and are available in every container having it mounted.
"""

import asyncio
import json
import logging
import os
import time
from threading import Thread

from geti_logger_tools.constants import DEFAULT_CONFIG_DIR, DEFAULT_CONFIG_FILE

LOGGER_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
NON_CONFIGURABLE_LOGGERS = ["uvicorn.access", "werkzeug", "pika", "aiohttp.access", "geti_logger_tools.logger_config"]


def get_logging_format(extra_headers: str = "") -> str:
    """
    Get the logging format as a string.

    :param extra_headers: Optional format string to embed additional headers before the message in the log records
    :returns: Logging format as string
    """
    extra_headers_str = f" {extra_headers}" if extra_headers else ""
    return f"%(asctime)s,%(msecs)03d [%(levelname)-8s] [%(name)s:%(lineno)d]{extra_headers_str}: %(message)s"


def _refresh(file_path, log_level=None):  # noqa: ANN001
    """
    Dynamically refreshes logger with information from given config file
    :param file_path: location of config file for logger, defined in the config map
    :param log_level: currently used log_level (taken from config map)
    :return: new log level
    """
    try:
        with open(file_path) as file:
            logging_config = json.load(file)
            new_level = logging_config["LOG_LEVEL"]
    except FileNotFoundError:
        return log_level

    try:
        if log_level != new_level:
            for single_logger in logging.Logger.manager.loggerDict.copy():
                logger = logging.getLogger(single_logger)
                if logger.name not in NON_CONFIGURABLE_LOGGERS:
                    logger.setLevel(getattr(logging, new_level))
                    # Do not output first initialization
                    if log_level is not None:
                        logging.getLogger(__name__).info(
                            f"Changed LOG_LEVEL to: {new_level} for logger name: {logger.name}"
                        )

    except AttributeError:
        logging.getLogger(__name__).error(f"Wrong LOG_LEVEL value: {new_level} in given config file: {file_path}")
        return log_level
    return new_level


def refresh_logger(file_path, log_level=None, interval=30, loop=None, use_async=True) -> None:  # noqa: ANN001
    """
    Dynamically refreshes logger with information from given config file
    :param file_path: location of config file for logger, defined in the config map
    :param log_level: currently used log_level (taken from config map)
    :param interval: time of periodical refresh for the logger
    :param loop: asynchronous loop to perform refresh
    :param use_async: whether to use asyncio for scheduling refresh task (if not then threading)
    """
    if use_async:
        if not loop:
            loop = asyncio.get_event_loop()
        new_level = _refresh(file_path, log_level)
        loop.call_later(interval, refresh_logger, file_path, new_level, interval, loop, use_async)
    else:
        while True:
            log_level = _refresh(file_path, log_level)
            time.sleep(interval)


def initialize_logger(package_name: str, use_async: bool = True, logging_format: str | None = None) -> logging.Logger:
    """
    Initialize logger and provide periodical dynamic refresh for its configuration
    :param package_name: given name of package for the logger
    :param use_async: whether to use asyncio for scheduling refresh task (if not then threading)
    :param logging_format: optional, logging format to use instead of the default one
    :return: initialized logger
    """
    logging_config_dir = os.getenv("LOGGING_CONFIG_DIR", DEFAULT_CONFIG_DIR)
    config_filepath = f"{logging_config_dir}/{DEFAULT_CONFIG_FILE}"
    if logging_format is None:
        logging_format = get_logging_format()
    logging.basicConfig(level=logging.INFO, format=logging_format, datefmt=LOGGER_DATE_FORMAT, force=True)

    if use_async:
        loop = asyncio.get_event_loop()
        loop.call_soon(refresh_logger, config_filepath)
    else:
        # initial blocking refresh for setting first logging level before app start
        _refresh(config_filepath)
        refresh_thread = Thread(
            target=refresh_logger,
            args=(config_filepath,),
            kwargs={"use_async": use_async},
            daemon=True,
        )
        refresh_thread.start()
    return logging.getLogger(package_name)
