# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import base64
import json
import os
from datetime import date, datetime, timezone
from typing import Annotated

import boto3
import jwt
from botocore.exceptions import ClientError
from fastapi import Header, HTTPException, status
from pydantic import BaseModel, Field

from geti_logger_tools.logger_config import initialize_logger

logger = initialize_logger(__name__)

JWT_ALGORITHM = "RS256"
FIRST_NAME_FIELDS = ["given_name", "firstName"]
LAST_NAME_FIELDS = ["family_name", "lastName"]


class DecodedUserData(BaseModel):
    email: str
    sub: str
    first_name: str
    last_name: str
    country_code: str | None = Field(None)
    is_intel_employee: bool = False


def lookup_jwt_fields(decoded_token: dict, fields: list[str]) -> str:
    """
    Find value of jwt token field under provided list of fields.
    """
    for field in fields:
        if field_value := decoded_token.get(field):
            return field_value
    raise ValueError(f"Unable to find {fields=} in {decoded_token=}")


async def parse_internal_jwt_token(x_auth_request_access_token: Annotated[str, Header()]) -> DecodedUserData:
    """
    Parse internal JWT token passed in the request and return UserData from decoded token.
    """
    try:
        decoded_token: dict = jwt.decode(
            x_auth_request_access_token,
            algorithms=[JWT_ALGORITHM],
            options={"verify_signature": False, "verify_exp": True},
        )
        decoded_external_token: dict = jwt.decode(
            decoded_token["external_token"],
            algorithms=[JWT_ALGORITHM],
            options={"verify_signature": False, "verify_exp": True},
        )
        return DecodedUserData(
            email=decoded_external_token["email"],
            sub=decoded_external_token["sub"],
            first_name=lookup_jwt_fields(decoded_external_token, FIRST_NAME_FIELDS),
            last_name=lookup_jwt_fields(decoded_external_token, LAST_NAME_FIELDS),
            country_code=decoded_external_token.get("countryCode"),
            is_intel_employee=decoded_external_token.get("isInternal", False),
        )
    except Exception:
        logger.exception("Failed to parse internal JWT token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


class OnboardingTokenService:
    """
    Class responsible for generating and verifying onboarding JWTs using AWS KMS.
    """

    def __init__(self):
        self.initialized = False

    @staticmethod
    def _base64_url_encode(data: bytes) -> bytes:
        """
        Encode data using base64 URL-safe encoding.
        """
        return base64.urlsafe_b64encode(data).rstrip(b"=")

    @staticmethod
    def _base64_url_decode(data: bytes) -> bytes:
        """
        Decode data using base64 URL-safe decoding.
        """
        return base64.urlsafe_b64decode(data + b"=" * (4 - len(data) % 4))

    def build_onboarding_token(self, date_from: date, date_to: date) -> str:
        """
        Build signed Onboarding Invitation Token using AWS KMS.
        """
        self._lazy_init()
        claims = {
            "iat": datetime.now(tz=timezone.utc).timestamp(),
            "nbf": datetime.combine(date=date_from, time=datetime.min.time(), tzinfo=timezone.utc).timestamp(),
            "exp": datetime.combine(date=date_to, time=datetime.max.time(), tzinfo=timezone.utc).timestamp(),
        }
        payload = json.dumps(claims).encode("utf8")
        payload_b64 = self._base64_url_encode(payload)

        header = {"typ": "JWT", "alg": self.jwt_algorithm, "kid": self._kms_key_id}
        header_json = json.dumps(header).encode("utf8")
        header_b64 = self._base64_url_encode(header_json)

        message = header_b64 + b"." + payload_b64

        try:
            mac_response = self.kms_client.generate_mac(
                KeyId=self._kms_key_id, MacAlgorithm=self.mac_algorithm, Message=message
            )
        except ClientError as e:
            logger.exception(f"Failed to generate MAC using AWS KMS: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        mac_b64 = self._base64_url_encode(mac_response["Mac"])
        jwt_token = message + b"." + mac_b64
        return jwt_token.decode("utf-8")

    def validate_onboarding_token(self, token: str) -> None:
        """
        Validates onboarding invitation token using AWS KMS.
        """
        self._lazy_init()
        try:
            message, mac_b64 = token.rsplit(".", 1)
            header_b64, payload_b64 = message.rsplit(".", 1)

            header_map = json.loads(self._base64_url_decode(header_b64.encode("utf-8")).decode("utf8"))
            if (
                header_map["typ"] != "JWT"
                or header_map["alg"] != self.jwt_algorithm
                or header_map["kid"] != self._kms_key_id
            ):
                raise ValueError("Onboarding token header does not match expected values")

            self.kms_client.verify_mac(
                KeyId=self._kms_key_id,
                MacAlgorithm=self.mac_algorithm,
                Message=message.encode("utf-8"),
                Mac=self._base64_url_decode(mac_b64.encode("utf-8")),
            )

            payload_map = json.loads(self._base64_url_decode(payload_b64.encode("utf-8")).decode("utf8"))
            current_timestamp = datetime.now(tz=timezone.utc).timestamp()
            if current_timestamp < payload_map["nbf"]:
                raise ValueError("Onboarding token is not valid yet")
            if current_timestamp > payload_map["exp"]:
                raise ValueError("Onboarding token is expired")

        except ValueError as e:
            logger.exception(f"Onboarding token validation error: {e}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid sign-up token")
        except ClientError as e:
            logger.exception(f"Onboarding token verification using AWS KMS failed: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _lazy_init(self) -> None:
        if self.initialized:
            return
        self.initialized = True
        try:
            self._kms_key_id = os.environ["KMS_KEY_ALIAS"]
        except KeyError:
            raise RuntimeError("Invalid configuration - KMS key ID for token signing is not set")
        self.kms_client = boto3.client("kms")
        self.mac_algorithm = "HMAC_SHA_512"
        self.jwt_algorithm = "HS512"
