# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from entities.reference_feature import ReferenceFeature, ReferenceMediaInfo
from entities.reference_feature_adapter import ReferenceFeatureAdapter
from repos.reference_feature_binary_repo import ReferenceFeatureBinaryRepo

from geti_types import ProjectIdentifier
from sc_sdk.repos.mappers import IDToMongo, IMapperForward, MediaIdentifierToMongo
from sc_sdk.repos.mappers.mongodb_mapper_interface import IMapperBackward


class MediaInfoToMongo(IMapperForward[ReferenceMediaInfo, dict], IMapperBackward[ReferenceMediaInfo, dict]):
    """MongoDB mapper for `MediaInfo` entities"""

    @staticmethod
    def forward(instance: ReferenceMediaInfo) -> dict:
        return {
            "dataset_storage_id": IDToMongo.forward(instance.dataset_storage_id),
            "annotation_scene_id": IDToMongo.forward(instance.annotation_scene_id),
            "media_identifier": MediaIdentifierToMongo.forward(instance.media_identifier),
        }

    @staticmethod
    def backward(instance: dict) -> ReferenceMediaInfo:
        return ReferenceMediaInfo(
            dataset_storage_id=IDToMongo.backward(instance["dataset_storage_id"]),
            annotation_scene_id=IDToMongo.backward(instance["annotation_scene_id"]),
            media_identifier=MediaIdentifierToMongo.backward(instance["media_identifier"]),
        )


class ReferenceFeatureToMongo(
    IMapperForward[ReferenceFeature, dict],
    IMapperBackward[ReferenceFeature, dict],
):
    """MongoDB mapper for `ReferenceFeature` entities"""

    @staticmethod
    def forward(instance: ReferenceFeature) -> dict:
        ref_feature_adapter = instance.reference_feature_adapter
        binary_filename = ref_feature_adapter.binary_filename if ref_feature_adapter else ""
        return {
            "_id": IDToMongo.forward(instance.label_id),
            "task_id": IDToMongo.forward(instance.task_id),
            "binary_filename": binary_filename,
            "media_info": MediaInfoToMongo.forward(instance.media_info),
        }

    @staticmethod
    def backward(instance: dict) -> ReferenceFeature:
        media_info_dict = instance["media_info"]
        media_info = ReferenceMediaInfo(
            dataset_storage_id=IDToMongo.backward(media_info_dict["dataset_storage_id"]),
            annotation_scene_id=IDToMongo.backward(media_info_dict["annotation_scene_id"]),
            media_identifier=MediaIdentifierToMongo.backward(media_info_dict["media_identifier"]),
        )
        project_identifier = ProjectIdentifier(
            workspace_id=IDToMongo.backward(instance["workspace_id"]),
            project_id=IDToMongo.backward(instance["project_id"]),
        )
        adapter = ReferenceFeatureAdapter(
            binary_repo=ReferenceFeatureBinaryRepo(identifier=project_identifier),
            binary_filename=instance["binary_filename"],
        )
        return ReferenceFeature(
            task_id=IDToMongo.backward(instance["task_id"]),
            label_id=IDToMongo.backward(instance["_id"]),
            media_info=media_info,
            reference_feature_adapter=adapter,
        )
