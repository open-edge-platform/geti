# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, TypeAdapter, computed_field, model_validator

from .base import BaseEntity


class ImageFormat(StrEnum):
    """Format of the image."""

    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"
    JFIF = "jfif"
    TIF = "tif"
    TIFF = "tiff"
    OME_TIFF = "ome.tiff"
    OME_TIF = "ome.tif"
    BMP = "bmp"
    WEBP = "webp"

    @classmethod
    def from_filename(cls, filename: str) -> "ImageFormat":
        """Resolve the longest supported suffix, including compound OME suffixes."""
        name = f".{filename.lower()}"
        for image_format in sorted(cls, key=lambda item: len(item.value), reverse=True):
            if name.endswith(f".{image_format.value}"):
                return image_format
        raise ValueError(f"Unsupported image filename: {filename}")


class VideoFormat(StrEnum):
    """Format of the video."""

    MP4 = "mp4"
    AVI = "avi"
    MKV = "mkv"
    MOV = "mov"
    WEBM = "webm"
    M4V = "m4v"


MediaFormat = ImageFormat | VideoFormat


class MediaType(StrEnum):
    """Type of the media"""

    IMAGE = "image"
    VIDEO = "video"
    VIDEO_FRAME = "video_frame"
    OME_IMAGE = "ome_image"
    OME_PLANE = "ome_plane"


LEAF_MEDIA_TYPES: tuple[MediaType, ...] = (MediaType.VIDEO_FRAME, MediaType.OME_PLANE)
CONTAINER_MEDIA_TYPES: tuple[MediaType, ...] = (MediaType.VIDEO, MediaType.OME_IMAGE)


class MediaSortBy(StrEnum):
    """Field to sort media listing by."""

    UPLOAD_DATE = "upload_date"


class SortDirection(StrEnum):
    """Direction to sort media listing in."""

    ASC = "asc"
    DESC = "desc"


class MediaAnnotationStatus(BaseModel):
    """
    Annotation status of an image, video frame, OME plane or OME container.

    It is loaded when media are listed or fetched by id (see ``MediaService``); elsewhere it keeps its default.

    Attributes:
        has_annotations: Whether the media is annotated. An annotation with an empty label counts as annotated.
    """

    model_config = ConfigDict(frozen=True)
    has_annotations: bool = False


class VideoAnnotationStatus(BaseModel):
    """
    Annotation status of a video, aggregated over its frames.

    It is loaded when media are listed or fetched by id (see ``MediaService``); elsewhere it keeps its default.

    Attributes:
        annotated_video_frames: Number of annotated frames of the video.
    """

    model_config = ConfigDict(frozen=True)
    annotated_video_frames: int = 0

    @computed_field
    @property
    def has_annotations(self) -> bool:
        """Whether at least one frame of the video is annotated"""
        return self.annotated_video_frames > 0


