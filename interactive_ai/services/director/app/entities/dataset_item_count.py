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

"""This module implements the DatasetItemCount"""

from dataclasses import dataclass

from geti_types import ID
from sc_sdk.entities.label import Label
from sc_sdk.entities.persistent_entity import PersistentEntity


@dataclass
class DatasetItemCountData:
    """
    Defines the counting information related to DatasetItemCount.

    count                   number of dataset items
    dataset_item_ids        list of dataset items ids
    per_label_count         dictionary with number of dataset items per label
    """

    count: int
    dataset_item_ids: list[ID]
    per_label_count: dict[ID, int]


@dataclass
class NewDatasetItemCountData(DatasetItemCountData):
    """Count data for new dataset items"""


@dataclass
class DeletedDatasetItemCountData(DatasetItemCountData):
    """Count data for deleted dataset items"""


@dataclass(frozen=True)
class LabelData:
    """
    Dataclass containing a selection of label properties. This is used to pass label information to the UI when the
    required annotations per label are requested, and avoids going to the LabelRepo which is expensive.

    :param id_: ID of the label
    :param name: Name of the label
    :param color_hex_str: Color of the label, in string format
    :param is_anomalous: Boolean indicating whether the label is anomalous
    """

    id_: ID
    name: str
    color_hex_str: str
    is_anomalous: bool

    @classmethod
    def from_label(cls, label: Label) -> "LabelData":
        """Create LabelData from a label

        :param label: Label to create dataclass for
        :returns: LabelData for the label
        """
        return cls(
            id_=label.id_,
            name=label.name,
            color_hex_str=label.color.hex_str,
            is_anomalous=label.is_anomalous,
        )


class DatasetItemCount(PersistentEntity):
    """
    This class represents the number of dataset items that have been created for a task. It is responsible for tracking
    the total number of dataset items for the task, the dataset items per label, and the unassigned dataset items.

    DatasetItemCount uses the same ID of the corresponding task node, which makes it
    a per-task singleton from the logical point of view.

    :param task_node_id: ID of the task_node, also used as ID for the DatasetItemCount object
    :param task_label_data: Label data for the task - contains the colors and names of labels relevant for this task
    :param n_dataset_items: Total number of dataset items that have been created for this task.
    :param n_items_per_label: Number of dataset items with this label that have been created
    :param unassigned_dataset_items: A list of all dataset item IDs for dataset items that are still unassigned
    :param ephemeral: True if the DatasetItemCount instance exists only in memory, False if
        it is backed up by the database
    """

    def __init__(
        self,
        task_node_id: ID,
        task_label_data: list[LabelData],
        n_dataset_items: int,
        n_items_per_label: dict[ID, int],
        unassigned_dataset_items: list[ID],
        ephemeral: bool = True,
    ) -> None:
        super().__init__(id_=task_node_id, ephemeral=ephemeral)
        self.task_label_data = task_label_data
        self.n_dataset_items = n_dataset_items
        self.n_items_per_label = n_items_per_label
        self.unassigned_dataset_items = unassigned_dataset_items

    @property
    def task_node_id(self) -> ID:
        return self.id_


class NullDatasetItemCount(DatasetItemCount):
    def __init__(self) -> None:
        super().__init__(
            task_node_id=ID(),
            task_label_data=[],
            n_dataset_items=0,
            n_items_per_label={},
            unassigned_dataset_items=[],
            ephemeral=False,
        )

    def __repr__(self) -> str:
        return "NullDatasetItemCount()"
