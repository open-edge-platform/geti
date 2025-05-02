#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

"""This module contains the MongoDB mapper for AnnotationSceneState related entities"""

from iai_core_py.entities.annotation_scene_state import AnnotationSceneState, AnnotationState
from iai_core_py.repos.mappers.mongodb_mapper_interface import IMapperSimple
from iai_core_py.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from iai_core_py.repos.mappers.mongodb_mappers.media_mapper import MediaIdentifierToMongo


class AnnotationSceneStateToMongo(IMapperSimple[AnnotationSceneState, dict]):
    """MongoDB mapper for `AnnotationSceneState` entities"""

    @staticmethod
    def forward(instance: AnnotationSceneState) -> dict:
        return {
            "_id": IDToMongo.forward(instance.id_),
            "media_identifier": MediaIdentifierToMongo.forward(instance.media_identifier),
            "annotation_scene_id": IDToMongo.forward(instance.annotation_scene_id),
            "state_per_task": [
                {
                    "task_id": IDToMongo.forward(task_id),
                    "annotation_state": str(annotation_state),
                }
                for task_id, annotation_state in instance.state_per_task.items()
            ],
            "unannotated_rois": [
                {
                    "task_id": IDToMongo.forward(task_id),
                    "roi_list": [IDToMongo.forward(roi_id) for roi_id in roi_id_list],
                }
                for task_id, roi_id_list in instance.unannotated_rois.items()
            ],
            "labels_to_revisit_per_annotation": [
                {
                    "annotation_id": IDToMongo.forward(ann_id),
                    "labels_ids": [IDToMongo.forward(label_id) for label_id in labels_to_revisit],
                }
                for ann_id, labels_to_revisit in instance.labels_to_revisit_per_annotation.items()
            ],
            "labels_to_revisit_full_scene": [
                IDToMongo.forward(label_id) for label_id in instance.labels_to_revisit_full_scene
            ],
            "media_annotation_state": str(instance.get_state_media_level()),
        }

    @staticmethod
    def backward(instance: dict) -> AnnotationSceneState:
        return AnnotationSceneState(
            media_identifier=MediaIdentifierToMongo.backward(instance["media_identifier"]),
            annotation_scene_id=IDToMongo.backward(instance["annotation_scene_id"]),
            annotation_state_per_task={
                IDToMongo.backward(annotation_state["task_id"]): AnnotationState[annotation_state["annotation_state"]]
                for annotation_state in instance["state_per_task"]
            },
            unannotated_rois={
                IDToMongo.backward(unannotated_roi_list["task_id"]): [
                    IDToMongo.backward(roi_id) for roi_id in unannotated_roi_list["roi_list"]
                ]
                for unannotated_roi_list in instance["unannotated_rois"]
            },
            id_=IDToMongo.backward(instance["_id"]),
            labels_to_revisit_per_annotation={
                IDToMongo.backward(ann_labels_item["annotation_id"]): [
                    IDToMongo.backward(label_id) for label_id in ann_labels_item["labels_ids"]
                ]
                for ann_labels_item in instance.get("labels_to_revisit_per_annotation", [])
            },
            labels_to_revisit_full_scene={
                IDToMongo.backward(label_id) for label_id in instance.get("labels_to_revisit_full_scene", [])
            },
            ephemeral=False,
        )