class BaseMedia(BaseEntity):
    """
    Media represents an image, container, or registered frame/plane within a dataset.

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
    """
    Attributes:
        annotation_status: Annotation status of the image
    """

    type: Literal[MediaType.IMAGE]
    annotation_status: MediaAnnotationStatus = Field(default_factory=MediaAnnotationStatus)


class OmeImage(BaseMedia):
    """An OME container whose individual planes can be annotated."""

    type: Literal[MediaType.OME_IMAGE]
    annotation_status: MediaAnnotationStatus = Field(default_factory=MediaAnnotationStatus)


class OmePlane(BaseMedia):
    """A lazily registered plane; pixels remain in its parent OME container."""

    type: Literal[MediaType.OME_PLANE]
    ome_image_id: UUID = Field(validation_alias=AliasChoices("ome_image_id", "parent_id"))
    z_index: int = Field(ge=0)
    t_index: int = Field(ge=0)
    annotation_status: MediaAnnotationStatus = Field(default_factory=MediaAnnotationStatus)


class VideoFrame(BaseMedia):
    """
    Attributes:
        video_id: Video identifier
        frame_index: Frame index
        annotation_status: Annotation status of the frame
    """

    type: Literal[MediaType.VIDEO_FRAME]
    video_id: UUID = Field(validation_alias=AliasChoices("video_id", "parent_id"))
    frame_index: int
    annotation_status: MediaAnnotationStatus = Field(default_factory=MediaAnnotationStatus)


class Video(BaseMedia):
    """
    Attributes:
        fps: Video fps
        frame_count: Total number of frames
        annotation_status: Annotation status of the video, aggregated over its frames
    """

    type: Literal[MediaType.VIDEO]
    fps: float
    frame_count: int
    annotation_status: VideoAnnotationStatus = Field(default_factory=VideoAnnotationStatus)

    @computed_field
    @property
    def duration(self) -> float:
        """Return duration in seconds"""
        return self.frame_count / self.fps

    # TODO: remove together with the deprecated `VideoView.annotated_frame_count` API field.
    @property
    def annotated_frame_count(self) -> int:
        """Deprecated alias of ``annotation_status.annotated_video_frames``"""
        return self.annotation_status.annotated_video_frames


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


class NotAnnotatedOmePlane(BaseModel):
    """An addressed plane that has not yet been registered for annotation."""

    model_config = ConfigDict(frozen=True)
    image: OmeImage
    z_index: int
    t_index: int


Media = Annotated[Image | Video | VideoFrame | OmeImage | OmePlane, Field(discriminator="type")]

MediaAdapter: TypeAdapter[Media] = TypeAdapter(Media)


class IndexRange(BaseModel):
    """An inclusive range of zero-based indexes."""

    start: Annotated[int, Field(description="First index to predict, inclusive", ge=0)]
    end: Annotated[int, Field(description="Last index to predict, inclusive", ge=0)]
    stride: Annotated[int, Field(description="Predict every nth index; stride=1 selects every index", ge=1)]

    @model_validator(mode="after")
    def validate_index_range(self) -> "IndexRange":
        if self.end < self.start:
            start_name = type(self).model_fields["start"].alias or "start"
            end_name = type(self).model_fields["end"].alias or "end"
            raise ValueError(f"{end_name} ({self.end}) must be >= {start_name} ({self.start})")
        return self

    @property
    def indexes(self) -> range:
        """Return requested indexes without allocating a list."""
        return range(self.start, self.end + 1, self.stride)

    @property
    def count(self) -> int:
        """Count requested indexes without allocating or overflowing a Python range length."""
        return (self.end - self.start) // self.stride + 1


class VideoRange(IndexRange):
    """An index range preserving the existing video request field names."""

    model_config = ConfigDict(serialize_by_alias=True)
    start: Annotated[
        int, Field(alias="start_frame", description="Index of the first frame to predict, inclusive", ge=0)
    ]
    end: Annotated[int, Field(alias="end_frame", description="Index of the last frame to predict, inclusive", ge=0)]
    stride: Annotated[
        int, Field(description="Predict every nth frame in the range, e.g. stride=1 means predict every frame", ge=1)
    ]

    @property
    def start_frame(self) -> int:
        """Return the first requested video frame."""
        return self.start

    @property
    def end_frame(self) -> int:
        """Return the last requested video frame."""
        return self.end


class PlaneRange(BaseModel):
    """Inclusive Z/T ranges; an omitted axis selects index zero."""

    z: IndexRange | None = None
    t: IndexRange | None = None

    @property
    def indexes(self) -> tuple[range, range]:
        """Return Z and T indexes without allocating plane lists."""
        return (
            self.z.indexes if self.z is not None else range(1),
            self.t.indexes if self.t is not None else range(1),
        )

    @property
    def count(self) -> int:
        """Return the number of planes in the Cartesian product."""
        return (self.z.count if self.z is not None else 1) * (self.t.count if self.t is not None else 1)


class MediaPredictionRequest(BaseModel):
    media_id: UUID
    range: VideoRange | None = None
    plane_range: PlaneRange | None = None

    @model_validator(mode="after")
    def validate_range_selection(self) -> "MediaPredictionRequest":
        if self.range is not None and self.plane_range is not None:
            raise ValueError("Specify either range or plane_range, not both.")
        return self

    @property
    def count(self) -> int:
        """Count requested images, frames or planes for the inference limit."""
        if self.range is not None:
            return self.range.count
        return self.plane_range.count if self.plane_range is not None else 1


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
