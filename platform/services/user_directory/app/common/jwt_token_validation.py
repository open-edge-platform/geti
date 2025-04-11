"""
Module for operations related to JWT token validation.
"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

import jwt.exceptions
from service_connection.k8s_client.secrets import get_secrets

from users_handler.exceptions import WrongUserToken
from users_handler.users_handler import UsersHandler, UserType

from common.errors import BadTokenError
from config import JWT_SECRET

logger = logging.getLogger(__name__)


def verify_jwt_token(handler: UsersHandler, token: str) -> UserType:
    """
    Wraps UsersHandler token verification with common list of exceptions which should return
    common error (e.g. 'bad request') from the API
    """
    try:
        secret = get_secrets(
            name=JWT_SECRET,
            secrets_list=["key"],
        )["key"]
        user = handler.verify_jwt_token(token, secret)
    except (
        jwt.exceptions.ExpiredSignatureError,
        jwt.exceptions.DecodeError,
        jwt.DecodeError,
        jwt.exceptions.InvalidTokenError,
        WrongUserToken,
    ) as ex:
        logger.exception("error during token verification")
        raise BadTokenError from ex

    return user
