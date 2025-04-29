# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Quota module
"""

import logging
import os

from cachetools import TTLCache, cached
from cachetools.keys import hashkey

from geti_types import ID
from grpc_interfaces.credit_system.client import CreditSystemClient

logger = logging.getLogger(__name__)

ORGANIZATION_QUOTA_CACHE_TTL = int(os.environ.get("ORGANIZATION_QUOTA_CACHE_TTL", 3600))


@cached(
    cache=TTLCache(maxsize=100, ttl=ORGANIZATION_QUOTA_CACHE_TTL),
    key=lambda organization_id: hashkey(organization_id),
)
def get_organization_job_quota(organization_id: ID) -> int:
    """
    Fetches information about organization job quota
    :param organization_id: ID of the organization to get quota for
    :return: quota, the number of jobs which can run simultaneously
    """
    logger.info(f"Getting organization {organization_id} job quota")
    with CreditSystemClient(metadata_getter=lambda: ()) as client:
        quota = client.get_jobs_quota(organization_id=str(organization_id))
    logger.info(f"Received organization {organization_id} job quota: {quota}")
    return quota
