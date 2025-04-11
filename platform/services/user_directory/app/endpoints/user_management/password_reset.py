# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
A module containing endpoints responsible for user's password reset
"""

import json
import logging
import os
from http import HTTPStatus
from typing import Annotated

from fastapi import Header, Request
from fastapi.responses import PlainTextResponse, RedirectResponse, Response
from jwt.exceptions import ExpiredSignatureError
from opentelemetry import trace  # type: ignore[attr-defined]
from pydantic import BaseModel, Field
from service_connection.k8s_client.config_maps import get_config_map
from service_connection.k8s_client.secrets import get_secrets
from service_connection.kafka import send_message
from service_connection.smtp_client import EmailTemplates, SMTPClient

from endpoints.user_management.router import users_router
from users_handler.exceptions import InvalidEmail, UserDoesNotExist
from users_handler.users_handler import UsersHandler, UserType
from users_handler.validation import MAX_INPUT_LENGTH, is_base64, validate_user_input

from common.endpoint_logger import EndpointLogger
from common.errors import BadTokenError, ErrorMessages, GeneralError
from common.interfaces.payload_error import ResponseException
from common.jwt_token_validation import verify_jwt_token
from common.users import get_user_by_email, update_password
from config import AUTH_CONFIG, IMPT_CONFIGURATION_CM, JWT_SECRET

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class PasswordRequestResetData(BaseModel):
    """Stores email on which new password will be sent"""

    email: str = Field(max_length=MAX_INPUT_LENGTH)


class PasswordResetData(BaseModel):
    """Stores user's new password and token"""

    new_password: str
    token: str


def _send_password_reset_email(user: UserType, exp_period_in_min: int, server_address: str):
    users_handler = UsersHandler(**AUTH_CONFIG)
    secret = get_secrets(
        name=JWT_SECRET,
        secrets_list=["key"],
    )["key"]
    token = users_handler.generate_jwt_token(
        uid=user["uid"],
        mail=user["mail"],
        exp_period_in_min=exp_period_in_min,
        secret=secret,
    )
    reset_link = f"https://{server_address}/confirm-action/registration/reset-password?token={token}"
    template_vars = {"resetLink": reset_link}

    topic, message = SMTPClient._render_template(
        template=EmailTemplates.PASSWORD_RESET.value, template_vars=template_vars
    )

    email_message = {
        "subject": topic,
        "to": user["mail"],
        "from_address": os.environ.get("INVITATION_FROM_ADDRESS", "no-reply@geti.intel.com"),
        "from_name": os.environ.get("INVITATION_FROM_NAME", "Intel Geti"),
        "content": "",
        "html_content": message,
    }
    send_message(json.dumps(email_message))


@users_router.post(
    "/request_password_reset",
    status_code=HTTPStatus.ACCEPTED,
    responses={
        HTTPStatus.ACCEPTED.value: {"description": "Password reset request sent."},
        HTTPStatus.BAD_REQUEST.value: {"description": "SMTP Server not configured."},
        HTTPStatus.NOT_FOUND.value: {"description": "User does not exist."},
        HTTPStatus.UNPROCESSABLE_ENTITY.value: {"description": ErrorMessages.INVALID_EMAIL},
    },
)
@EndpointLogger.extended_logging
async def request_password_reset(  # noqa: ANN201
    user_data: PasswordRequestResetData, host: Annotated[str | None, Header()] = None
):
    """
    Request password endpoint on /users/request_password_reset"
    :param user_data: data payload containing user's email address.
    :param host: 'Host' header value in request
    """
    server_address = host if host else "intel.com"
    try:
        UsersHandler.is_email_valid(user_data.email)
    except InvalidEmail as msg:
        logger.error(msg)
        return PlainTextResponse(ErrorMessages.INVALID_EMAIL, status_code=HTTPStatus.UNPROCESSABLE_ENTITY)

    with tracer.start_as_current_span("get-expiration-time-from-cm"):
        try:
            exp_period_in_min = int(
                get_config_map(name=IMPT_CONFIGURATION_CM, field_list=["password_reset_expiration"])[
                    "password_reset_expiration"
                ]
            )
        except KeyError:
            return PlainTextResponse(ErrorMessages.SMTP_SERVER_NOT_CONFIGURED, status_code=HTTPStatus.BAD_REQUEST)

    with tracer.start_as_current_span("get-user-by-email"):
        user = await get_user_by_email(user_data.email)

    if user is None:
        logger.error(f"User does not exist {user_data.email}")
    else:
        _send_password_reset_email(user=user, exp_period_in_min=exp_period_in_min, server_address=server_address)

    return PlainTextResponse("Password reset request sent", status_code=HTTPStatus.ACCEPTED)


