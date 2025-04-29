# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from sc_sdk.entities.dataset_item import DatasetItem
from sc_sdk.entities.image import Image
from sc_sdk.entities.video import VideoFrame
from sc_sdk.repos.mappers import DatetimeToMongo, IDToMongo, IMapperForward, MediaIdentifierToMongo
from sc_sdk.repos.mappers.mongodb_mappers.annotation_mapper import AnnotationToMongo, AnnotationToMongoForwardParameters
from sc_sdk.repos.mappers.mongodb_mappers.dataset_storage_filter_mapper import VideoFilterData, VideoFilterDataMapper
from sc_sdk.repos.mappers.mongodb_mappers.shape_mapper import ShapeToMongo, ShapeToMongoForwardParameters


class TrainingRevisionToMongo(IMapperForward[DatasetItem, dict]):
    """MongoDB mapper for `DatasetItem` entities"""

    @staticmethod
    def forward(instance: DatasetItem) -> dict:
        # By passing media height/width equal to 0, the ROI shape area parameters
        # will be left uninitialized
        roi_mapper_parameters = AnnotationToMongoForwardParameters(
            media_height=0,
            media_width=0,
        )
        shape_parameters = ShapeToMongoForwardParameters(
            media_width=instance.media.width,
            media_height=instance.media.height,
            include_coordinates=False,  # Skip storage of shape coordinates
        )
        if isinstance(instance.media, VideoFrame):
            upload_date = instance.media.video.creation_date  # type: ignore
            size = instance.media.video.size
            uploader_id = instance.media.video.uploader_id
            video_filter_data = VideoFilterDataMapper.forward(VideoFilterData.from_video(instance.media.video))
        elif isinstance(instance.media, Image):
            upload_date = instance.media.creation_date  # type: ignore
            uploader_id = instance.media.uploader_id
            size = instance.media.size
        else:
            raise ValueError(f"Unexpected media type for dataset item: {type(instance.media)}")

        result = {
            "_id": IDToMongo.forward(instance.id_),
            "media_identifier": MediaIdentifierToMongo.forward(instance.media_identifier),
            "roi": AnnotationToMongo.forward(
                instance.roi,
                parameters=roi_mapper_parameters,
            ),
            "subset": str(instance.subset),
            "media_name": instance.media.name,
            "media_extension": instance.media.extension.name,
            "media_width": instance.media.width,
            "media_height": instance.media.height,
            "size": size,
            "upload_date": DatetimeToMongo.forward(upload_date),
            "uploader_id": uploader_id,
            "user_name": instance.annotation_scene.last_annotator_id,
            "annotation_scene_id": IDToMongo.forward(instance.annotation_scene.id_),
            "annotations": [
                [{"shape": ShapeToMongo.forward(annotation.shape, parameters=shape_parameters)}]
                for annotation in instance.annotation_scene.annotations
            ],
            "label_ids": [
                IDToMongo.forward(label_id) for label_id in instance.annotation_scene.get_label_ids(include_empty=True)
            ],
            "creation_date": DatetimeToMongo.forward(instance.annotation_scene.creation_date),
        }
        if isinstance(instance.media, VideoFrame):
            result.update(video_filter_data)

        return result
