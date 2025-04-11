# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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

"""This module implements the Dataset Storage entity"""

import datetime

from sc_sdk.entities.persistent_entity import PersistentEntity
from sc_sdk.utils.constants import DEFAULT_USER_NAME
from sc_sdk.utils.time_utils import now

from geti_types import CTX_SESSION_VAR, ID, DatasetStorageIdentifier


class DatasetStorage(PersistentEntity):
    """
    DatasetStorage is a container that represents a single logical dataset (meant as
    collection of media and annotations to be used for AI workflows) from the user PoV.

    :param name: Name of the dataset storage, defined by the user
    :param _id: ID of the dataset storage
    :param project_id: ID of the project containing the storage
    :param use_for_training: Bool indicating if the storage is used for training jobs
    :param creator_name: Optional, name of the user who created the dataset storage;
        if unspecified, the system automatically assigns a default name
    :param creation_date: Optional, timestamp when the dataset storage was created;
        if unspecified, the system automatically uses the current date
    """

    def __init__(
        self,
        name: str,
        _id: ID,
        project_id: ID,
        use_for_training: bool,
        creator_name: str | None = None,
        creation_date: datetime.datetime | None = None,
        ephemeral: bool = True,
    ) -> None:
        super().__init__(id_=_id, ephemeral=ephemeral)
        self.name = name
        self.workspace_id = CTX_SESSION_VAR.get().workspace_id if _id != ID() else ID()
        self.project_id = project_id
        self.identifier = DatasetStorageIdentifier(
            workspace_id=self.workspace_id, project_id=project_id, dataset_storage_id=_id
        )
        self.use_for_training = use_for_training
        self.creator_name = creator_name if creator_name is not None else DEFAULT_USER_NAME
        self.creation_date = now() if creation_date is None else creation_date

    def __repr__(self) -> str:
        return (
            f"DatasetStorage(id_={self.id_}, "
            f"name={self.name}, "
            f"use_for_training={self.use_for_training}, "
            f"creation_date={self.creation_date})"
        )

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DatasetStorage):
            return self.id_ == other.id_
        return False


class NullDatasetStorage(DatasetStorage):
    """Representation of a 'dataset storage not found'"""

    def __init__(self) -> None:
        super().__init__(
            name="",
            _id=ID(),
            project_id=ID(),
            creation_date=datetime.datetime.min,
            use_for_training=False,
            ephemeral=False,
        )

    def __repr__(self) -> str:
        return "NullDatasetStorage()"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, NullDatasetStorage)
