# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from __future__ import annotations

from typing import Protocol

from geti_logger_tools.logger_config import initialize_logger
from models.statuses import Status

logger = initialize_logger(__name__)


class AccountServiceRepoInterface(Protocol):
    async def update(self, model: AccountServiceModel, modified_by: str) -> None:
        raise NotImplementedError

    async def get(self, id_: str) -> AccountServiceModel | None:
        raise NotImplementedError


class ModelUpdateError(Exception):
    """
    Thrown when update of an model fails.
    """


class AccountServiceModel:
    repo: AccountServiceRepoInterface | None = None

    _REPO_NOT_PROVIDED_MSG = "repo object has to be passed as class variable before initialization"

    def __init__(self, id_: str, status: Status) -> None:
        self.id_ = id_
        self.status = status
        if not self.repo:
            raise ValueError(self._REPO_NOT_PROVIDED_MSG)

    def __str__(self) -> str:
        return f"{self.__class__.__name__} {self.id_} [status: {self.status}]"

    def is_registered(self) -> bool:
        """
        Check if current status is REGISTERED.
        """
        return self.status == Status.REGISTERED

    async def set_as_active(self, modified_by: str) -> None:
        """
        Idempotent method for setting active state
        """
        if self.status == Status.ACTIVE:
            return
        self.status = Status.ACTIVE
        await self.update(modified_by=modified_by)

    async def set_as_registered(self, modified_by: str) -> None:
        """
        Idempotent method for setting registered state
        """
        if self.status == Status.REGISTERED:
            return
        self.status = Status.REGISTERED
        await self.update(modified_by=modified_by)

    async def update(self, modified_by: str) -> None:
        """
        Update state in backend repo.
        """
        try:
            await self.repo.update(self, modified_by=modified_by)  # type: ignore
        except Exception as ex:
            raise ModelUpdateError(f"Failed to update {self.__class__.__name__}: {self}") from ex

    @classmethod
    async def get(cls, id_: str) -> AccountServiceModel | None:
        """
        Get model from backend repo.
        """
        if not cls.repo:
            raise ValueError(cls._REPO_NOT_PROVIDED_MSG)
        return await cls.repo.get(id_)