@users_router.get(
    "/registration/reset-password",
    responses={
        HTTPStatus.BAD_REQUEST.value: {"description": HTTPStatus.BAD_REQUEST.description},
        HTTPStatus.NOT_FOUND.value: {"description": HTTPStatus.NOT_FOUND.description},
        HTTPStatus.GONE.value: {"description": HTTPStatus.GONE.description},
    },
    status_code=HTTPStatus.TEMPORARY_REDIRECT,
)
@EndpointLogger.extended_logging
async def check_token_validity(token: str, request: Request, host: Annotated[str | None, Header()] = None) -> Response:
    """
    Validate token, replace it with new one and redirect to UI page.
    """
    server_address = host if host else "intel.com"
    try:
        handler = UsersHandler(**AUTH_CONFIG)
        secret = get_secrets(
            name=JWT_SECRET,
            secrets_list=["key"],
        )["key"]
        user = verify_jwt_token(handler, token)  # removes the token after successful verification
        new_token = handler.generate_replacing_jwt_token(uid=user["uid"], prev_token=token, secret=secret)
        logger.info(f"Link {request.url.path} is valid to use")
        redirect_link = f"https://{server_address}{request.url.path.replace('/api/v1/users/', '/')}?token={new_token}"
        logger.info(f"Redirecting to: {redirect_link}")
        return RedirectResponse(url=redirect_link)
    except UserDoesNotExist:
        logger.exception("User does not exist. Redirecting to error page.")
        return RedirectResponse(url=f"https://{server_address}/registration/users/not-found")
    except (ExpiredSignatureError, BadTokenError):
        logger.exception(f"Link {request['path']} has already been used or expired. Redirecting to error page.")
        return RedirectResponse(url=f"https://{server_address}/registration/invalid-link")


@users_router.post(
    "/reset_password",
    responses={
        HTTPStatus.BAD_REQUEST.value: {"description": HTTPStatus.BAD_REQUEST.description},
        HTTPStatus.UNAUTHORIZED.value: {"description": HTTPStatus.UNAUTHORIZED.description},
        HTTPStatus.NOT_FOUND.value: {"description": HTTPStatus.NOT_FOUND.description},
        HTTPStatus.OK.value: {"description": HTTPStatus.OK.description},
    },
    response_class=PlainTextResponse,
)
@EndpointLogger.extended_logging
async def reset_password(body: PasswordResetData):  # noqa: ANN201, PLR0911
    """
    /users/reset_password handler
    """
    try:
        token, new_password = body.token, body.new_password
        with tracer.start_as_current_span("input-validation"):
            if not is_base64(new_password):
                return PlainTextResponse("Wrong password format", status_code=HTTPStatus.BAD_REQUEST)
            validate_user_input({"password": new_password})

        with tracer.start_as_current_span("verify-jwt-token"):
            handler = UsersHandler(**AUTH_CONFIG)
            user = verify_jwt_token(handler, token)

        with tracer.start_as_current_span("update-password"):
            update_password(uid=user["uid"], new_password=new_password)

    except BadTokenError:
        return PlainTextResponse("Unauthorized", status_code=HTTPStatus.UNAUTHORIZED)
    except ValueError as e:
        logger.exception("Got ValueError", exc_info=e)
        return PlainTextResponse(content="Bad Request", status_code=HTTPStatus.BAD_REQUEST)
    except UserDoesNotExist:
        return PlainTextResponse(ErrorMessages.USER_NOT_FOUND, status_code=HTTPStatus.NOT_FOUND)
    except ResponseException as ex:
        if ex.error_code == GeneralError.WEAK_PASSWORD.name:
            return PlainTextResponse(ErrorMessages.WEAK_PASSWORD, status_code=HTTPStatus.BAD_REQUEST)
        if ex.error_code == GeneralError.INVALID_INPUT.name:
            return PlainTextResponse("Wrong input", status_code=HTTPStatus.BAD_REQUEST)

    return PlainTextResponse("Password was reset", status_code=HTTPStatus.OK)
