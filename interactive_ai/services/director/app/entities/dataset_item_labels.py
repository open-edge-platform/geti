# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
