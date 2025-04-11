# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from __future__ import annotations

from typing import TYPE_CHECKING

from geti_logger_tools.logger_config import initialize_logger
from models.account_service_model import AccountServiceModel, AccountServiceRepoInterface

if TYPE_CHECKING:
    from grpc_interfaces.account_service.pb.user_common_pb2 import UserData
    from grpc_interfaces.account_service.pb.user_pb2 import UserProfileData

    from models.statuses import Status

logger = initialize_logger(__name__)


class UserRepoInterface(AccountServiceRepoInterface):
    async def update(self, user: User) -> None:
        pass

    async def get(self, id_: str) -> User | None:
        pass

    async def get_user_by_email(self, email: str, organization_id: str) -> User | None:
        pass

    async def get_user_profile(self, token: str) -> UserProfileData | None:
        pass

    async def create(self, user_data: UserData) -> None:
        pass

    async def set_roles(self, user_id: str, organization_id: str, roles: list) -> None:
        pass


class User(AccountServiceModel):
    """
    User model.
    Provide repo class variable before initialization.
    """

    repo: UserRepoInterface | None = None

    def __init__(  # noqa: PLR0913
        self,
        id_: str,
        first_name: str,
        second_name: str,
        email: str,
        status: Status,
        organization_id: str | None = None,
        user_consent: str | None = None,
        telemetry_consent: str | None = None,
        external_id: str | None = None,
    ) -> None:
        super().__init__(id_, status)
        self.first_name = first_name
        self.second_name = second_name
        self.email = email
        self.organization_id = organization_id
        self.user_consent = user_consent
        self.telemetry_consent = telemetry_consent
        self.external_id = external_id

    @classmethod
    async def get_by_email(cls, email: str, organization_id: str) -> User | None:
        """
        Get User from backend repo by email.
        """
        if not cls.repo:
            raise ValueError(cls._REPO_NOT_PROVIDED_MSG)
        return await cls.repo.get_user_by_email(email=email, organization_id=organization_id)

    @classmethod
    async def get_user_profile(cls, token: str) -> UserProfileData | None:
        """
        Get User profile with token
        """
        if not cls.repo:
            raise ValueError(cls._REPO_NOT_PROVIDED_MSG)
        return await cls.repo.get_user_profile(token=token)

    @classmethod
    async def create(cls, user_data: UserData) -> None:
        """
        Create user with status ACT
        """
        if not cls.repo:
            raise ValueError(cls._REPO_NOT_PROVIDED_MSG)
        return await cls.repo.create(user_data=user_data)

    @classmethod
    async def set_roles(cls, user_id: str, organization_id: str, roles: list) -> None:
        """
        Set roles for user
        """
        if not cls.repo:
            raise ValueError(cls._REPO_NOT_PROVIDED_MSG)
        return await cls.repo.set_roles(user_id=user_id, organization_id=organization_id, roles=roles)
