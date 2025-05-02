#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

"""This module contains the MongoDB mapper for Annotation entities"""

from dataclasses import dataclass

from iai_core_py.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from iai_core_py.repos.mappers.mongodb_mapper_interface import (
    IMapperForward,
    IMapperParametricForward,
    IMapperProjectIdentifierBackward,
)

from .id_mapper import IDToMongo
from .label_mapper import ScoredLabelToMongo
from .media_mapper import MediaIdentifierToMongo
from .primitive_mapper import DatetimeToMongo
from .shape_mapper import ShapeToMongo, ShapeToMongoForwardParameters
from geti_types import ID, ProjectIdentifier


class AnnotationSceneToMongo(
    IMapperForward[AnnotationScene, dict],
    IMapperProjectIdentifierBackward[AnnotationScene, dict],
):
    """MongoDB mapper for `AnnotationScene` entities"""

    @staticmethod
    def forward(instance: AnnotationScene) -> dict:
        annotation_to_mongo_parameters = AnnotationToMongoForwardParameters(
            media_width=instance.media_width,
            media_height=instance.media_height,
        )
        return {
            "_id": IDToMongo.forward(instance.id_),
            "kind": str(instance.kind),
            "creation_date": DatetimeToMongo.forward(instance.creation_date),
            "media_identifier": MediaIdentifierToMongo.forward(instance.media_identifier),
            "editor_name": instance.last_annotator_id,
            "annotations": [
                AnnotationToMongo.forward(
                    annotation,
                    parameters=annotation_to_mongo_parameters,
                )
                for annotation in instance.annotations
            ],
            "label_ids": [IDToMongo.forward(label_id) for label_id in instance.get_label_ids(include_empty=True)],
            "invalid_task_ids": [IDToMongo.forward(task_id) for task_id in instance.invalid_for_task_ids],
            "task_id": IDToMongo.forward(instance.task_id) if instance.task_id is not None else None,
            "media_height": instance.media_height,
            "media_width": instance.media_width,
            "model_ids": [
                IDToMongo.forward(model_id) for model_id in instance.get_model_ids(include_user_annotations=False)
            ],
        }

    @staticmethod
    def backward(instance: dict, project_identifier: ProjectIdentifier) -> AnnotationScene:
        annotations = []
        for annotation in instance["annotations"]:
            annotations.append(AnnotationToMongo.backward(annotation, project_identifier=project_identifier))

        media_identifier = MediaIdentifierToMongo.backward(instance["media_identifier"])

        invalid_task_ids = [IDToMongo.backward(task_id) for task_id in instance.get("invalid_task_ids", [])]

        creation_date = DatetimeToMongo.backward(instance.get("creation_date"))

        task_id = instance.get("task_id")
        if task_id is not None:
            task_id = ID(task_id)
        return AnnotationScene(
            kind=AnnotationSceneKind[instance["kind"]],
            media_identifier=media_identifier,
            media_height=instance.get("media_height"),  # type: ignore
            media_width=instance.get("media_width"),  # type: ignore
            id_=IDToMongo.backward(instance["_id"]),
            last_annotator_id=instance.get("editor_name", ""),
            creation_date=creation_date,
            annotations=annotations,
            invalid_task_ids=invalid_task_ids,
            task_id=task_id,
            ephemeral=False,
        )


@dataclass
class AnnotationToMongoForwardParameters:
    """Forward mapping parameters for `Annotation`"""

    media_height: int  # pixel
    media_width: int  # pixel


class AnnotationToMongo(
    IMapperParametricForward[Annotation, dict, AnnotationToMongoForwardParameters],
    IMapperProjectIdentifierBackward[Annotation, dict],
):
    """MongoDB mapper for `Annotation` entities"""

    @staticmethod
    def forward(
        instance: Annotation,
        parameters: AnnotationToMongoForwardParameters,
    ) -> dict:
        labels = [ScoredLabelToMongo.forward(label) for label in instance.get_labels(include_empty=True)]
        shape_parameters = ShapeToMongoForwardParameters(
            media_width=parameters.media_width, media_height=parameters.media_height
        )
        return {
            "_id": IDToMongo.forward(instance.id_),
            "shape": ShapeToMongo.forward(instance.shape, parameters=shape_parameters),
            "labels": labels,
        }

    @staticmethod
    def backward(instance: dict, project_identifier: ProjectIdentifier) -> Annotation:
        return Annotation(
            shape=ShapeToMongo.backward(instance["shape"]),
            labels=[
                ScoredLabelToMongo.backward(label, project_identifier=project_identifier)
                for label in instance.get("labels", [])
            ],
            id_=IDToMongo.backward(instance["_id"]),
        )
