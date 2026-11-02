# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from enum import StrEnum
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, computed_field, model_validator

from .base import BaseEntity


class ImageFormat(StrEnum):
    """Format of the image."""

    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"
    JFIF = "jfif"
    TIF = "tif"
    TIFF = "tiff"
    BMP = "bmp"
    WEBP = "webp"


class VideoFormat(StrEnum):
    """Format of the video."""

    MP4 = "mp4"
    AVI = "avi"
    MKV = "mkv"
    MOV = "mov"
    WEBM = "webm"
    M4V = "m4v"


class OmeFormat(StrEnum):
    """Format of an OME (multi-dimensional microscopy) image."""

    OME_TIFF = "ome.tiff"
    OME_TIF = "ome.tif"


MediaFormat = ImageFormat | VideoFormat | OmeFormat


def parse_media_format(file_name_or_extension: str) -> MediaFormat | None:
    """
    Resolve a media format from a file name or extension, honouring compound extensions.

    The longest matching suffix wins, so that `a.ome.tiff` resolves to OME-TIFF while `b.tiff` resolves to TIFF.

    Args:
        file_name_or_extension: A file name (`a.ome.tiff`) or an extension with or without the leading dot.

    Returns:
        The matching media format, or None if the extension is not supported.
    """
    value = file_name_or_extension.lower()
    formats: list[MediaFormat] = [*OmeFormat, *ImageFormat, *VideoFormat]
    for media_format in sorted(formats, key=lambda f: len(f.value), reverse=True):
        if value == media_format.value or value.endswith(f".{media_format.value}"):
            return media_format
    return None


def split_media_file_name(file_name: str) -> tuple[str, str]:
    """
    Split a file name into its base name and extension, keeping compound extensions such as `.ome.tiff` whole.

    Args:
        file_name: The file name to split.

    Returns:
        A tuple of (base name, extension without the leading dot). The extension is empty if there is none.
    """
    for ome_format in OmeFormat:
        suffix = f".{ome_format.value}"
        if file_name.lower().endswith(suffix) and len(file_name) > len(suffix):
            return file_name[: -len(suffix)], file_name[-len(suffix) + 1 :]
    name, dot, extension = file_name.rpartition(".")
    return (name, extension) if dot else (file_name, "")


class MediaType(StrEnum):
    """Type of the media"""

    IMAGE = "image"
    VIDEO = "video"
    VIDEO_FRAME = "video_frame"
    OME_IMAGE = "ome_image"
    OME_PLANE = "ome_plane"


# Media types acting as containers of lazily-created leaf media, and the leaf media types themselves.
# Leaves are annotated individually but are never listed or assigned to dataset views on their own.
CONTAINER_MEDIA_TYPES: tuple[MediaType, ...] = (MediaType.VIDEO, MediaType.OME_IMAGE)
LEAF_MEDIA_TYPES: tuple[MediaType, ...] = (MediaType.VIDEO_FRAME, MediaType.OME_PLANE)


def _expose_parent_id(model: type[BaseModel], data: Any, field_name: str) -> Any:
    """
    Map the ORM `parent_id` attribute onto the public field name of a leaf media (e.g. `video_id`).

    ORM rows store the parent container under `parent_id`, while the public models keep a descriptive name.
    Plain dicts and objects without `parent_id` (e.g. domain models) are passed through unchanged.
    """
    if isinstance(data, dict) or not hasattr(data, "parent_id"):
        return data
    values = {name: getattr(data, name) for name in model.model_fields if hasattr(data, name)}
    values[field_name] = data.parent_id
    return values


class MediaSortBy(StrEnum):
    """Field to sort media listing by."""

    UPLOAD_DATE = "upload_date"


class SortDirection(StrEnum):
    """Direction to sort media listing in."""

    ASC = "asc"
    DESC = "desc"


class BaseMedia(BaseEntity):
    """
    Media represents an uploaded or fetched media within a dataset, it can be one of Image, Video or VideoFrame.

    Attributes:
        id: Unique identifier for the media.
        type: Type of the media.
        project_id: Identifier of the project to which the media belongs.
        name: Name of the media.
        format: Format of the media (e.g., JPG, PNG).
        width: Width of the media in pixels.
        height: Height of the media in pixels.
        size: Size of the media in bytes.
        source_id: Identifier of the source from which the media was acquired, if applicable.
    """

    model_config = ConfigDict(frozen=True)
    id: UUID
    project_id: UUID
    name: str
    format: MediaFormat
    width: int
    height: int
    size: int
    source_id: UUID | None


class Image(BaseMedia):
    type: Literal[MediaType.IMAGE]


class VideoFrame(BaseMedia):
    """
    Attributes:
        video_id: Video identifier
        frame_index: Frame index
    """

    type: Literal[MediaType.VIDEO_FRAME]
    video_id: UUID
    frame_index: int

    @model_validator(mode="before")
    @classmethod
    def _map_parent_id(cls, data: Any) -> Any:
        return _expose_parent_id(cls, data, "video_id")


