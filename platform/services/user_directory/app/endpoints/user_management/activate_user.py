# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import base64
import logging
from http import HTTPStatus

import jwt
from fastapi.responses import PlainTextResponse
from grpc_interfaces.account_service.pb.organization_pb2 import FindOrganizationRequest
from grpc_interfaces.account_service.pb.user_common_pb2 import UserData
from grpc_interfaces.account_service.pb.user_pb2 import FindUserRequest
from opentelemetry import trace  # type: ignore[attr-defined]
from pydantic import BaseModel
from service_connection.k8s_client.secrets import get_secrets

from endpoints.user_management.router import users_router
from users_handler.exceptions import UserDoesNotExist, WeakPassword, WrongUserToken
from users_handler.user_type import UserType
from users_handler.users_handler import UsersHandler
from users_handler.validation import validate_user_input

from common.account_service import AccountServiceConnection
from common.endpoint_logger import EndpointLogger
from common.errors import BadTokenError
from config import AUTH_CONFIG, JWT_SECRET

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class ActivateData(BaseModel):
    first_name: str
    second_name: str
    password: str
    token: str


@users_router.post(
    "/confirm_registration",
    responses={
        HTTPStatus.OK.value: {"description": "User has been successfully activated."},
        HTTPStatus.BAD_REQUEST.value: {"description": HTTPStatus.BAD_REQUEST.description},
        HTTPStatus.NOT_FOUND.value: {"description": HTTPStatus.NOT_FOUND.description},
        HTTPStatus.UNAUTHORIZED.value: {"description": HTTPStatus.UNAUTHORIZED.description},
        HTTPStatus.INTERNAL_SERVER_ERROR.value: {"description": HTTPStatus.INTERNAL_SERVER_ERROR.description},
    },
)
@EndpointLogger.extended_logging
async def activate(data: ActivateData) -> PlainTextResponse:  # noqa: D103
    account_service = AccountServiceConnection()
    handler = UsersHandler(**AUTH_CONFIG)
    user_data = None
    rollback_password = None
    try:
        with tracer.start_as_current_span("input-validation"):
            try:
                validate_user_input(
                    {"password": data.password, "first_name": data.first_name, "second_name": data.second_name}
                )
            except ValueError as err:
                return PlainTextResponse(str(err), status_code=HTTPStatus.BAD_REQUEST)
            handler.check_password_strength(data.password)
        with tracer.start_as_current_span("verify-jwt-token"):
            user = verify_payload(handler, data.token)
        if user["mail"]:
            rollback_user = account_service.client.user_stub.find(FindUserRequest(email=user["mail"]))
            user_data = next(i for i in rollback_user.users if i.email == user["mail"])
            organization_list = account_service.get_organization(FindOrganizationRequest())
            find_user = {"email": user["mail"], "organization_id": organization_list.organizations[0].id}
        else:
            raise UserDoesNotExist
        rollback_password = handler.get_password(user["uid"])
        modified_user = UserData(
            **find_user, first_name=data.first_name, second_name=data.second_name, id=user_data.id, status="ACT"
        )
        account_service.client.user_stub.modify(modified_user)
        handler.change_user_password(user["uid"], data.password)
        handler.edit_user(user["uid"], email_token="")
        return PlainTextResponse(status_code=HTTPStatus.OK)
    except BadTokenError:
        return PlainTextResponse("Unauthorized", status_code=HTTPStatus.UNAUTHORIZED)
    except (UserDoesNotExist, WrongUserToken, StopIteration):
        return PlainTextResponse("Not found", status_code=HTTPStatus.NOT_FOUND)
    except WeakPassword:
        return PlainTextResponse(
            "Specified password does not meet minimal requirements", status_code=HTTPStatus.BAD_REQUEST
        )
    except Exception:
        if user_data and rollback_password:
            rollback_user = UserData(
                **find_user, first_name=data.first_name, second_name=data.second_name, id=user_data.id, status="RGS"
            )
            account_service.client.user_stub.modify(rollback_user)
            handler.change_user_password(user["uid"], base64.urlsafe_b64encode(rollback_password.encode()).decode())
            handler.edit_user(user["uid"], email_token=data.token)
        return PlainTextResponse("Error during activation, rollback", status_code=HTTPStatus.INTERNAL_SERVER_ERROR)


def verify_payload(handler: UsersHandler, token: str) -> UserType:
    """
    Wraps UsersHandler token verification with common list of exceptions which should return
    common error (e.g. 'bad request') from the API
    """
    try:
        secret = get_secrets(
            name=JWT_SECRET,
            secrets_list=["key"],
        )["key"]
        logger.debug(f"secret {secret}")
        unsafe_uid = jwt.decode(
            jwt=token,
            algorithms=[UsersHandler.JWT_ALGORITHM],
            options={"verify_signature": False, "verify_exp": True},
        ).get("mail", "")
        validate_user_input({"user_id": unsafe_uid})
        if not unsafe_uid:
            raise BadTokenError
        payload = jwt.decode(
            jwt=token,
            key=secret,
            algorithms=[UsersHandler.JWT_ALGORITHM],
            options={"verify_signature": True, "verify_exp": True},
        )
        uid = payload["mail"]
        user = handler.get_user(uid)
        if user.get("email_token") != token:
            raise WrongUserToken
        if not user["registered"]:
            raise UserDoesNotExist
        return user
    except (
        jwt.exceptions.ExpiredSignatureError,
        jwt.exceptions.DecodeError,
        jwt.DecodeError,
        jwt.exceptions.InvalidTokenError,
    ) as ex:
        logger.exception("error during token verification")
        raise BadTokenError from ex
