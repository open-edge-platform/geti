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
import io
from dataclasses import dataclass

import numpy as np

from entities.reference_feature_adapter import ReferenceFeatureAdapter

from geti_types import ID, MediaIdentifierEntity, NullMediaIdentifier
from sc_sdk.entities.persistent_entity import PersistentEntity


@dataclass(frozen=True)
class ReferenceMediaInfo:
    """ReferenceMediaInfo stores information about the media used for learning the reference feature"""

    dataset_storage_id: ID
    annotation_scene_id: ID
    media_identifier: MediaIdentifierEntity


class ReferenceFeature(PersistentEntity):
    """
    ReferenceFeature represents a SINGLE feature vector generated through one-shot learning for a specific label.

    Note: the ID of the reference feature entity is the same as the ID of the label it represents.

    :param task_id: ID of the task associated with this reference feature
    :param label_id: ID of the label associated with this reference feature
    :param media_info: information about the media used for learning the reference feature
    :param reference_feature_adapter: adapter to fetch the vector binary data of this reference feature
    :param numpy: numpy data of this reference feature
    """

    def __init__(
        self,
        task_id: ID,
        label_id: ID,
        media_info: ReferenceMediaInfo,
        reference_feature_adapter: ReferenceFeatureAdapter | None = None,
        numpy: np.ndarray | None = None,
        ephemeral: bool = True,
    ):
        if reference_feature_adapter is None and numpy is None:
            raise ValueError("Either an adapter or numpy data must be provided to create a ReferenceFeature")
        super().__init__(id_=label_id, ephemeral=ephemeral)
        self.task_id = task_id
        self.media_info = media_info
        self.reference_feature_adapter: ReferenceFeatureAdapter | None = reference_feature_adapter
        self._numpy: np.ndarray | None = numpy

    @property
    def label_id(self) -> ID:
        """Get ID of the label associated with this reference feature"""
        return self.id_

    @property
    def numpy(self) -> np.ndarray:
        """Get numpy array of this reference feature"""
        if self._numpy is None:
            if self.reference_feature_adapter is None:
                raise ValueError("Neither the adapter or numpy data is set for this ReferenceFeature")
            self._numpy = self.reference_feature_adapter.numpy
        return self._numpy

    @property
    def numpy_npz_bytes(self) -> bytes:
        """Get numpy data as bytes"""
        buffer = io.BytesIO()
        np.savez(buffer, array=self.numpy)
        return buffer.getvalue()

    @property
    def data_binary_filename(self) -> str:
        """Get the binary filename of the numpy data"""
        if self.reference_feature_adapter is not None:
            return self.reference_feature_adapter.binary_filename
        return ""

    def __repr__(self) -> str:
        return f"ReferenceFeature(id={self.id_}, label_id={self.label_id}, media_info={self.media_info})"


class NullReferenceFeature(ReferenceFeature):
    """Representation of a not found reference feature"""

    def __init__(self) -> None:
        super().__init__(
            task_id=ID(),
            label_id=ID(),
            media_info=ReferenceMediaInfo(
                dataset_storage_id=ID(),
                annotation_scene_id=ID(),
                media_identifier=NullMediaIdentifier(),
            ),
            numpy=np.array([], dtype=np.uint8),
            ephemeral=True,
        )

    def __repr__(self) -> str:
        return "NullReferenceFeature()"
