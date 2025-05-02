# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from iai_core_py.entities.annotation_scene_state import AnnotationState
from iai_core_py.entities.dataset_storage_filter_data import (
    AnnotationSceneFilterData,
    DatasetStorageFilterData,
    MediaFilterData,
    ShapeFilterData,
    VideoFilterData,
)
from iai_core_py.entities.media import ImageExtensions, MediaPreprocessingStatus, VideoExtensions
from iai_core_py.entities.shapes import ShapeType
from iai_core_py.repos.mappers import DatetimeToMongo, IDToMongo, IMapperSimple, MediaIdentifierToMongo


class DatasetStorageFilterDataToMongo(IMapperSimple[DatasetStorageFilterData, dict]):
    """MongoDB mapper for DatasetStorageFilterData"""

    @staticmethod
    def forward(instance: DatasetStorageFilterData) -> dict:
        result = {
            "_id": IDToMongo.forward(instance.id_),
            "media_identifier": MediaIdentifierToMongo.forward(instance.media_identifier),
            "preprocessing": instance.preprocessing.value,
        }
        if instance.media_annotation_state is not None:
            result["media_annotation_state"] = instance.media_annotation_state.name

        if instance.media_filter_data is not None:
            result.update(MediaFilterDataMapper.forward(instance=instance.media_filter_data))
        if instance.annotation_scene_filter_data is not None:
            result.update(AnnotationSceneFilterDataMapper.forward(instance=instance.annotation_scene_filter_data))

        return result

    @staticmethod
    def backward(instance: dict) -> DatasetStorageFilterData:
        media_identifier = MediaIdentifierToMongo.backward(instance["media_identifier"])
        media_filter_data: MediaFilterData | None = None
        if "media_name" in instance:
            media_filter_data = MediaFilterDataMapper.backward(instance=instance)
        annotation_scene_filter_data: AnnotationSceneFilterData | None = None
        if "annotation_scene_id" in instance:
            annotation_scene_filter_data = AnnotationSceneFilterDataMapper.backward(instance=instance)
        media_annotation_state = instance.get("media_annotation_state")

        return DatasetStorageFilterData(
            media_identifier=media_identifier,
            media_filter_data=media_filter_data,
            annotation_scene_filter_data=annotation_scene_filter_data,
            media_annotation_state=(
                AnnotationState[media_annotation_state] if media_annotation_state is not None else None
            ),
            preprocessing=MediaPreprocessingStatus[instance["preprocessing"]]
            # TODO: remove in scope of CVS-163688
            if "preprocessing" in instance
            else MediaPreprocessingStatus.FINISHED,
            ephemeral=False,
        )


class MediaFilterDataMapper(IMapperSimple[MediaFilterData, dict]):
    """MongoDB mapper for MediaFilterData"""

    @staticmethod
    def forward(instance: MediaFilterData) -> dict:
        result = {
            "media_name": instance.media_name,
            "media_width": instance.media_width,
            "media_height": instance.media_height,
            "upload_date": instance.upload_date,
            "uploader_id": instance.uploader_id,
            "size": instance.size,
        }
        if instance.video_filter_data is not None:
            result.update(VideoFilterDataMapper.forward(instance=instance.video_filter_data))
        if instance.media_extension is not None:
            result["media_extension"] = instance.media_extension.name

        return result

    @staticmethod
    def backward(instance: dict) -> MediaFilterData:
        upload_date = DatetimeToMongo.backward(instance["upload_date"]) if instance["upload_date"] is not None else None
        video_filter_data = None
        if "frame_count" in instance:
            video_filter_data = VideoFilterDataMapper.backward(instance)

        media_extension: ImageExtensions | VideoExtensions | None = None
        if "frame_count" in instance and "media_extension" in instance:
            # After the migration script has run, media_extension will always exist and we can combine if statement
            # with the above if statement for video_filter_data
            media_extension = VideoExtensions[instance["media_extension"]]
        elif "media_extension" in instance:
            media_extension = ImageExtensions[instance["media_extension"]]

        return MediaFilterData(
            media_name=instance["media_name"],
            media_extension=media_extension,
            media_width=instance["media_width"],
            media_height=instance["media_height"],
            upload_date=upload_date,  # type: ignore
            uploader_id=instance["uploader_id"],
            size=instance["size"],
            video_filter_data=video_filter_data,
        )


class VideoFilterDataMapper(IMapperSimple[VideoFilterData, dict]):
    """MongoDB mapper for MediaFilterData"""

    @staticmethod
    def forward(instance: VideoFilterData) -> dict:
        return {
            "frame_count": instance.frame_count,
            "frame_stride": instance.frame_stride,
            "frame_rate": instance.frame_rate,
            "duration": instance.duration,
        }

    @staticmethod
    def backward(instance: dict) -> VideoFilterData:
        return VideoFilterData(
            frame_count=instance["frame_count"],
            frame_stride=instance["frame_stride"],
            frame_rate=instance["frame_rate"],
            duration=instance["duration"],
            unannotated_frames=instance.get("unannotated_frames"),
        )


class AnnotationSceneFilterDataMapper(IMapperSimple[AnnotationSceneFilterData, dict]):
    """MongoDB mapper for AnnotationSceneFilterData"""

    @staticmethod
    def forward(instance: AnnotationSceneFilterData) -> dict:
        return {
            "annotation_scene_id": IDToMongo.forward(instance.annotation_scene_id),
            "user_name": instance.user_name,
            "annotations": [{"shape": ShapeFilterDataMapper.forward(shape)} for shape in instance.shapes],
            "label_ids": [IDToMongo.forward(id_) for id_ in instance.label_ids],
            "creation_date": instance.creation_date,
        }

    @staticmethod
    def backward(instance: dict) -> AnnotationSceneFilterData:
        shapes = [ShapeFilterDataMapper.backward(annotation["shape"]) for annotation in instance["annotations"]]
        label_ids = [IDToMongo.backward(id_) for id_ in instance["label_ids"]]
        creation_date = (
            DatetimeToMongo.backward(instance["creation_date"]) if instance["creation_date"] is not None else None
        )

        return AnnotationSceneFilterData(
            annotation_scene_id=IDToMongo.backward(instance["annotation_scene_id"]),
            user_name=instance["user_name"],
            shapes=shapes,
            label_ids=label_ids,
            creation_date=creation_date,  # type: ignore
        )


class ShapeFilterDataMapper(IMapperSimple[ShapeFilterData, dict]):
    """MongoDB mapper for ShapeFilterData"""

    @staticmethod
    def forward(instance: ShapeFilterData) -> dict:
        return {
            "type": instance.shape_type.name,
            "area_percentage": instance.area_percentage,
            "area_pixel": instance.area_pixel,
        }

    @staticmethod
    def backward(instance: dict) -> ShapeFilterData:
        return ShapeFilterData(
            shape_type=ShapeType[instance["type"]],
            area_percentage=instance["area_percentage"],
            area_pixel=instance["area_pixel"],
        )
