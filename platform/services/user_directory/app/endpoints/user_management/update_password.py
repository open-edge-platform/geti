"""
password update endpoint
"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from http import HTTPStatus

from fastapi import Header
from fastapi.responses import PlainTextResponse
from opentelemetry import trace  # type: ignore[attr-defined]
from pydantic import BaseModel

from endpoints.user_management.router import users_router
from users_handler.exceptions import UserDoesNotExist
from users_handler.validation import is_base64, validate_user_input

from common.endpoint_logger import EndpointLogger
from common.errors import ErrorMessages, GeneralError, ResponseError
from common.interfaces.payload_error import ResponseException
from common.users import get_user_from_header, update_password

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class PasswordUpdateData(BaseModel):
    new_password: str
    old_password: str


@users_router.post(
    "/{user_id}/update_password",
    responses={
        HTTPStatus.BAD_REQUEST.value: {"description": HTTPStatus.BAD_REQUEST.description},
        HTTPStatus.UNAUTHORIZED.value: {"description": HTTPStatus.UNAUTHORIZED.description},
        HTTPStatus.OK.value: {"description": HTTPStatus.OK.description},
    },
    response_class=PlainTextResponse,
)
@EndpointLogger.extended_logging
async def update_user_password(  # noqa: ANN201, PLR0911
    user_id: str,
    body: PasswordUpdateData,
    x_auth_request_access_token: str | None = Header(default=None, include_in_schema=False),
):
    """
    /users/[user_id]/update_password handler
    """
    try:
        old_password, new_password = body.old_password, body.new_password
        if not (is_base64(old_password) and is_base64(new_password)):
            return PlainTextResponse(content="Wrong password format", status_code=HTTPStatus.BAD_REQUEST)
        with tracer.start_as_current_span("validate-inputs"):
            validate_user_input({"user_id": user_id})
            validate_user_input({"password": new_password})
        with tracer.start_as_current_span("validate-user-logged-in"):
            validate_user_logged_in(x_auth_request_access_token, user_id)

        with tracer.start_as_current_span("update-password"):
            update_password(uid=user_id, old_password=old_password, new_password=new_password)

    except ValueError as err:
        return PlainTextResponse(content=str(err), status_code=HTTPStatus.BAD_REQUEST)
    except ResponseError:
        return PlainTextResponse(content="Unauthorized", status_code=HTTPStatus.UNAUTHORIZED)
    except UserDoesNotExist:
        return PlainTextResponse(content=ErrorMessages.USER_NOT_FOUND, status_code=HTTPStatus.NOT_FOUND)
    except ResponseException as ex:
        if ex.error_code == GeneralError.SAME_NEW_PASSWORD.name:
            return PlainTextResponse(ErrorMessages.SAME_NEW_PASSWORD, status_code=HTTPStatus.CONFLICT)
        if ex.error_code == GeneralError.WRONG_OLD_PASSWORD.name:
            return PlainTextResponse(ErrorMessages.WRONG_OLD_PASSWORD, status_code=HTTPStatus.BAD_REQUEST)
        if ex.error_code == GeneralError.WEAK_PASSWORD.name:
            return PlainTextResponse(ErrorMessages.WEAK_PASSWORD, status_code=HTTPStatus.BAD_REQUEST)
        if ex.error_code in (GeneralError.INVALID_INPUT.name, GeneralError.ELEMENT_NOT_FOUND.name):
            return PlainTextResponse("Wrong input", status_code=HTTPStatus.BAD_REQUEST)

    return PlainTextResponse(content="Password has been updated", status_code=HTTPStatus.OK)


def validate_user_logged_in(x_auth_request_access_token: str | None, user_id):  # noqa: ANN001, ANN201, D103
    active_user = get_user_from_header(x_auth_request_access_token)
    if active_user["uid"] != user_id:
        raise ResponseError("Unauthorized", status_code=HTTPStatus.UNAUTHORIZED)
