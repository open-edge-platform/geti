# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This file defines the DatasetStorageFilterData class"""

from dataclasses import dataclass
from datetime import datetime

from iai_core.entities.annotation import AnnotationScene
from iai_core.entities.annotation_scene_state import AnnotationState
from iai_core.entities.image import Image
from iai_core.entities.media import ImageExtensions, MediaIdentifierEntity, MediaPreprocessingStatus, VideoExtensions
from iai_core.entities.persistent_entity import PersistentEntity
from iai_core.entities.shapes import Shape, ShapeType
from iai_core.entities.video import Video

from geti_types import ID, NullMediaIdentifier


@dataclass
class ShapeFilterData:
    """
    ShapeFilterData keeps track of data from Shape that are relevant for dataset storage filtering.
    """

    shape_type: ShapeType
    area_percentage: float
    area_pixel: float

    @classmethod
    def from_shape(cls, shape: Shape, media_width: int, media_height: int) -> "ShapeFilterData":
        """
        Extract relevant shape data and return ShapeFilterData object

        :param shape: the Shape that contains the data
        :param media_width: width of the original image
        :param media_height: height of the origanl image
        :return: ShapeFilterData containing the relevant data for filtering
        """
        area_percentage = shape.get_area()
        return cls(
            shape_type=shape.type,
            area_percentage=area_percentage,
            area_pixel=area_percentage * media_width * media_height,
        )


@dataclass
class AnnotationSceneFilterData:
    """
    Stores data from an annotation scene relevant for dataset filtering.

    :param annotation_scene_id: ID of the most recent annotation scene for the media
    :param user_name: editor name of the last annotation scene for the media
    :param shapes: shape filter data of all shapes in the annotation scene
    :param label_ids: ID of all labels present in the last annotation scene
    :param creation_date: creation date of the last annotation scene
    """

    annotation_scene_id: ID
    user_name: str
    shapes: list[ShapeFilterData]
    label_ids: list[ID]
    creation_date: datetime

    @classmethod
    def from_annotation_scene(cls, annotation_scene: AnnotationScene) -> "AnnotationSceneFilterData":
        """
        Extract relevant annotation scene data and return AnnotationSceneFilterData object

        :param annotation_scene: the AnnotationScene that contains the data
        :return: AnnotationSceneFilterData containing the relevant data for filtering
        """
        shapes = [
            ShapeFilterData.from_shape(
                shape=annotation.shape,
                media_width=annotation_scene.media_width,
                media_height=annotation_scene.media_height,
            )
            for annotation in annotation_scene.annotations
        ]
        return cls(
            annotation_scene_id=annotation_scene.id_,
            user_name=annotation_scene.last_annotator_id,
            shapes=shapes,
            label_ids=sorted(annotation_scene.get_label_ids(include_empty=True)),
            creation_date=annotation_scene.creation_date,
        )


@dataclass
class VideoFilterData:
    """
    Stores data from a video entity relevant for dataset storage filtering

    :param frame_count: total frame count of the video
    :param frame_stride: number of frames skipped by default for annotations
    :param frame_rate: frames per second of the video
    :param duration: duration in seconds of the video
    :param unannotated_frames: number of frames without annotations, by default the total frame count of the video
    """

    frame_count: int
    frame_stride: int
    frame_rate: float
    duration: int
    unannotated_frames: int | None = None

    @classmethod
    def from_video(cls, video: Video) -> "VideoFilterData":
        """
        Extract relevant video data and return VideoFilterData object

        :param video: the Video entity that contains the data
        :return: VideoFilterData containing the relevant data for filtering
        """
        return cls(
            frame_count=video.total_frames,
            frame_stride=video.stride,
            frame_rate=video.fps,
            duration=video.duration,
            unannotated_frames=video.total_frames,
        )


@dataclass
class MediaFilterData:
    """
    Stores data from media entities relevant for dataset storage filtering

    :param media_name: name of the media
    :param media_extension: extension of the media file
    :param media_height: height of the media in pixels
    :param media_width: width of the media in pixels
    :param upload_date: upload date of the media
    :param size: size on harddisk of media_entity
    :param video_filter_data: video data relevant for filtering
    """

    media_name: str
    media_extension: (
        ImageExtensions | VideoExtensions | None
    )  # Only optional until after the migration script added all extensions
    media_width: int
    media_height: int
    upload_date: datetime
    uploader_id: str
    size: int
    video_filter_data: VideoFilterData | None = None

    @classmethod
    def from_media(cls, media: Image | Video) -> "MediaFilterData":
        """
        Extract relevant media data and return MediaFilterData object

        :param media: the Image or Video entity that contains the data
        :return: MediaFilterData containing the relevant data for filtering
        """
        return cls(
            media_name=media.name,
            media_extension=media.extension,
            media_width=media.width,
            media_height=media.height,
            upload_date=media.creation_date,
            uploader_id=media.uploader_id,
            size=media.size,
            video_filter_data=VideoFilterData.from_video(video=media) if isinstance(media, Video) else None,
        )


