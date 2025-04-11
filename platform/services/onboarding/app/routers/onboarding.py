# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from enum import Enum
from http import HTTPStatus
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from grpc_interfaces.account_service.pb.user_common_pb2 import UserData, UserRole, UserRoleOperation
from pydantic import BaseModel, Field

from dependencies import FeatureFlag, is_feature_flag_enabled
from geti_logger_tools.logger_config import initialize_logger
from jwt_utils import DecodedUserData, OnboardingTokenService, parse_internal_jwt_token
from models.organization import Organization
from models.statuses import Status
from models.user import User
from models.workspace import Workspace

from communication.credit_system.create_subscription import create_subscription, fail_subscription
from communication.marketing_platform.register_user import register_user_in_marketing_platform

DEFAULT_PRODUCT_NAME = "Geti Free Tier"
INTERNAL_PRODUCT_NAME = "Intel Trial"

logger = initialize_logger(__name__)

router = APIRouter(prefix="/onboarding")


class OnboardingRequestBody(BaseModel):
    user_consent: str
    telemetry_consent: str
    organization_id: str
    organization_name: str | None = Field(None)
    profession: str | None = Field(None)
    onboarding_token: str | None = Field(None)
    request_access_reason: str | None = Field(None)


async def create_free_tier_user(
    onboarding_req_body: OnboardingRequestBody, user_data: DecodedUserData
) -> PlainTextResponse:
    """
    Onboard Free Tier user
    """
    if is_feature_flag_enabled(FeatureFlag.REQUIRE_INVITATION_LINK) and not user_data.is_intel_employee:
        if onboarding_req_body.onboarding_token is None:
            logger.error(f"User {user_data.email} doesn't have the onboarding token.")
            raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)

        token_svc = OnboardingTokenService()
        token_svc.validate_onboarding_token(token=onboarding_req_body.onboarding_token)
    return await create_user(onboarding_req_body, user_data, Status.ACTIVE)


async def create_user(
    onboarding_req_body: OnboardingRequestBody, user_data: DecodedUserData, status: Enum
) -> PlainTextResponse:
    """
    Create new user with organization and workspace
    """
    try:
        organization = await Organization.create(
            onboarding_req_body.organization_name, status, onboarding_req_body.request_access_reason
        )
        workspace = await Workspace.create(organization)
        new_user = await User.create(
            UserData(
                first_name=user_data.first_name,
                second_name=user_data.last_name,
                status=status.value,
                external_id=user_data.sub,
                email=user_data.email,
                organization_id=organization.id,
                telemetry_consent=onboarding_req_body.telemetry_consent,
                user_consent=onboarding_req_body.user_consent,
            )
        )
        roles = [
            {"role": "workspace_admin", "resource_id": workspace.id, "resource_type": "workspace"},
            {"role": "organization_admin", "resource_id": organization.id, "resource_type": "organization"},
        ]
        role_ops: list[UserRoleOperation] = []
        for role_op in roles:
            user_role = UserRole(
                role=role_op["role"], resource_type=role_op["resource_type"], resource_id=role_op["resource_id"]
            )
            role_operation = UserRoleOperation(role=user_role, operation="CREATE")
            role_ops.append(role_operation)
        await User.set_roles(user_id=new_user.id, organization_id=organization.id, roles=role_ops)

        if is_feature_flag_enabled(FeatureFlag.CREDIT_SYSTEM):
            await create_subscription(
                organization_id=organization.id,
                workspace_id=workspace.id,
                product_name=_resolve_product_name(user_data=user_data),
            )

        await _register_user_in_marketing_platform(
            user=new_user,
            organization_name=organization.name,
            profession=onboarding_req_body.profession,
            country_code=user_data.country_code,
        )

        return PlainTextResponse(status_code=HTTPStatus.OK)
    except Exception:
        logger.exception("Failed to onboard new user")
        return PlainTextResponse(status_code=HTTPStatus.BAD_REQUEST)


async def create_request_user(
    onboarding_req_body: OnboardingRequestBody, user_data: DecodedUserData
) -> PlainTextResponse:
    """
    Onboard Requested access user
    """
    return await create_user(onboarding_req_body, user_data, Status.REQUESTED)


