# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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

from starlette.requests import Request

from communication.http_exceptions import InvalidOperationIdException

from geti_fastapi_tools.dependencies import is_valid_id
from geti_types import ID

logger = logging.getLogger(__name__)


def get_export_operation_id(export_operation_id: str) -> ID:
    """Initializes and validates an export operation ID"""
    if not is_valid_id(export_operation_id):
        logger.info("Invalid project export operation id: %s", export_operation_id)
        raise InvalidOperationIdException(operation_id=export_operation_id)
    return ID(export_operation_id)


def get_request_domain(request: Request) -> str:
    """Extract the domain name from the request"""
    return str(request.base_url).removeprefix("http://").removeprefix("https://").replace("/", "")
