# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from __future__ import annotations

from typing import TYPE_CHECKING

from geti_logger_tools.logger_config import initialize_logger
from models.account_service_model import AccountServiceModel, AccountServiceRepoInterface

if TYPE_CHECKING:
    from grpc_interfaces.account_service.pb.organization_pb2 import OrganizationData
    from grpc_interfaces.account_service.pb.workspace_pb2 import WorkspaceData


logger = initialize_logger(__name__)


class WorkspaceRepoInterface(AccountServiceRepoInterface):
    async def update(self, workspace: Workspace) -> None:
        pass

    async def get(self, id_: str) -> Workspace | None:
        pass

    async def create(self, organization: OrganizationData) -> WorkspaceData | None:
        pass

    async def get_by_organization_id(self, organization_id: str) -> WorkspaceData | None:
        pass


class Workspace(AccountServiceModel):
    """
    Workspace model.
    Provide repo class variable before initialization.
    """

    repo: WorkspaceRepoInterface | None = None

    def __init__(self, id_: str, name: str, organization_id: str) -> None:
        super().__init__(id_)
        self.name = name
        self.organization_id = organization_id

    @classmethod
    async def create(cls, organization: OrganizationData) -> WorkspaceData | None:
        """
        Create workspace linked to organization by id
        """
        if not cls.repo:
            raise ValueError(cls._REPO_NOT_PROVIDED_MSG)
        return await cls.repo.create(organization=organization)

    @classmethod
    async def get_by_organization_id(cls, organization_id: str) -> WorkspaceData | None:
        """
        Find organization's workspace
        """
        if not cls.repo:
            raise ValueError(cls._REPO_NOT_PROVIDED_MSG)
        return await cls.repo.get_by_organization_id(organization_id=organization_id)
