"""
Simple utils shared across multiple modules
"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import json
import logging
import os
import tarfile
import time
from functools import lru_cache, wraps

import requests

import config

logger = logging.getLogger(__name__)

DEFAULT_ORGANIZATION_ID = "000000000000000000000001"
DEFAULT_WORKSPACE_NAME = "Default Workspace"
API_BASE_PATTERN = "/api/v1"


def timed_lru_cache(_func=None, *, seconds: int = 5, maxsize: int = 128, typed: bool = False):  # noqa: ANN001, ANN201
    """Timed LRU cache"""

    def wrapper_cache(func):  # noqa: ANN001
        func = lru_cache(maxsize=maxsize, typed=typed)(func)
        func.delta = seconds * 10**9
        func.expiration = time.monotonic_ns() + func.delta

        @wraps(func)
        def wrapped_func(*args, **kwargs):
            if time.monotonic_ns() >= func.expiration:
                func.cache_clear()
                func.expiration = time.monotonic_ns() + func.delta
            return func(*args, **kwargs)

        wrapped_func.cache_info = func.cache_info
        wrapped_func.cache_clear = func.cache_clear
        return wrapped_func

    if _func is None:
        return wrapper_cache
    return wrapper_cache(_func)


def make_tarfile(output_filename: str, paths: list[str]):  # noqa: ANN201
    """Creates a .tar.gz archive
    :param output_filename: Contains full path with the file name where archive will be stored
    :param paths: Paths to the files/directories that will be added to the archive
    """
    logger.debug(f"Creating {output_filename} archive")
    with tarfile.open(name=output_filename, mode="w:gz", format=tarfile.PAX_FORMAT, compresslevel=1) as tar:
        for path in paths:
            logger.debug(f"Adding {path} to the {output_filename} archive")
            tar.add(path, arcname=os.path.basename(path))
    logger.debug("All files have been added to the archive")


@timed_lru_cache(seconds=86400)
def get_default_workspace_id(organization_id: str = DEFAULT_ORGANIZATION_ID) -> str:
    """
    Send request to /api/v1/workspaces to get id of default workspace
    """
    organization_id_url_part = f"/organizations/{organization_id}"
    workspaces_url = f"http://{config.IMPT_RESOURCE_SERVICE_HOST}:{config.IMPT_RESOURCE_SERVICE_PORT}{API_BASE_PATTERN}{organization_id_url_part}/workspaces"
    headers = {"content-type": "application/json"}
    workspaces = json.loads(requests.get(url=workspaces_url, headers=headers, timeout=(2.0, 2.0)).text)
    for workspace in workspaces["workspaces"]:
        if workspace["name"] == DEFAULT_WORKSPACE_NAME:
            return workspace["id"]
    raise ValueError(f"{DEFAULT_WORKSPACE_NAME} does not exist.")
