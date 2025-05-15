# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements export utilities
"""

import itertools
from typing import TYPE_CHECKING, Any

from geti_types import ID, ProjectIdentifier
from iai_core.entities.annotation import AnnotationSceneKind
from iai_core.entities.dataset_storage import DatasetStorage
from iai_core.entities.label import Domain
from iai_core.entities.label_schema import LabelGroup, LabelSchema
from iai_core.entities.project import Project
from iai_core.repos import AnnotationSceneRepo, ImageRepo, LabelRepo, LabelSchemaRepo, VideoRepo
from iai_core.utils.uid_generator import generate_uid
from jobs_common_extras.datumaro_conversion.definitions import GetiProjectType

from job.utils.import_utils import ImportUtils

if TYPE_CHECKING:
    from geti_types import MediaIdentifierEntity
__all__ = ["ExportUtils"]


# workaround to avoid pymongo aggregate error (DocumentTooLarge).
MAX_IDENTIFIERS = 10000


class ExportUtils:
    @staticmethod
    def build_label_schema_from_dataset_storage(
        dataset_storage: DatasetStorage,
        include_empty: bool = False,
    ) -> LabelSchema:
        """
        Build a dataset containing all the images and (latest) annotations in a
        dataset storage.

        Optionally, it's possible to exclude the unannotated images from the dataset.

        :param dataset_storage: Dataset storage containing images and annotations
        :param include_unannotated: Whether to include unannotated images or not
        :return: Dataset with images and annotations
        """
        annotation_scene_repo = AnnotationSceneRepo(dataset_storage.identifier)
        image_repo = ImageRepo(dataset_storage.identifier)
        video_repo = VideoRepo(dataset_storage.identifier)
        media_identifiers: list[MediaIdentifierEntity] = []
        media_identifiers.extend(image_repo.get_all_identifiers())
        media_identifiers.extend(video_repo.get_frame_identifiers())

        # workaround to avoid pymongo aggregate error (DocumentTooLarge).
        splits = [media_identifiers[i : i + MAX_IDENTIFIERS] for i in range(0, len(media_identifiers), MAX_IDENTIFIERS)]
        label_ids: set[ID] = set()
        for split in splits:
            latest = annotation_scene_repo.get_latest_annotations_by_kind_and_identifiers(
                media_identifiers=split,
                annotation_kind=AnnotationSceneKind.ANNOTATION,
            )
            label_ids.update(set(itertools.chain.from_iterable(scene.get_label_ids(include_empty) for scene in latest)))

        project_identifier = ProjectIdentifier(
            workspace_id=dataset_storage.workspace_id,
            project_id=dataset_storage.project_id,
        )
        label_repo = LabelRepo(project_identifier=project_identifier)
        label_list = [label_repo.get_by_id(label_id) for label_id in label_ids]
        label_group = LabelGroup(name="from_label_list", labels=list(label_list))

        return LabelSchema(id_=generate_uid(), label_groups=[label_group])

    @staticmethod
    def create_voc_label_map(label_schema: LabelSchema) -> dict[str, Any]:
        """
        For VOC action classification task, which is used for exporting
        task in the chaining scenario, we need to mark detection labels as
        primary labels and other labels as action labels

        NOTE: consider all non-detection labels actions instead of just
        children of a specific label. It is workaround, because
        schema = LabelSchemaRepo(workspace).get_by_id(dataset.label_schema_id)
        returns NullLabelSchema, so getting label relationships
        is impossible.

        :param dataset: SC Dataset
        :return: dictionary mapping primary label to list of action labels
        """
        labels = label_schema.get_labels(include_empty=False)
        primary_labels = set()
        action_labels = set()
        for label in labels:
            if label.domain in [Domain.DETECTION, Domain.ANOMALY_DETECTION]:
                primary_labels.add(label)
            else:
                action_labels.add(label)

        if not primary_labels:
            # If we don't have any detection labels, we just export as
            # classification
            primary_labels = action_labels
            action_labels = set()

        return {
            label.name: [
                label.color.rgb_tuple,
                [],
                [label.name for label in action_labels],
            ]
            for label in primary_labels
        }

    @staticmethod
    def determine_use_label_schema(project_type: GetiProjectType) -> bool:
        """
        Determines whether metadata should be stored depending on the task type.

        :param project_type: Geti project type
        :return: Boolean indicating whether metadata should be stored
        """
        return project_type in [
            GetiProjectType.CLASSIFICATION,
            GetiProjectType.ROTATED_DETECTION,
            GetiProjectType.ANOMALY_CLASSIFICATION,
            GetiProjectType.ANOMALY_DETECTION,
            GetiProjectType.ANOMALY_SEGMENTATION,
            GetiProjectType.CHAINED_DETECTION_CLASSIFICATION,
            GetiProjectType.CHAINED_DETECTION_SEGMENTATION,
        ]

    @staticmethod
    def get_task_type_with_labels(project: Project | None = None) -> list[list[Any]]:
        """
        Find label names for each task_node in the project

        :param project: if not None, extract label metadata from the project
        :return: a list of list [task_type, list of label names]
        """
        task_type_labels: list[list[Any]] = []
        if project is None:
            return task_type_labels

        label_schema_repo = LabelSchemaRepo(project.identifier)
        for task_node in project.task_graph.tasks:
            if not task_node.task_properties.is_trainable:
                continue
            task_type_name = ImportUtils.task_type_to_rest_api_string(task_node.task_properties.task_type)
            label_schema_view = label_schema_repo.get_latest_view_by_task(task_node_id=task_node.id_)
            task_labels = [label.name for label in label_schema_view.get_labels(include_empty=False)]
            task_type_labels.append([task_type_name, task_labels])

        return task_type_labels
