# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

import abc
from collections.abc import Generator, Sequence

from pymongo.client_session import ClientSession
from pymongo.collation import Collation
from pymongo.command_cursor import CommandCursor

from sc_sdk.repos.base import PersistedEntityT, SessionBasedRepo
from sc_sdk.repos.mappers import CursorIterator

from geti_types import ID


class BackwardCompatibilitySessionRepo(SessionBasedRepo[PersistedEntityT], metaclass=abc.ABCMeta):
    """
    Interface of a backward-compatible class for session-based repositories.
    This class is particularly useful when migrating documents from collection A to collection B.
    It ensures that data is read from repository A and written to both repositories A and B, thereby maintaining
    backward compatibility during the migration period.
    """

    @property
    @abc.abstractmethod
    def backward_compatibility_repo_adapter(self) -> SessionBasedRepo:
        """Returns the backward compatibility repo adapter instance"""

    def save(
        self,
        instance: PersistedEntityT,
        mongodb_session: ClientSession | None = None,
    ) -> None:
        # save on both new and backward compatibility repo
        self.backward_compatibility_repo_adapter.save(instance, mongodb_session)
        super().save(instance, mongodb_session)

    def save_many(
        self,
        instances: Sequence[PersistedEntityT],
        mongodb_session: ClientSession | None = None,
    ) -> None:
        # save on both new and backward compatibility repo
        self.backward_compatibility_repo_adapter.save_many(instances, mongodb_session)
        super().save_many(instances, mongodb_session)

    def get_by_id(self, id_: ID) -> PersistedEntityT:
        # read only from backward compatibility repo
        return self.backward_compatibility_repo_adapter.get_by_id(id_)

    def get_one(
        self,
        extra_filter: dict | None = None,
        latest: bool = False,
        earliest: bool = False,
        sort_by: str | None = None,
    ) -> PersistedEntityT:
        # read only from backward compatibility repo
        return self.backward_compatibility_repo_adapter.get_one(
            extra_filter=extra_filter, latest=latest, earliest=earliest, sort_by=sort_by
        )

    def get_all(
        self, extra_filter: dict | None = None, sort_info: list | None = None
    ) -> CursorIterator[PersistedEntityT]:
        # read only from backward compatibility repo
        return self.backward_compatibility_repo_adapter.get_all(extra_filter=extra_filter, sort_info=sort_info)

    def get_all_ids(self, extra_filter: dict | None = None) -> Generator[ID, None, None]:
        # read only from backward compatibility repo
        return self.backward_compatibility_repo_adapter.get_all_ids(extra_filter=extra_filter)

    def distinct(self, key: str, extra_filter: dict | None = None) -> tuple:
        # read only from backward compatibility repo
        return self.backward_compatibility_repo_adapter.distinct(key, extra_filter=extra_filter)

    def count(self, extra_filter: dict | None = None) -> int:
        # read only from backward compatibility repo
        return self.backward_compatibility_repo_adapter.count(extra_filter=extra_filter)

    def delete_by_id(self, id_: ID) -> bool:
        # delete from both new and backward compatibility repo
        self.backward_compatibility_repo_adapter.delete_by_id(id_)
        return super().delete_by_id(id_)

    def delete_all(self, extra_filter: dict | None = None) -> bool:
        # delete from both new and backward compatibility repo
        self.backward_compatibility_repo_adapter.delete_all(extra_filter)
        return super().delete_all(extra_filter)

    def exists(self, id_: ID) -> bool:
        # read only from backward compatibility repo
        return self.backward_compatibility_repo_adapter.exists(id_)

    def aggregate_read(self, pipeline: list[dict], collation: Collation | None = None) -> CommandCursor:
        raise NotImplementedError("Aggregate pipelines are not supported in backward compatibility repositories")

    def aggregate_write(self, pipeline: list[dict], collation: Collation | None = None) -> CommandCursor:
        raise NotImplementedError("Aggregate pipelines are not supported in backward compatibility repositories")
