# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module is responsible for computing the AnnotationSceneState for an AnnotationScene
"""

import itertools
import logging
from collections.abc import Iterator, Mapping, Sequence
from random import shuffle
from typing import cast

from iai_core_py.entities.annotation import Annotation, AnnotationScene
from iai_core_py.entities.annotation_scene_state import AnnotationSceneState, AnnotationState, NullAnnotationSceneState
from iai_core_py.entities.dataset_storage import DatasetStorage
from iai_core_py.entities.label_schema import LabelSchema, LabelSchemaView, NullLabelSchema
from iai_core_py.entities.model_template import TaskType
from iai_core_py.entities.project import Project
from iai_core_py.entities.task_node import TaskNode
from iai_core_py.repos import AnnotationSceneStateRepo, ImageRepo, LabelSchemaRepo, VideoRepo
from iai_core_py.utils.iteration import grouper
from iai_core_py.utils.type_helpers import SequenceOrSet

from geti_types import ID, DatasetStorageIdentifier, MediaIdentifierEntity, MediaType

logger = logging.getLogger(__name__)


AnnotationStatePerTask = dict[ID, AnnotationState] | dict[ID, AnnotationState | None] | dict[ID, None]


class AnnotationSceneStateHelper:
    """
    Helper class that contains logic to compute AnnotationSceneState from AnnotationScene.
    """

    @staticmethod
    def compute_annotation_scene_state(
        annotation_scene: AnnotationScene,
        project: Project,
        labels_to_revisit_per_annotation: Mapping[ID, SequenceOrSet[ID]] | None = None,
        labels_to_revisit_full_scene: SequenceOrSet[ID] | None = None,
        label_schema_by_task: Mapping[ID, LabelSchema] | None = None,
    ) -> AnnotationSceneState:
        """
        Computes the AnnotationSceneState for a given annotation scene and task graph.

        Optionally it can also set the per-annotation and per-task pending states.

        :param annotation_scene: AnnotationScene to compute the AnnotationSceneState for
        :param project: Project where the scene is defined
        :param labels_to_revisit_per_annotation: For each annotation, set of labels for which that annotation
            should be revisited by the user. If unspecified, no annotation is assumed to be to revisit.
        :param labels_to_revisit_full_scene: Set of labels to revisit at the full scene level.
            If unspecified, no label is assumed to be revisited.
        :param label_schema_by_task: Optional, dictionary with the label schema for each task node. If not provided,
            the label schema per task will be fetched from the database.
        :return AnnotationSceneState
        """
        # TODO: this is working under the assumption that the task chain is always correct, i.e.,
        #       Detection -> Crop -> Segmentation, or Detection -> Crop -> Classification. This is okay for MVP, but
        #       will not be valid when we expose more task chain types.
        trainable_tasks = project.get_trainable_task_nodes()
        annotation_states = {}
        previous_task: TaskNode | None = None
        previous_task_label_schema: LabelSchema | None = None
        unannotated_rois: dict[ID, list[ID]] = {}

        label_schema_repo = LabelSchemaRepo(project.identifier)
        for task in trainable_tasks:
            task_label_schema: LabelSchema
            if label_schema_by_task is None:
                task_label_schema = label_schema_repo.get_latest_view_by_task(task_node_id=task.id_)
            else:
                task_label_schema = label_schema_by_task[task.id_]
            if isinstance(task_label_schema, NullLabelSchema):
                logger.error(
                    "Could not find label schema for task %s of project %s to compute the annotation scene state; "
                    "the output state will probably be incorrect",
                    task.id_,
                    project.id_,
                )
            if isinstance(task_label_schema, LabelSchemaView):
                task_label_schema = cast("LabelSchema", task_label_schema)
            (
                task_annotation_state,
                task_unannotated_rois,
            ) = AnnotationSceneStateHelper._compute_task_annotation_state(
                annotation_scene=annotation_scene,
                task=task,
                task_label_schema=task_label_schema,
                previous_task=previous_task,
                previous_task_label_schema=previous_task_label_schema,
            )
            annotation_states[task.id_] = task_annotation_state
            unannotated_rois[task.id_] = task_unannotated_rois
            previous_task = task
            previous_task_label_schema = task_label_schema
        return AnnotationSceneState(
            media_identifier=annotation_scene.media_identifier,
            annotation_scene_id=annotation_scene.id_,
            annotation_state_per_task=annotation_states,
            unannotated_rois=unannotated_rois,
            labels_to_revisit_per_annotation=labels_to_revisit_per_annotation,
            labels_to_revisit_full_scene=labels_to_revisit_full_scene,
            id_=AnnotationSceneStateRepo.generate_id(),
        )

    @staticmethod
    def _compute_task_annotation_state(
        annotation_scene: AnnotationScene,
        task: TaskNode,
        task_label_schema: LabelSchema,
        previous_task: TaskNode | None,
        previous_task_label_schema: LabelSchema | None,
    ) -> tuple[AnnotationState, list[ID]]:
        """
        Computes the AnnotationState of an AnnotationScene for a specific task. Checks the TaskType of the previous
        trainable task, and calls the correct function for the task. There are three possibilities and the proper
        method is called for each:

         - The task is the first or only trainable task
         - The previous trainable task is a local task and the task is local
         - The previous trainable task is a local task and the task is global

        :param annotation_scene: AnnotationScene to determine the state for
        :param task: task to determine the AnnotationState for
        :param task_label_schema: label schema relative to the task node
        :param previous_task: The trainable task that preceded the task
        :param previous_task_label_schema: label schema relative to the previous task node
        :return: a tuple containing:
            - AnnotationState that indicates the AnnotationState of the AnnotationScene for this specific task.
            - List of Annotation IDs of ROIs that are not annotated for this task
        """
        # TODO use task_type.is_local once added CVS-82933
        local_task_types = [task for task in TaskType if task.is_trainable and not task.is_global]

        if previous_task is None:
            task_annotation_state = AnnotationSceneStateHelper._compute_annotation_state_first_task(
                annotation_scene=annotation_scene,
                task_label_schema=task_label_schema,
            )
            task_unannotated_rois: list[ID] = []
        elif previous_task.task_properties.task_type in local_task_types and task.task_properties.task_type.is_global:
            (
                task_annotation_state,
                task_unannotated_rois,
            ) = AnnotationSceneStateHelper._compute_state_and_unannotated_rois_local_to_global(
                annotation_scene=annotation_scene,
                previous_task_label_schema=previous_task_label_schema,  # type: ignore[arg-type]
                current_task_label_schema=task_label_schema,
            )
        elif (
            previous_task.task_properties.task_type in local_task_types
            and task.task_properties.task_type in local_task_types
        ):
            (
                task_annotation_state,
                task_unannotated_rois,
            ) = AnnotationSceneStateHelper._compute_state_and_unannotated_rois_local_to_local(
                annotation_scene=annotation_scene,
                previous_task_label_schema=previous_task_label_schema,  # type: ignore[arg-type]
                current_task_label_schema=task_label_schema,
            )
        else:
            raise NotImplementedError(
                "At this moment annotation scene state is only supported for local->global and local->local."
            )
        return task_annotation_state, task_unannotated_rois

    @staticmethod
    def _compute_annotation_state_first_task(
        annotation_scene: AnnotationScene,
        task_label_schema: LabelSchema,
    ) -> AnnotationState:
        """
        For an AnnotationScene, computes the annotation state of this scene for a task that does
        not have a previous task before it. For such a task, the state is ANNOTATED
        if there are annotations with labels for the task, otherwise it is NONE.

        :param annotation_scene: AnnotationScene to get the annotation state of the first task for
        :param task_label_schema: Label schema of the task node to compute the annotation state for
        """
        task_labels = set(task_label_schema.get_label_ids(include_empty=True))
        scene_labels = set(annotation_scene.get_label_ids(include_empty=True))
        if task_labels.isdisjoint(scene_labels):
            return AnnotationState.NONE
        return AnnotationState.ANNOTATED

    @staticmethod
    def _compute_state_and_unannotated_rois_local_to_global(
        annotation_scene: AnnotationScene,
        previous_task_label_schema: LabelSchema,
        current_task_label_schema: LabelSchema,
    ) -> tuple[AnnotationState, list[ID]]:
        """
        For an annotation scene, computes the annotation state and unannotated roi's of this scene for a global task
        that was preceded by a local task.

         :param annotation_scene: AnnotationScene for which to check the annotation state
         :param previous_task_label_schema: Label schema of the previous (local) task
         :param current_task_label_schema: Label schema of the Current (global) task
         :return: a tuple of:
            - AnnotationState
            - List of Annotation IDs of ROIs that are not annotated for this task
        """
        previous_task_label_ids = previous_task_label_schema.get_label_ids(include_empty=True)
        current_task_label_ids = current_task_label_schema.get_label_ids(include_empty=True)

        first_task_annotations = annotation_scene.get_annotations_with_label_ids(previous_task_label_ids)
        previous_task_rois = [ann for ann in first_task_annotations if len(ann.get_labels(include_empty=False)) != 0]

        output_unannotated_rois: list[ID] = []
        for annotation in previous_task_rois:
            annotation_label_ids = annotation.get_label_ids(include_empty=True)
            if annotation_label_ids.isdisjoint(current_task_label_ids):
                output_unannotated_rois.append(annotation.id_)

        output_annotation_state = AnnotationSceneStateHelper._compute_task_state_from_unannotated_rois(
            unannotated_rois=output_unannotated_rois,
            all_rois=previous_task_rois,
            previous_task_is_annotated=bool(first_task_annotations),
        )
        return output_annotation_state, output_unannotated_rois

    @staticmethod
    def _compute_state_and_unannotated_rois_local_to_local(
        annotation_scene: AnnotationScene,
        previous_task_label_schema: LabelSchema,
        current_task_label_schema: LabelSchema,
    ) -> tuple[AnnotationState, list[ID]]:
        """
        For an annotation scene, computes the annotation state and unannotated roi's of this scene for a local task
        that was preceded by another local task.

         :param annotation_scene: AnnotationScene for which to check the annotation state
         :param previous_task_label_schema: Label schema of the previous (local) task
         :param current_task_label_schema: Label schema of the Current (local) task
         :return: a tuple of:
            - AnnotationState
              - NONE: If there are no labels in the entire annotation scene for the current task
              - PARTIALLY_ANNOTATED: If there are annotations for the task, but not all of the
                annotations of the previous task are also annotated for this task
              - ANNOTATED: If every annotation for the previous task also has a label for this task
            - List of Annotation IDs of ROIs that are not annotated for this task
        """
        previous_task_label_ids = previous_task_label_schema.get_label_ids(include_empty=True)
        current_task_label_ids = current_task_label_schema.get_label_ids(include_empty=True)

        first_task_annotations = annotation_scene.get_annotations_with_label_ids(previous_task_label_ids)
        second_task_annotations = annotation_scene.get_annotations_with_label_ids(current_task_label_ids)
        rois_from_previous_task = [
            ann for ann in first_task_annotations if len(ann.get_labels(include_empty=False)) != 0
        ]

        output_unannotated_rois: list[ID] = []
        for roi in rois_from_previous_task:
            for annotation in second_task_annotations:
                if roi.shape.intersects(annotation.shape):
                    # first task shape is annotated in second task, continue checking next shape
                    break
            else:
                # if the break clause is not triggered, that means the shape in the first task doesn't intersect with
                # any labels in the current task, so annotation state must be PARTIALLY_ANNOTATED
                output_unannotated_rois.append(roi.id_)

        output_annotation_state = AnnotationSceneStateHelper._compute_task_state_from_unannotated_rois(
            unannotated_rois=output_unannotated_rois,
            all_rois=rois_from_previous_task,
            previous_task_is_annotated=bool(first_task_annotations),
        )
        return output_annotation_state, output_unannotated_rois

    @staticmethod
    def _compute_task_state_from_unannotated_rois(
        unannotated_rois: list[ID],
        all_rois: list[Annotation],
        previous_task_is_annotated: bool,
    ) -> AnnotationState:
        """
        Compare the list of unannotated ROI IDs and the list of all ROIs and determine the annotation state.
        - If the previous task is annotated and no ROIs are unannotated, the annotation state for the task is ANNOTATED
        - If all ROIs are unannotated, the state for the task is NONE
        - Else, the state for the task is PARTIALLY_ANNOTATED

        :param unannotated_rois: List of the IDs of all unannotated ROIs
        :param all_rois: List of all ROIs
        :param previous_task_is_annotated: Boolean indicating whether the previous task is annotated
        :return: AnnotationState that indicates the annotation state of the task.
        """
        if previous_task_is_annotated and len(unannotated_rois) == 0:
            return AnnotationState.ANNOTATED
        if len(all_rois) == len(unannotated_rois):
            return AnnotationState.NONE
        return AnnotationState.PARTIALLY_ANNOTATED

    @staticmethod
    def get_media_per_task_states_from_repo(
        media_identifiers: Sequence[MediaIdentifierEntity],
        dataset_storage_identifier: DatasetStorageIdentifier,
        project: Project,
    ) -> dict[MediaIdentifierEntity, AnnotationStatePerTask]:
        """
        For a list of media identifiers, get the state of each media identifier per task.
        For images and video frames, the per-task state is taken immediately from the AnnotationSceneState.
        For videos, the state of a task is ANNOTATED if all frames within stride are ANNOTATED for that task, NONE if
        all frames within stride are NONE for that task, and PARTIALLY_ANNOTATED otherwise.

        :param media_identifiers: List of media identifiers to get the state for. image, frame and video identifiers are
        all allowed.
        :param dataset_storage_identifier: Identifier of the dataset storage containing the media
        :param project: Project to which the media identifiers belong
        :return: Annotation state per task for each media identifier
        """
        ann_scene_state_repo = AnnotationSceneStateRepo(dataset_storage_identifier)
        task_ids = [task.id_ for task in project.get_trainable_task_nodes()]
        # Split the media identifiers between image/frame and video
        image_and_video_frame_identifiers = [
            identifier
            for identifier in media_identifiers
            if identifier.media_type in (MediaType.IMAGE, MediaType.VIDEO_FRAME)
        ]
        video_identifiers = [identifier for identifier in media_identifiers if identifier.media_type == MediaType.VIDEO]

        media_states_per_task: dict[MediaIdentifierEntity, AnnotationStatePerTask] = {}

        # Determine the media level state of the image and video frame identifiers
        image_and_frame_states = ann_scene_state_repo.get_latest_by_media_identifiers(image_and_video_frame_identifiers)
        for identifier in image_and_video_frame_identifiers:
            if isinstance(image_and_frame_states[identifier], NullAnnotationSceneState):
                media_states_per_task[identifier] = dict.fromkeys(task_ids, AnnotationState.NONE)
            elif image_and_frame_states[identifier].get_state_media_level() == AnnotationState.TO_REVISIT:
                media_states_per_task[identifier] = dict.fromkeys(task_ids, AnnotationState.TO_REVISIT)
            else:
                media_states_per_task[identifier] = image_and_frame_states[identifier].state_per_task

        # Videos do not have a sensible annotation state as they do not have an annotation scene
        null_annotation_state: AnnotationStatePerTask = dict.fromkeys(task_ids)
        media_states_per_task.update(dict.fromkeys(video_identifiers, null_annotation_state))

        return media_states_per_task

    @staticmethod
    def get_unannotated_media_identifiers_in_dataset_storage(
        dataset_storage_identifier: DatasetStorageIdentifier,
        project: Project,
        max_unseen_media: int | None = None,
    ) -> Iterator[MediaIdentifierEntity]:
        """
        Returns an iterator with media identifiers in a project which do not have any annotations.
        This function checks for ImageIdentifier and VideoFrameIdentifier

        :param dataset_storage_identifier: Identifier of the dataset storage containing the media
        :param project: Project for which to get the identifiers
        :param max_unseen_media: maximum number of identifiers to be returned

        :return: Iterator with unannotated media identifiers.
        """

        def get_unannotated_iterators(limit: int | None = None):
            image_identifiers = ImageRepo(dataset_storage_identifier).get_all_identifiers()
            frame_identifiers = VideoRepo(dataset_storage_identifier).get_frame_identifiers()
            all_media_identifiers = itertools.chain(image_identifiers, frame_identifiers)

            media_identifiers_chunks = grouper(all_media_identifiers)

            for media_identifiers in media_identifiers_chunks:
                annotation_states = AnnotationSceneStateHelper.get_media_per_task_states_from_repo(
                    media_identifiers=media_identifiers,
                    dataset_storage_identifier=dataset_storage_identifier,
                    project=project,
                )

                unannotated_identifiers: list[MediaIdentifierEntity] = []
                for identifier, state_per_task in annotation_states.items():
                    if set(state_per_task.values()) == {AnnotationState.NONE}:
                        unannotated_identifiers.append(identifier)

                # make sure to yield exactly `limit` items if specified
                if limit is not None:
                    shuffle(unannotated_identifiers)
                    if limit <= len(unannotated_identifiers):
                        yield unannotated_identifiers[:limit]
                        break
                    limit -= len(unannotated_identifiers)
                yield unannotated_identifiers

        # chains the results and return as a flat iterator
        return itertools.chain.from_iterable(get_unannotated_iterators(limit=max_unseen_media))

    @staticmethod
    def get_annotation_states_for_scenes(
        annotation_scenes: Sequence[AnnotationScene],
        dataset_storage: DatasetStorage,
        project: Project,
    ) -> dict[ID, AnnotationSceneState]:
        """
        For each annotation scene ID in a list, get the most recent AnnotationSceneStates in the repo. If any state is
        not in the repo, compute it on the spot.

        :param annotation_scenes: List of annotation scenes for which to get the states
        :param dataset_storage: DatasetStorage the annotation states and scenes belong to
        :param project: Project for which to get the annotation states
        :return: Dict with a AnnotationSceneState for each annotation ID
        """
        annotation_state_repo = AnnotationSceneStateRepo(dataset_storage.identifier)
        annotation_scene_ids = [scene.id_ for scene in annotation_scenes]
        states = annotation_state_repo.get_latest_for_annotation_scenes(annotation_scene_ids=annotation_scene_ids)
        # In rare cases, annotation scene states can be missing. In that case, compute them on the spot.
        not_found_annotation_scene_ids = set(annotation_scene_ids).difference(set(states.keys()))
        for annotation_scene_id in not_found_annotation_scene_ids:
            logger.warning(
                "No annotation state was found for annotation with ID %s, so it was computed from the "
                "annotation scene.",
                annotation_scene_id,
            )
            state_not_found_scene = next(scene for scene in annotation_scenes if scene.id_ == annotation_scene_id)
            state = AnnotationSceneStateHelper.compute_annotation_scene_state(state_not_found_scene, project=project)
            annotation_state_repo.save(state)
            states[state_not_found_scene.id_] = state
        return states

    @staticmethod
    def get_annotation_state_for_scene(
        annotation_scene: AnnotationScene,
        dataset_storage_identifier: DatasetStorageIdentifier,
        project: Project | None = None,
    ) -> AnnotationSceneState:
        """
        For an annotation scene, get the most recent AnnotationSceneState in the repo. If it isn't in the repo,
        compute it from the annotation scene.

        :param annotation_scene: annotation scene for which to get the states
        :param dataset_storage_identifier: Identifier of the dataset storage
            the annotation state and scene belong to
        :param project: Optional, project containing the dataset storage. If provided,
            the annotation scene state will be generated on the fly when missing.
        :return: AnnotationSceneState for the annotation scene
        """
        annotation_state_repo = AnnotationSceneStateRepo(dataset_storage_identifier)
        annotation_state = annotation_state_repo.get_latest_for_annotation_scene(
            annotation_scene_id=annotation_scene.id_
        )
        # In rare cases, annotation scene states can be missing
        if isinstance(annotation_state, NullAnnotationSceneState):
            logger.warning(
                "No annotation state was found for annotation with ID %s",
                annotation_scene.id_,
            )
            # try to compute it on the spot, if the project is available
            if project is not None:
                annotation_state = AnnotationSceneStateHelper.compute_annotation_scene_state(
                    annotation_scene=annotation_scene, project=project
                )
                annotation_state_repo.save(annotation_state)

        return annotation_state
