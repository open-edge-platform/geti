# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import logging
from collections.abc import Sequence

from service.label_schema_service import LabelSchemaService

from geti_kafka_tools import publish_event
from geti_telemetry_tools import unified_tracing
from geti_types import CTX_SESSION_VAR, ID, DatasetStorageIdentifier
from iai_core_py.entities.annotation import AnnotationScene, AnnotationSceneKind
from iai_core_py.entities.annotation_scene_state import AnnotationSceneState, AnnotationState
from iai_core_py.entities.label import Label
from iai_core_py.entities.label_schema import LabelSchema
from iai_core_py.entities.project import Project
from iai_core_py.repos import AnnotationSceneRepo, AnnotationSceneStateRepo, VideoRepo
from iai_core_py.repos.dataset_storage_filter_repo import DatasetStorageFilterRepo
from iai_core_py.utils.annotation_scene_state_helper import AnnotationSceneStateHelper
from iai_core_py.utils.iteration import grouper
from iai_core_py.utils.label_resolver import LabelResolver

logger = logging.getLogger(__name__)


class AnnotationManager:
    @staticmethod
    @unified_tracing
    def save_annotations(  # noqa: PLR0913
        annotation_scenes: Sequence[AnnotationScene],
        project: Project,
        dataset_storage_identifier: DatasetStorageIdentifier,
        label_schema: LabelSchema,
        label_schema_by_task: dict[ID, LabelSchema] | None = None,
        labels_to_revisit_per_annotation: Sequence[dict] | None = None,
        labels_to_revisit_full_scene: Sequence[set] | None = None,
        chunk_size: int = 16,
        calculate_task_to_revisit: bool = True,
    ) -> tuple[tuple[AnnotationScene, AnnotationSceneState, list[ID]], ...]:
        """
        Save one or more AnnotationScene to the repo.

        If the annotation is incomplete, missing labels are added (`LabelResolver.complete_labels`).
        The method also creates AnnotationSceneStates accordingly and publishes an event for each saved annotation.

        :param annotation_scenes: AnnotationScene objects to save
        :param project: Project containing the annotated media
        :param label_schema: Label schema relative to the project
        :param label_schema_by_task: Optional, dictionary with the label schema for each task node. If not provided,
            the label schema per task will be fetched from the database.
        :param dataset_storage_identifier: identifier of the dataset storage that contains the annotated media
        :param labels_to_revisit_full_scene: labels to revisit at full annotation scene level, for each scene
        :param labels_to_revisit_per_annotation: label to revisit per annotation, for each scene
        :param chunk_size: number of annotation scenes to process in a single batch
        :return: Tuple of N elements (N=number of annotation scenes) where each element is a tuple containing:
            - the persisted AnnotationScene object
            - the persisted AnnotationSceneState object
            - the list of task IDs of the tasks for which the annotations in the scene have to be revisited
        """
        ann_scene_repo = AnnotationSceneRepo(dataset_storage_identifier)
        ann_scene_state_repo = AnnotationSceneStateRepo(dataset_storage_identifier)
        if labels_to_revisit_per_annotation is None:
            labels_to_revisit_per_annotation = [{} for _ in range(len(annotation_scenes))]
        if labels_to_revisit_full_scene is None:
            labels_to_revisit_full_scene = [set() for _ in range(len(annotation_scenes))]

        # Complete annotations with missing labels
        for annotation_scene in annotation_scenes:
            for annotation in annotation_scene.annotations:
                annotation.set_labels(
                    LabelResolver.complete_labels(label_schema, annotation.get_labels(include_empty=True))
                )

        annotation_scenes_states: list[AnnotationSceneState] = []
        tasks_to_revisit: list[list[ID]] = []
        for ann_scenes_chunk, lbl_rev_per_ann_chunk, lbl_rev_full_scene_chunk in zip(
            grouper(annotation_scenes, chunk_size=chunk_size),
            grouper(labels_to_revisit_per_annotation, chunk_size=chunk_size),
            grouper(labels_to_revisit_full_scene, chunk_size=chunk_size),
        ):
            # Compute the annotation scene state for each scene in the chunk
            ann_scenes_states_chunk = [
                AnnotationSceneStateHelper.compute_annotation_scene_state(
                    annotation_scene=ann_scene,
                    project=project,
                    labels_to_revisit_per_annotation=lbl_rev_per_ann,
                    labels_to_revisit_full_scene=lbl_rev_full_scene,
                    label_schema_by_task=label_schema_by_task,
                )
                for ann_scene, lbl_rev_per_ann, lbl_rev_full_scene in zip(
                    ann_scenes_chunk, lbl_rev_per_ann_chunk, lbl_rev_full_scene_chunk
                )
            ]
            annotation_scenes_states.extend(ann_scenes_states_chunk)

            if calculate_task_to_revisit:
                # Compute the tasks to revisit in the chunk
                tasks_to_revisit_chunk = [
                    AnnotationManager._compute_tasks_to_revisit(
                        project=project,
                        annotation_scene_state=ann_scene_state,
                        label_schema_by_task=label_schema_by_task,
                    )
                    for ann_scene_state in ann_scenes_states_chunk
                ]
                tasks_to_revisit.extend(tasks_to_revisit_chunk)

            # Save annotations and states in the chunk
            ann_scene_repo.save_many(ann_scenes_chunk)
            ann_scene_state_repo.save_many(ann_scenes_states_chunk)

            # Publish Kafka events for each scene in the chunk
            for ann_scene in ann_scenes_chunk:
                AnnotationManager.publish_annotation_scene(
                    annotation_scene_id=ann_scene.id_,
                    project_id=dataset_storage_identifier.project_id,
                    workspace_id=dataset_storage_identifier.workspace_id,
                    dataset_storage_id=dataset_storage_identifier.dataset_storage_id,
                )

        if not calculate_task_to_revisit:
            tasks_to_revisit = [[] for _ in annotation_scenes]

        return tuple(
            (ann_scene, ann_scene_state, tasks_to_revisit_for_scene)
            for ann_scene, ann_scene_state, tasks_to_revisit_for_scene in zip(
                annotation_scenes, annotation_scenes_states, tasks_to_revisit
            )
        )

    @staticmethod
    def _compute_tasks_to_revisit(
        project: Project,
        annotation_scene_state: AnnotationSceneState,
        label_schema_by_task: dict[ID, LabelSchema] | None = None,
    ) -> list[ID]:
        """
        Returns the ID's of those tasks for which the Annotations in the
        AnnotationScene described by the AnnotationSceneState need to be revisited

        :param project: Project where the tasks are defined
        :param annotation_scene_state: AnnotationSceneState describing the state of
            the AnnotationScene
        :param label_schema_by_task: Optional, dictionary with the label schema for each task node. If not provided,
            the label schema per task will be fetched from the database.
        :return: list of task id's corresponding to the tasks that need revisiting
        """
        tasks_to_revisit: list[ID] = []
        for task in project.get_trainable_task_nodes():
            if label_schema_by_task is None:
                task_labels = LabelSchemaService.get_latest_labels_for_task(
                    project_identifier=project.identifier,
                    task_node_id=task.id_,
                    include_empty=True,
                )
                task_labels_ids = tuple(label.id_ for label in task_labels)
            else:
                task_labels_ids = tuple(
                    label.id_ for label in label_schema_by_task[task.id_].get_labels(include_empty=True)
                )
            if annotation_scene_state.is_media_to_revisit_for_task(task_labels_ids):
                tasks_to_revisit.append(task.id_)
        return tasks_to_revisit

    @staticmethod
    @unified_tracing
    def get_filtered_frame_annotation_scenes(  # noqa: PLR0913
        dataset_storage_identifier: DatasetStorageIdentifier,
        video_id: ID,
        annotation_kind: AnnotationSceneKind = AnnotationSceneKind.ANNOTATION,
        start_frame: int | None = None,
        end_frame: int | None = None,
        frameskip: int | None = None,
        limit: int | None = None,
        task_id: ID | None = None,
        model_ids: set[ID] | None = None,
    ) -> tuple[list[AnnotationScene], int]:
        """
        Gets the frame annotation scenes of the specified kind for the given video id.
        Additional parameter are used to filter the list of frames, if provided.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the video and annotations
        :param video_id: ID of the video to add the annotation to
        :param annotation_kind: Kind of the annotation to get. Defaults to use annotation type.
        :param start_frame: If searching within a range of frames, first index of the range (inclusive).
            A value of None is used to indicate the start of the video.
        :param end_frame: If searching within a range of frames, last index of the range (inclusive).
            A value of None is used to indicate the end of the video.
        :param frameskip: Stride to use for the search; only frames whose indices are multiple
            of this stride will be considered. If None, default to video fps.
        :param limit: number of annotation scenes to return
        :param task_id: ID of the task. only required if annotation scene kind is task_prediction.
        :param model_ids: ID of the models to be used for filtering. Only required for kind prediction
        :return Tuple containing:
          - list of annotation scenes/predictions
          - total number of matching annotation scenes/predictions, ignoring the limit
        """
        if frameskip is None:
            video = VideoRepo(dataset_storage_identifier).get_by_id(video_id)
            frameskip = int(video.fps)
        repo = AnnotationSceneRepo(dataset_storage_identifier)
        return repo.get_video_frame_annotations_by_video_id(
            video_id=video_id,
            annotation_kind=annotation_kind,
            task_id=task_id,
            model_ids=model_ids,
            start_frame=start_frame,
            end_frame=end_frame,
            frame_skip=frameskip,
            limit=limit,
        )

    @staticmethod
    def _suspend_annotations_by_labels_in_dataset_storage(
        project: Project,
        dataset_storage_identifier: DatasetStorageIdentifier,
        global_labels_to_revisit_if_present: Sequence[Label],
        global_labels_to_revisit_unconditionally: Sequence[Label],
        local_labels_to_revisit: Sequence[Label],
    ) -> tuple[ID, ...]:
        """
        Given a set of labels that were recently affected by a label schema change,
        update the revisit states of the annotation scene in the given dataset storage.

        :param project: Project containing the dataset storage
        :param dataset_storage_identifier: Identifier of the dataset storage
            containing the annotations
        :param global_labels_to_revisit_if_present: List of global labels whose
            annotation scene 'revisit' state must be updated for those annotations
            that contain these labels.
        :param global_labels_to_revisit_unconditionally: List of global labels whose
            annotation scene 'revisit' state must be updated for any annotation,
            regardless of whether it contains the label or not.
        :param local_labels_to_revisit: List of local labels whose annotation scene
            'revisit' state must be updated at the full ROI level.
        :return: Tuple with the IDs of the annotation scenes whose 'revisit' changed.
        """
        ann_scene_repo = AnnotationSceneRepo(dataset_storage_identifier)
        ann_scene_state_repo = AnnotationSceneStateRepo(dataset_storage_identifier)
        global_labels_ids_to_revisit_if_present = {label.id_ for label in global_labels_to_revisit_if_present}
        global_labels_ids_to_revisit_unconditionally = {label.id_ for label in global_labels_to_revisit_unconditionally}

        scenes = ann_scene_repo.get_all_by_kind(kind=AnnotationSceneKind.ANNOTATION)

        scenes_to_revisit_ids: set[ID] = set()

        # Iterate over all the annotation scenes
        for annotation_scene in scenes:
            # Fetch the current state and get its 'revisit' values
            old_annotation_scene_state = AnnotationSceneStateHelper.get_annotation_state_for_scene(
                annotation_scene=annotation_scene,
                dataset_storage_identifier=dataset_storage_identifier,
                project=project,
            )
            # Skip unannotated media
            state_media_level = old_annotation_scene_state.get_state_media_level()
            if state_media_level == AnnotationState.NONE:  # unannotated
                continue

            old_labels_to_revisit_per_ann = old_annotation_scene_state.labels_to_revisit_per_annotation
            old_labels_to_revisit_full_scene = old_annotation_scene_state.labels_to_revisit_full_scene

            # Compute the new 'revisit' state for each annotation and the whole roi
            new_labels_to_revisit_per_ann: dict[ID, set[ID]] = {}
            for annotation in annotation_scene.annotations:
                # If some labels were already to revisit, keep them as such
                old_labels_to_revisit_for_ann = old_labels_to_revisit_per_ann.get(annotation.id_, ())
                if old_labels_to_revisit_for_ann:
                    new_labels_to_revisit_per_ann[annotation.id_] = set(old_labels_to_revisit_for_ann)
                else:
                    new_labels_to_revisit_per_ann.setdefault(annotation.id_, set())
                # Finally add the newly affected labels as well
                for ann_label in annotation.get_labels():
                    if ann_label.id_ in global_labels_ids_to_revisit_if_present:
                        new_labels_to_revisit_per_ann[annotation.id_].add(ann_label.id_)
                new_labels_to_revisit_per_ann[annotation.id_].update(global_labels_ids_to_revisit_unconditionally)
                # If any label was set to revisit, store its ID
                if len(new_labels_to_revisit_per_ann[annotation.id_]) > len(old_labels_to_revisit_for_ann):
                    scenes_to_revisit_ids.add(annotation_scene.id_)

            # Compute the 'revisit' state at the full scene level
            new_labels_to_revisit_full_scene = old_labels_to_revisit_full_scene.union(
                label.id_ for label in local_labels_to_revisit
            )
            # If any label was set to revisit, store its ID
            if len(new_labels_to_revisit_full_scene) > len(old_labels_to_revisit_full_scene):
                scenes_to_revisit_ids.add(annotation_scene.id_)

            # Build the updated annotation scene state
            new_annotation_scene_state = AnnotationSceneStateHelper.compute_annotation_scene_state(
                annotation_scene=annotation_scene,
                project=project,
                labels_to_revisit_per_annotation=new_labels_to_revisit_per_ann,
                labels_to_revisit_full_scene=new_labels_to_revisit_full_scene,
            )
            ann_scene_state_repo.save(new_annotation_scene_state)

        return tuple(scenes_to_revisit_ids)

    @staticmethod
    def suspend_annotations_by_labels(
        project: Project,
        global_labels_to_revisit_if_present: Sequence[Label],
        global_labels_to_revisit_unconditionally: Sequence[Label],
        local_labels_to_revisit: Sequence[Label],
    ) -> dict[ID, tuple[ID, ...]]:
        """
        Given a set of labels that were recently affected by a label schema change,
        update the revisit states of the annotation scene in all dataset storages.

        :param project: Project
        :param global_labels_to_revisit_if_present: List of global labels whose
            annotation scene 'revisit' state must be updated for those annotations
            that contain these labels.
        :param global_labels_to_revisit_unconditionally: List of global labels whose
            annotation scene 'revisit' state must be updated for any annotation,
            regardless of whether it contains the label or not.
        :param local_labels_to_revisit: List of local labels whose annotation scene
            'revisit' state must be updated at the full ROI level.
        :return: Dict mapping each dataset storage to a tuple containing the IDs of
            the annotation scenes (in that storage) whose 'revisit' changed.
        """
        scene_to_revisit_ids_by_storage: dict[ID, tuple[ID, ...]] = {}
        for dataset_storage in project.get_dataset_storages():
            scene_to_revisit_ids = AnnotationManager._suspend_annotations_by_labels_in_dataset_storage(
                project=project,
                dataset_storage_identifier=dataset_storage.identifier,
                global_labels_to_revisit_if_present=global_labels_to_revisit_if_present,
                global_labels_to_revisit_unconditionally=global_labels_to_revisit_unconditionally,
                local_labels_to_revisit=local_labels_to_revisit,
            )
            dataset_storage_filter_repo = DatasetStorageFilterRepo(
                dataset_storage_identifier=dataset_storage.identifier
            )
            dataset_storage_filter_repo.update_annotation_scenes_to_revisit(
                annotation_scene_ids=scene_to_revisit_ids,
            )
            scene_to_revisit_ids_by_storage[dataset_storage.id_] = scene_to_revisit_ids
        return scene_to_revisit_ids_by_storage

    @staticmethod
    def publish_annotation_scene(
        annotation_scene_id: ID,
        project_id: ID,
        workspace_id: ID,
        dataset_storage_id: ID,
    ) -> None:
        """
        Publish an event to inform the other services about a new or modified annotation scene

        :param annotation_scene_id: ID of the annotation scene
        :param project_id: ID of the project
        :param workspace_id: ID of the workspace
        :param dataset_storage_id: ID of the dataset storage the scene belongs to
        """
        body = {
            "workspace_id": workspace_id,
            "project_id": project_id,
            "dataset_storage_id": dataset_storage_id,
            "annotation_scene_id": annotation_scene_id,
        }
        publish_event(
            topic="new_annotation_scene",
            body=body,
            key=str(annotation_scene_id).encode(),
            headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
        )
