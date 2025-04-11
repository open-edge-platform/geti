#
# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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
#

"""This module contains the MongoDB mapper for AnnotationSceneState related entities"""

from sc_sdk.entities.annotation_scene_state import AnnotationSceneState, AnnotationState
from sc_sdk.repos.mappers.mongodb_mapper_interface import IMapperSimple
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from sc_sdk.repos.mappers.mongodb_mappers.media_mapper import MediaIdentifierToMongo


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
