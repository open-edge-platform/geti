# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from __future__ import annotations

from typing import TYPE_CHECKING

from geti_logger_tools.logger_config import initialize_logger
from models.account_service_model import AccountServiceModel, AccountServiceRepoInterface

if TYPE_CHECKING:
    from grpc_interfaces.account_service.pb.organization_pb2 import OrganizationData

    from models.statuses import Status

logger = initialize_logger(__name__)


class OrganizationRepoInterface(AccountServiceRepoInterface):
    async def update(self, organization: Organization) -> None:
        pass

    async def get(self, id_: str) -> Organization | None:
        pass

    async def create(self, organization_name: str, status: str, request_access_reason: str) -> OrganizationData | None:
        pass


class Organization(AccountServiceModel):
    """
    Organization model.
    Provide repo class variable before initialization.
    """

    repo: OrganizationRepoInterface | None = None

    def __init__(self, id_: str, status: Status, cell_id: str, name: str) -> None:
        super().__init__(id_=id_, status=status)
        self.cell_id = cell_id
        self.name = name

    @classmethod
    async def create(cls, organization_name: str, status: str, request_access_reason: str) -> OrganizationData | None:
        """
        Create organization with name and status
        """
        if not cls.repo:
            raise ValueError(cls._REPO_NOT_PROVIDED_MSG)
        return await cls.repo.create(
            organization_name=organization_name, status=status, request_access_reason=request_access_reason
        )