class Video(BaseMedia):
    """
    Attributes:
        fps: Video fps
        frame_count: Total number of frames
    """

    type: Literal[MediaType.VIDEO]
    fps: float
    frame_count: int
    annotated_frame_count: int = 0

    @computed_field
    @property
    def duration(self) -> float:
        """Return duration in seconds"""
        return self.frame_count / self.fps


class NotAnnotatedVideoFrame(BaseModel):
    """
    Video frame that is not annotated yet. It contains the video information and the frame index.
    """

    model_config = ConfigDict(frozen=True)
    video: Video
    frame_index: int

    @computed_field
    @property
    def video_id(self) -> UUID:
        return self.video.id


class OmeImage(BaseMedia):
    """
    Multi-dimensional (XYCZT) OME image. Its annotatable (Z, T) planes are `OmePlane` media created lazily.

    Attributes:
        plane_count: Total number of (Z, T) planes in the image
    """

    type: Literal[MediaType.OME_IMAGE]
    plane_count: int

    @model_validator(mode="before")
    @classmethod
    def _map_frame_count(cls, data: Any) -> Any:
        # ORM rows store the number of leaves of any container under `frame_count`
        if isinstance(data, dict) or not hasattr(data, "frame_count"):
            return data
        values = {name: getattr(data, name) for name in cls.model_fields if hasattr(data, name)}
        values["plane_count"] = data.frame_count
        return values


class OmePlane(BaseMedia):
    """
    Annotated (Z, T) plane of an OME image, holding all the channels.

    Attributes:
        ome_image_id: Identifier of the parent OME image
        z_index: Z index of the plane
        t_index: T index of the plane
    """

    type: Literal[MediaType.OME_PLANE]
    ome_image_id: UUID
    z_index: int
    t_index: int

    @model_validator(mode="before")
    @classmethod
    def _map_parent_id(cls, data: Any) -> Any:
        return _expose_parent_id(cls, data, "ome_image_id")


class NotAnnotatedOmePlane(BaseModel):
    """OME plane that is not annotated yet. It contains the OME image information and the plane coordinates."""

    model_config = ConfigDict(frozen=True)
    ome_image: OmeImage
    z_index: int
    t_index: int

    @computed_field
    @property
    def ome_image_id(self) -> UUID:
        return self.ome_image.id


Media = Annotated[Image | Video | VideoFrame | OmeImage | OmePlane, Field(discriminator="type")]

MediaAdapter: TypeAdapter[Media] = TypeAdapter(Media)


class VideoRange(BaseModel):
    start_frame: Annotated[int, Field(description="Index of the first frame to predict, inclusive", ge=0)]
    end_frame: Annotated[int, Field(description="Index of the last frame to predict, inclusive", ge=0)]
    stride: Annotated[
        int, Field(description="Predict every nth frame in the range, e.g. stride=1 means predict every frame", ge=1)
    ]

    @model_validator(mode="after")
    def validate_frame_range(self) -> "VideoRange":
        if self.end_frame < self.start_frame:
            raise ValueError(f"end_frame ({self.end_frame}) must be >= start_frame ({self.start_frame})")
        return self


class IndexRange(BaseModel):
    start: Annotated[int, Field(description="First index, inclusive", ge=0)]
    end: Annotated[int, Field(description="Last index, inclusive", ge=0)]
    stride: Annotated[int, Field(description="Take every nth index in the range", ge=1)] = 1

    @model_validator(mode="after")
    def validate_index_range(self) -> "IndexRange":
        if self.end < self.start:
            raise ValueError(f"end ({self.end}) must be >= start ({self.start})")
        return self

    @property
    def indexes(self) -> list[int]:
        return list(range(self.start, self.end + 1, self.stride))


class PlaneRange(BaseModel):
    """Range of (Z, T) planes of an OME image; every combination of the Z and T indexes is selected."""

    z: IndexRange = Field(default_factory=lambda: IndexRange(start=0, end=0))
    t: IndexRange = Field(default_factory=lambda: IndexRange(start=0, end=0))

    @property
    def count(self) -> int:
        return len(self.z.indexes) * len(self.t.indexes)


class MediaPredictionRequest(BaseModel):
    media_id: UUID
    range: VideoRange | None
    plane_range: Annotated[PlaneRange | None, Field(description="Planes to predict, for OME images only")] = None


class MediaListPredictionRequest(BaseModel):
    model_id: UUID
    model_variant_id: UUID | None = None
    media: list[MediaPredictionRequest]
    device: str
    confidence_threshold: Annotated[
        float | None,
        Field(
            default=None,
            ge=0.0,
            le=1.0,
            description=(
                "Confidence threshold to apply to the model before inference. "
                "When omitted, the model keeps the threshold it is currently using. "
                "If never set, the model uses the optimal threshold determined at export time, if any."
            ),
        ),
    ]