async def activate_regular_user(
    organization: Organization,
    workspace: Workspace,
    user: User,
    jwt_user_data: DecodedUserData,
    onboarding_req_body: OnboardingRequestBody,
    existing_user: User,
) -> None:
    """
    Activate regular registered user
    """
    organization_registered = organization.is_registered()
    organization_id = user.organization_id
    try:
        if organization_registered:
            await organization.set_as_active(modified_by=user.id_)
            if is_feature_flag_enabled(FeatureFlag.CREDIT_SYSTEM):
                await create_subscription(
                    organization_id=organization_id,
                    workspace_id=workspace.id,
                    product_name=_resolve_product_name(user_data=jwt_user_data),
                )
        user.status = Status.ACTIVE
        user.first_name, orig_first_name = jwt_user_data.first_name, user.first_name
        user.second_name, orig_second_name = jwt_user_data.last_name, user.second_name
        user.user_consent = onboarding_req_body.user_consent
        orig_user_consent = existing_user.user_consent if existing_user else ""
        user.telemetry_consent = onboarding_req_body.telemetry_consent
        orig_telemetry_consent = existing_user.user_consent if existing_user else ""
        user.external_id, orig_external_id = jwt_user_data.sub, user.external_id
        await user.update(modified_by=user.id_)
    except Exception:
        logger.exception(
            f"Failed to onboard user {jwt_user_data.email} in organization {organization_id}, performing rollback ..."
        )
        if organization_registered:
            await organization.set_as_registered(modified_by=user.id_)
            if is_feature_flag_enabled(FeatureFlag.CREDIT_SYSTEM):
                await fail_subscription(
                    organization_id=organization_id,
                    workspace_id=workspace.id,
                    product_name=_resolve_product_name(user_data=jwt_user_data),
                )
        user.status = Status.REGISTERED
        user.first_name = orig_first_name
        user.second_name = orig_second_name
        user.user_consent = orig_user_consent
        user.telemetry_consent = orig_telemetry_consent
        user.external_id = orig_external_id
        await user.update(modified_by=user.id_)
        raise
    if not orig_user_consent:
        await _register_user_in_marketing_platform(
            user=user,
            organization_name=organization.name,
            profession=onboarding_req_body.profession,
            country_code=jwt_user_data.country_code,
        )


@router.post("/user")
async def user_onboarding(
    onboarding_req_body: OnboardingRequestBody,
    request: Request,
    jwt_user_data: DecodedUserData = Depends(parse_internal_jwt_token),  # noqa: FAST002
) -> Any:
    """
    User onboarding endpoint.
    """
    if not all([onboarding_req_body.user_consent == "y", onboarding_req_body.telemetry_consent == "y"]):
        return PlainTextResponse(status_code=HTTPStatus.BAD_REQUEST)
    existing_user = await User.get_user_profile(request.headers["x-auth-request-access-token"])

    if (
        not existing_user
        and not onboarding_req_body.onboarding_token
        and is_feature_flag_enabled(FeatureFlag.REQ_ACCESS)
    ):
        logger.info("Creating requested user")
        return await create_request_user(onboarding_req_body=onboarding_req_body, user_data=jwt_user_data)

    if (
        not onboarding_req_body.organization_id
        and onboarding_req_body.organization_name
        and not existing_user
        and is_feature_flag_enabled(FeatureFlag.FREE_TIER)
    ):
        return await create_free_tier_user(onboarding_req_body=onboarding_req_body, user_data=jwt_user_data)

    user_email = jwt_user_data.email
    user: User = await User.get_by_email(email=user_email, organization_id=onboarding_req_body.organization_id)
    if not user or not user.is_registered():
        logger.info(f"User {user_email} is not registered, or is already active")
        return PlainTextResponse(status_code=HTTPStatus.NOT_FOUND)
    organization_id = user.organization_id
    workspace = await Workspace.get_by_organization_id(organization_id)
    organization = await Organization.get(organization_id)

    await activate_regular_user(organization, workspace, user, jwt_user_data, onboarding_req_body, existing_user)

    return PlainTextResponse(status_code=HTTPStatus.OK)


async def _register_user_in_marketing_platform(
    user: User,
    organization_name: str,
    profession: str | None = None,
    country_code: str | None = None,
) -> None:
    try:
        await register_user_in_marketing_platform(
            user=user,
            organization_name=organization_name,
            profession=profession,
            country_code=country_code,
        )
    except Exception:
        logger.exception("Failed to register user in marketing platform")


def _resolve_product_name(user_data: DecodedUserData):
    """
    Product choice depends currently on whether the user is external or Intel employee.
    """
    return INTERNAL_PRODUCT_NAME if user_data.is_intel_employee else DEFAULT_PRODUCT_NAME
