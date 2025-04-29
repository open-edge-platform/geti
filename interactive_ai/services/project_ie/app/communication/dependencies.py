# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
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
