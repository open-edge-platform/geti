# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
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

from behave import then
from behave.runner import Context
from geti_client import ApiException


@then("the request is rejected")
def step_then_request_rejected(context: Context) -> None:
    """Verifies that the request raises an exception"""
    if not hasattr(context, "exception"):
        assert False, "The previous step did not raise an error, or it wasn't captured into the context"

    if not isinstance(context.exception, ApiException):
        assert False, "An error occurred during the previous step, but it does not originate from the API request"

    assert 400 <= context.exception.status < 500, (
        f"The request did not return a client error (4xx status code); exception {context.exception}"
    )
