# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
