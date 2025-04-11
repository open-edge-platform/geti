# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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

"""This module implements the DatasetItemLabels"""

from geti_types import ID
from sc_sdk.entities.persistent_entity import PersistentEntity


class DatasetItemLabels(PersistentEntity):
    """
    This class represents the labels for a dataset item. In the future if the buffer dataset items are stored in their
    own repo, the information of labels per dataset item can be stored in that repo. :todo remove this class CVS-99554

    :param dataset_item_id: ID of the dataset item for which we are storing label ids
    :param label_ids: Relevant label IDs for the dataset item
    :param ephemeral: True if the DatasetItemLabels instance exists only in memory, False if
        it is backed up by the database
    """

    def __init__(
        self,
        dataset_item_id: ID,
        label_ids: list[ID],
        ephemeral: bool = True,
    ) -> None:
        super().__init__(id_=dataset_item_id, ephemeral=ephemeral)
        self.dataset_item_id = dataset_item_id
        self.label_ids = label_ids


class NullDatasetItemLabels(DatasetItemLabels):
    def __init__(self) -> None:
        super().__init__(
            dataset_item_id=ID(),
            label_ids=[],
            ephemeral=False,
        )
