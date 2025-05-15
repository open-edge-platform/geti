# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This file defines the IMetedata interface and implements IMetadata classes"""

import abc
from enum import Enum, auto
from typing import Any

from iai_core.adapters.adapter import IAdapter
from iai_core.entities.model import Model

from geti_types import ID, MediaIdentifierEntity, NullMediaIdentifier, PersistentEntity


class IMetadata(metaclass=abc.ABCMeta):
    """This interface represents any additional metadata information which can be connected to an IMedia."""

    __name: str | None = None

    @property
    def name(self) -> str | None:
        """Gets or sets the name of the Metadata item."""
        return self.__name

    @name.setter
    def name(self, value: str | None) -> None:
        self.__name = value


class FloatType(Enum):
    """Represents the use of the FloatMetadata."""

    FLOAT = auto()  # Regular float, without particular context
    EMBEDDING_VALUE = auto()
    ACTIVE_SCORE = auto()

    def __str__(self):
        """Return the name of FloatType enum."""
        return str(self.name)


class FloatMetadata(IMetadata):
    """This class represents metadata of type float.

    Args:
        name (str): Name of the metadata.
        value (float): Value of the metadata.
        float_type (FloatType): Type of the metadata.
    """

    def __init__(self, name: str, value: float, float_type: FloatType = FloatType.FLOAT) -> None:
        self.name = name
        self.value = value
        self.float_type = float_type

    def __repr__(self) -> str:
        """Prints the model, data and type of the from iai_core.entities.dataset_item."""
        return f"FloatMetadata({self.name}, {self.value}, {self.float_type})"

    def __eq__(self, other: object) -> bool:
        """Checks if two FloatMetadata have the same name, value and type."""
        if isinstance(other, FloatMetadata):
            return self.name == other.name and self.value == other.value and self.float_type == other.float_type
        return False


class VideoMetadata(IMetadata):
    """This class represents metadata of video.

    Args:
        video_id (str): id(name) for video.
        frame_idx (int): Index for frame.
        is_empty_frame(bool): whether this is empty frame(for action detection)
    """

    def __init__(self, video_id: str, frame_idx: int, is_empty_frame: bool):
        self.video_id = video_id
        self.frame_idx = frame_idx
        self.is_empty_frame = is_empty_frame
        self.metadata = {"video_id": video_id, "frame_idx": frame_idx, "is_empty_frame": is_empty_frame}

    def __repr__(self) -> str:
        """Prints the video_id, frame_id and type of the from iai_core.entities.dataset_item."""
        out_string = "VideoMetadata"
        out_string += f"({self.metadata})"
        return out_string

    def __eq__(self, other: object):
        """Checks if two VideoMetadata have the same name, value and type."""
        if isinstance(other, VideoMetadata):
            return self.metadata == other.metadata
        return False

    def update(self, key: str, value: Any) -> None:
        """Update metadata information."""
        setattr(self, key, value)
        self.metadata[key] = value


class NullMetadata(IMetadata):
    """
    This class represents a None value in metadata
    """

    def __init__(self) -> None:
        self.name = None
        self.value = None

    def __repr__(self) -> str:
        return f"NullMetadata({self.name}, {self.value})"


class MetadataItem(PersistentEntity):
    """
    MetadataItem links a generic metadata value (embeddings, uncertainty scores,
    saliency maps, ...) with the corresponding media, dataset item and model.
    """

    def __init__(
        self,
        id: ID,
        data: IMetadata,
        dataset_item_id: ID,
        media_identifier: MediaIdentifierEntity = NullMediaIdentifier(),
        model: Model | None = None,
        ephemeral: bool = True,
    ) -> None:
        PersistentEntity.__init__(self, id_=id, ephemeral=ephemeral)

        self.data = data
        self._model = model
        self.dataset_item_id = dataset_item_id
        self.media_identifier = media_identifier
        self._model_adapter: IAdapter | None = None

    @property
    def model(self) -> Model | None:
        if self._model is not None:  # type: ignore
            return self._model  # type: ignore
        if self._model_adapter is not None:
            self._model = self._model_adapter.get()
        return self._model

    @classmethod
    def with_adapters(
        cls,
        id: ID,
        data: IMetadata,
        dataset_item_id: ID,
        model_adapter: IAdapter[Model],
        media_identifier: MediaIdentifierEntity = NullMediaIdentifier(),
        ephemeral: bool = True,
    ):
        """
        Initializes a MetadataItem with the given adapter to lazily fetch a model.
        """
        inst = cls(
            id=id, data=data, dataset_item_id=dataset_item_id, media_identifier=media_identifier, ephemeral=ephemeral
        )
        inst._model_adapter = model_adapter
        return inst

    def __repr__(self) -> str:
        return (
            f"MetadataItem(id={self.id_}, media_identifier={self.media_identifier}, "
            f"model={self.model}, data={self.data})"
        )

    def __eq__(self, other: object):
        if not isinstance(other, MetadataItem):
            return False
        return self.id_ == other.id_ and self.media_identifier == other.media_identifier and self.data == other.data


class NullMetadataItem(MetadataItem):
    """
    This class represents MetadataItem not found.
    """

    def __init__(self) -> None:
        super().__init__(
            id=ID(),
            data=NullMetadata(),
            media_identifier=NullMediaIdentifier(),
            dataset_item_id=ID(),
            ephemeral=False,
        )

    def __repr__(self) -> str:
        return "NullMetadataItem()"