class DatasetStorageFilterData(PersistentEntity):
    """
    DatasetStorageFilterData keeps track of data relevant for filtering a dataset storage.

    :param media_identifier: MediaIdentifier of the media
    :param media_filter_data: data relevant for dataset storage filtering from a media entity
    :param annotation_scene_filter_data: data relevant for dataset storage filtering from an annotation scene
    :param media_annotation_state: AnnotationState of the media
    :param preprocessing: Preprocessing status of the media
    :param ephemeral: bool indicating whether or not entity is persisted in DB
    """

    def __init__(
        self,
        media_identifier: MediaIdentifierEntity,
        preprocessing: MediaPreprocessingStatus,
        media_filter_data: MediaFilterData | None = None,
        annotation_scene_filter_data: AnnotationSceneFilterData | None = None,
        media_annotation_state: AnnotationState | None = None,
        ephemeral: bool = True,
    ) -> None:
        self.media_identifier = media_identifier
        self.preprocessing = preprocessing
        self.media_filter_data = media_filter_data
        self.annotation_scene_filter_data = annotation_scene_filter_data
        self.media_annotation_state = media_annotation_state
        super().__init__(id_=self.media_identifier.as_id(), ephemeral=ephemeral)

    @property
    def id_(self) -> ID:
        return self.media_identifier.as_id()

    @id_.setter
    def id_(self, _) -> None:  # noqa: ANN001
        raise NotImplementedError(
            "id_ cannot be set for DatasetStorageFilterData, it is derived from media_filter_data.media_identifier."
        )

    @classmethod
    def create_dataset_storage_filter_data(
        cls,
        media_identifier: MediaIdentifierEntity,
        preprocessing: MediaPreprocessingStatus,
        media: Image | Video | None = None,
        annotation_scene: AnnotationScene | None = None,
        media_annotation_state: AnnotationState | None = None,
    ) -> "DatasetStorageFilterData":
        """
        Extract data from media and annotation scene relevant for filtering

        :param media_identifier: MediaIdentifier of the image, video or video frame
        :param preprocessing: Media preprocessing data
        :param media: the Image or Video entity that contains the data
        :param annotation_scene: the AnnotationScene that contains the data
        :param media_annotation_state: the AnnotationState of the media
        :returns: DatasetStorageFilterData containing the relevant data for filtering
        """
        if media is not None and media_identifier.media_id != media.media_identifier.media_id:
            raise ValueError(
                f"media_identifier {media_identifier} and media.media_identifier "
                f"{media.media_identifier} should have the same media_id."
            )
        if annotation_scene is not None and media_annotation_state is None:
            raise ValueError("If annotation_scene is provided, then a media_annotation_state must be provided as well.")

        media_filter_data: MediaFilterData | None = None
        if media is not None:
            media_filter_data = MediaFilterData.from_media(media=media)

        annotation_scene_filter_data: AnnotationSceneFilterData | None = None
        if annotation_scene is not None:
            annotation_scene_filter_data = AnnotationSceneFilterData.from_annotation_scene(
                annotation_scene=annotation_scene
            )

        return cls(
            media_identifier=media_identifier,
            media_filter_data=media_filter_data,
            annotation_scene_filter_data=annotation_scene_filter_data,
            media_annotation_state=media_annotation_state,
            preprocessing=preprocessing,
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"media_identifier={self.media_identifier}, "
            f"media_filter_data={self.media_filter_data}, "
            f"annotation_scene_filter_data={self.annotation_scene_filter_data}, "
            f"ephemeral={self.ephemeral})"
        )


class NullDatasetStorageFilterData(DatasetStorageFilterData):
    def __init__(self) -> None:
        super().__init__(media_identifier=NullMediaIdentifier(), preprocessing=MediaPreprocessingStatus.FINISHED)
