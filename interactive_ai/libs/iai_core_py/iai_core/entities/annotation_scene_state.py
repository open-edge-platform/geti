"""This module implements the AnnotationSceneState entity"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import itertools
from collections import defaultdict
from collections.abc import Mapping
from enum import Enum

from iai_core.entities.persistent_entity import PersistentEntity
from iai_core.utils.type_helpers import SequenceOrSet

from geti_types import ID, MediaIdentifierEntity, NullMediaIdentifier, VideoIdentifier


class AnnotationState(Enum):
    """
    Describes an annotation state. AnnotationState is used for two separate cases:
    - To describe the per-task annotation state of an annotation scene
    - To describe the media level annotation state

    Some examples to clarify distinction between media level and task level state: Classification->Detection project

    Image with 2 bounding boxes, each labeled for classification too:
      - per-task annotation state: {detection: ANNOTATED, classification: ANNOTATED}
      - global media-level annotation state: ANNOTATED

    Image with 2 bounding boxes, only one labeled for classification:
      - per-task annotation state: {detection: ANNOTATED, classification: PARTIALLY_ANNOTATED}
      - global media-level annotation state: PARTIALLY_ANNOTATED

    Image with 2 bounding boxes, none labeled for classification:
      - per-task annotation state: {detection: ANNOTATED, classification: NONE}
      - global media-level annotation state: PARTIALLY_ANNOTATED

    Image with no annotations at all:
      - per-task annotation state: {detection: NONE, classification: NONE}
      - global media-level annotation state: NONE

    In any case when an AnnotationSceneState has one or more labels_to_revisit_full_scene
    all tasks will return annotation state TO_REVISIT

    """

    ANNOTATED = 0
    PARTIALLY_ANNOTATED = 1
    NONE = 2
    TO_REVISIT = 3

    def __str__(self) -> str:
        return str(self.name)


class AnnotationSceneState(PersistentEntity):
    """
    Describe the state of an annotation scene with respect to:
      - per-task annotation state (annotated, partially annotated, unannotated)
      - per-annotation per-label revisit state (i.e. whether the user should revisit it)

    AnnotationSceneState is linked to a media identifier and an annotation scene.

    :param id_: Unique ID for the annotation scene state instance
    :param media_identifier: Identifies the media the state belongs to. Either ImageIdentifier or VideoFrameIdentifier
    :param annotation_scene_id: ID of the Annotation scene the state is connected to
    :param annotation_state_per_task: For each task ID, specifies the AnnotationState for that task
    :param unannotated_rois: For each task ID, lists all the ROIs that are not annotated for that task
    :param labels_to_revisit_per_annotation: For each annotation, set of labels for which that annotation
        should be revisited by the user. If unspecified, no annotation is assumed to be to revisit.
    :param labels_to_revisit_full_scene: Set of labels to revisit at the full scene level.
        If unspecified, no label is assumed to be revisited.
    """

    def __init__(  # noqa: PLR0913
        self,
        id_: ID,
        media_identifier: MediaIdentifierEntity,
        annotation_scene_id: ID,
        annotation_state_per_task: dict[ID, AnnotationState],
        unannotated_rois: dict[ID, list[ID]],
        labels_to_revisit_per_annotation: Mapping[ID, SequenceOrSet[ID]] | None = None,
        labels_to_revisit_full_scene: SequenceOrSet[ID] | None = None,
        ephemeral: bool = True,
    ) -> None:
        if isinstance(media_identifier, VideoIdentifier):
            raise TypeError("Only VideoFrameIdentifier or ImageIdentifier have an AnnotationSceneState")
        super().__init__(id_=id_, ephemeral=ephemeral)
        self.media_identifier = media_identifier
        self.annotation_scene_id = annotation_scene_id
        self._annotation_state_per_task = annotation_state_per_task
        self.unannotated_rois = unannotated_rois
        self._labels_to_revisit_per_annotation = self._init_labels_to_revisit_per_annotation(
            labels_to_revisit_per_annotation
        )
        self._labels_to_revisit_full_scene: set[ID] = (
            set(labels_to_revisit_full_scene) if labels_to_revisit_full_scene else set()
        )

    @staticmethod
    def _init_labels_to_revisit_per_annotation(
        labels_to_revisit_per_annotation: Mapping[ID, SequenceOrSet[ID]] | None,
    ) -> defaultdict[ID, tuple[ID, ...]]:
        res: defaultdict[ID, tuple[ID, ...]] = defaultdict(tuple)
        if labels_to_revisit_per_annotation:
            for ann_id, label_ids in labels_to_revisit_per_annotation.items():
                res[ann_id] = tuple(label_ids)
        return res

    def get_state_media_level(self) -> AnnotationState:
        """
        Compute the annotation state on the media level. The state on the media level
        describes the annotation state  of the media for the entire task chain.

        :return: AnnotationState on the media level:
         - TO_REVISIT if there is at least 1 label in _labels_to_revisit_full_scene
         - NONE if there are no annotations or partial annotations at all
         - ANNOTATED if all tasks are annotated (there are no partially annotated or unannotated tasks)
         - PARTIALLY_ANNOTATED in all other cases
        """
        if len(self._labels_to_revisit_full_scene) > 0 or any(self._labels_to_revisit_per_annotation.values()):
            return AnnotationState.TO_REVISIT

        states = set(self._annotation_state_per_task.values())
        if all(state == AnnotationState.NONE for state in states):
            state = AnnotationState.NONE
        elif all(state == AnnotationState.ANNOTATED for state in states):
            state = AnnotationState.ANNOTATED
        else:
            state = AnnotationState.PARTIALLY_ANNOTATED
        return state

    @property
    def state_per_task(self) -> dict[ID, AnnotationState]:
        """
        Returns the annotation states
        """
        return self._annotation_state_per_task

    @state_per_task.setter
    def state_per_task(self, value: dict[ID, AnnotationState]):
        self._annotation_state_per_task = value

    @property
    def labels_to_revisit_per_annotation(self) -> dict[ID, tuple[ID, ...]]:
        """
        Returns the labels to revisit for each annotation
        """
        return self._labels_to_revisit_per_annotation

    @property
    def labels_to_revisit_full_scene(self) -> set[ID]:
        """
        Returns the labels to revisit at the full scene level
        """
        return self._labels_to_revisit_full_scene

    def is_annotation_to_revisit_for_task(self, annotation_id: ID, task_labels: SequenceOrSet[ID]) -> bool:
        """
        Check whether an annotation should be revisited for a given task.

        :param annotation_id: ID of the Annotation
        :param task_labels: Set of IDs of the labels belonging to the TaskNode
        :return: bool indicating if the annotation should be revisited for the task
        """
        return bool(set(task_labels) & set(self._labels_to_revisit_per_annotation[annotation_id]))

    def is_annotation_to_revisit(self, annotation_id: ID) -> bool:
        """
        Check whether an annotation should be revisited, for any label.

        :param annotation_id: ID of the Annotation
        :return: bool indicating if the annotation should be revisited
        """
        return len(self._labels_to_revisit_per_annotation[annotation_id]) > 0

    def is_media_to_revisit_at_scene_level_for_task(self, task_labels: SequenceOrSet[ID]) -> bool:
        """
        Check if the media should be revisited at the full scene level for a given task.

        Note that this only considers actions to be taken at the scene level
        (e.g. adding missing shapes), not annotation-specific operations.

        :param task_labels: Set of IDs of the labels belonging to the TaskNode
        :return: bool indicating if the media should be revisited for the task
        """
        return bool(set(task_labels) & set(self._labels_to_revisit_full_scene))

    def is_media_to_revisit_at_scene_level(self) -> bool:
        """
        Check if the media should be revisited at the full scene level, for any task.

        :return: bool indicating if the media should be revisited
        """
        return len(self._labels_to_revisit_full_scene) > 0

    def is_media_to_revisit_for_task(self, task_labels: SequenceOrSet[ID]) -> bool:
        """
        Check whether the media should be revisited for a given task.

        This includes both actions at the scene level and annotation-specific ones.

        :param task_labels: Set of IDs of the labels belonging to the TaskNode
        :return: bool indicating if the media should be revisited for the task
        """
        if self.is_media_to_revisit_at_scene_level_for_task(task_labels):
            return True

        labels_to_revisit: set[ID] = set(
            itertools.chain(*(ann_labels for ann_labels in self._labels_to_revisit_per_annotation.values()))
        )
        return bool(set(task_labels) & set(labels_to_revisit))

    def is_media_to_revisit(self) -> bool:
        """
        Check whether the media should be revisited.

        This includes both actions at the scene level and annotation-specific ones.

        :return: bool indicating if the media should be revisited
        """
        if self.is_media_to_revisit_at_scene_level():
            return True

        return any(self._labels_to_revisit_per_annotation.values())

    def __eq__(self, other: object):
        if not isinstance(other, AnnotationSceneState):
            return False
        return (
            self.media_identifier == other.media_identifier
            and self.annotation_scene_id == other.annotation_scene_id
            and self.state_per_task == other.state_per_task
            and self._labels_to_revisit_per_annotation == other._labels_to_revisit_per_annotation
            and self._labels_to_revisit_full_scene == other._labels_to_revisit_full_scene
            and self.id_ == other.id_
        )

    def __repr__(self) -> str:
        return (
            f"AnnotationSceneState({self.id_}, "
            f"media_identifier={self.media_identifier}, "
            f"annotation_scene_id={self.annotation_scene_id}, "
            f"state_per_task={self.state_per_task})"
        )


class NullAnnotationSceneState(AnnotationSceneState):
    """Represents 'AnnotationSceneState not found'"""

    def __init__(self) -> None:
        super().__init__(
            media_identifier=NullMediaIdentifier(),
            annotation_scene_id=ID(),
            annotation_state_per_task={},
            unannotated_rois={},
            id_=ID(),
            ephemeral=False,
        )

    def __repr__(self) -> str:
        return "NullAnnotationSceneState()"
