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
import logging
from collections.abc import Mapping, Sequence

from communication.exceptions import AnnotationSceneNotFoundException, AnnotationsNotFoundException
from service.label_schema_service import LabelSchemaService

from geti_kafka_tools import publish_event
from geti_telemetry_tools import unified_tracing
from geti_types import CTX_SESSION_VAR, ID, DatasetStorageIdentifier, ImageIdentifier, MediaIdentifierEntity
from sc_sdk.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind, NullAnnotationScene
from sc_sdk.entities.annotation_scene_state import AnnotationSceneState, AnnotationState, NullAnnotationSceneState
from sc_sdk.entities.dataset_storage import DatasetStorage
from sc_sdk.entities.image import Image
from sc_sdk.entities.label import Label
from sc_sdk.entities.label_schema import LabelSchema
from sc_sdk.entities.project import Project
from sc_sdk.entities.scored_label import LabelSource, ScoredLabel
from sc_sdk.entities.shapes import Rectangle
from sc_sdk.entities.suspended_scenes import SuspendedAnnotationScenesDescriptor
from sc_sdk.repos import AnnotationSceneRepo, AnnotationSceneStateRepo, SuspendedAnnotationScenesRepo, VideoRepo
from sc_sdk.repos.dataset_storage_filter_repo import DatasetStorageFilterRepo
from sc_sdk.utils.annotation_scene_state_helper import AnnotationSceneStateHelper, AnnotationStatePerTask
from sc_sdk.utils.iteration import grouper
from sc_sdk.utils.label_resolver import LabelResolver

logger = logging.getLogger(__name__)


class AnnotationManager:
    @staticmethod
    @unified_tracing
    def get_annotation_scene_by_id(
        dataset_storage_identifier: DatasetStorageIdentifier,
        annotation_scene_id: ID,
        media_id: ID,
    ) -> AnnotationScene:
        """
        Get annotation scene by its id

        :param dataset_storage_identifier: Identifier of the dataset storage
            containing the annotation scene
        :param annotation_scene_id: ID of the annotation scene
        :param media_id: ID of the media which has the annotation scene
        :return: AnnotationScene with annotation_scene_id as the id
        :raises AnnotationSceneNotFoundException: when annotation scene with id
            annotation_scene_id is not found.
        """
        annotation_scene_repo = AnnotationSceneRepo(dataset_storage_identifier)
        annotation_scene = annotation_scene_repo.get_by_id(annotation_scene_id)
        if isinstance(annotation_scene, NullAnnotationScene) or annotation_scene.media_identifier.media_id != media_id:
            raise AnnotationSceneNotFoundException(annotation_scene_id)
        if annotation_scene.kind not in [
            AnnotationSceneKind.ANNOTATION,
            AnnotationSceneKind.INTERMEDIATE,
        ]:
            raise AnnotationSceneNotFoundException(
                annotation_scene_id=annotation_scene_id,
                annotation_kind=annotation_scene.kind,
            )
        return annotation_scene

    @staticmethod
    @unified_tracing
    def get_latest_annotation_scene_for_media(
        dataset_storage_identifier: DatasetStorageIdentifier,
        media_identifier: MediaIdentifierEntity,
    ) -> AnnotationScene:
        """
        Get the latest annotation scene by media identifier.

        :param dataset_storage_identifier: Identifier of the dataset storage
            containing the annotation scene
        :param media_identifier: MediaIdentifierEntity of the media
        :return: latest AnnotationScene for media
        """
        annotation_scene_repo = AnnotationSceneRepo(dataset_storage_identifier)

        annotation_scene = annotation_scene_repo.get_latest_annotation_by_kind_and_identifier(
            media_identifier, AnnotationSceneKind.ANNOTATION
        )
        if isinstance(annotation_scene, NullAnnotationScene):
            raise AnnotationsNotFoundException(media_identifier)

        return annotation_scene

    @staticmethod
    @unified_tracing
    def save_annotations(  # noqa: PLR0913
        annotation_scenes: Sequence[AnnotationScene],
        project: Project,
        dataset_storage_identifier: DatasetStorageIdentifier,
        label_schema: LabelSchema,
        label_schema_by_task: Mapping[ID, LabelSchema] | None = None,
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
    @unified_tracing
    def create_global_annotations_for_image(
        project: Project,
        dataset_storage_identifier: DatasetStorageIdentifier,
        image: Image,
        labels: list[Label],
        user_id: ID,
    ) -> dict[ID, AnnotationState]:
        """
        Create annotations for the image when it is uploaded with labels.

        :param project: Project to which the video belongs
        :param dataset_storage_identifier: Identifier of the dataset storage
        :param image: Image that is uploaded with labels
        :param labels: Labels that will be used to annotate the image
        :param user_id: ID of the user who created or updated the annotation
        return: For each trainable task in the project, annotation state of the uploaded image for that task
        """
        scored_labels = [
            ScoredLabel(
                label_id=label.id_, is_empty=label.is_empty, probability=1.0, label_source=LabelSource(user_id=user_id)
            )
            for label in labels
        ]
        annotations = [Annotation(shape=Rectangle.generate_full_box(), labels=scored_labels)]
        annotation_scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=ImageIdentifier(image_id=image.id_),
            media_height=image.height,
            media_width=image.width,
            id_=AnnotationSceneRepo.generate_id(),
            last_annotator_id=user_id,
            annotations=annotations,
        )

        label_schema = LabelSchemaService.get_latest_label_schema_for_project(project.identifier)

        _, annotation_scene_state, _ = AnnotationManager.save_annotations(
            annotation_scenes=[annotation_scene],
            project=project,
            dataset_storage_identifier=dataset_storage_identifier,
            label_schema=label_schema,
            calculate_task_to_revisit=False,
        )[0]
        return annotation_scene_state.state_per_task

    @staticmethod
    def get_media_states_per_task(
        dataset_storage_identifier: DatasetStorageIdentifier,
        media_identifiers: Sequence[MediaIdentifierEntity],
        project: Project,
    ) -> dict[MediaIdentifierEntity, AnnotationStatePerTask]:
        """
        For a list of media identifiers, get the annotation state per task.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the media
        :param media_identifiers: identifiers of the media to get the states for
        :param project: Project the media belong to
        :return: Dict containing the state per task for each media identifier.
        """
        return AnnotationSceneStateHelper.get_media_per_task_states_from_repo(
            media_identifiers=media_identifiers,
            dataset_storage_identifier=dataset_storage_identifier,
            project=project,
        )

    @staticmethod
    def get_annotation_state_information_for_scene(
        dataset_storage_identifier: DatasetStorageIdentifier,
        annotation_scene: AnnotationScene,
        project: Project,
    ) -> tuple[AnnotationSceneState, list[ID]]:
        """
        Returns the latest AnnotationSceneState for a given AnnotationScene

        :param dataset_storage_identifier: Identifier of the dataset storage
            containing the annotation_scene
        :param annotation_scene: AnnotationScene to get the state for
        :param project: Project to which the annotation_scene belongs
        :return: A tuple containing:
            - the AnnotationSceneState for the annotation_scene
            - a list of task_ids, holding the tasks that should be revisited for this
                annotation scene. If no tasks need revisiting, this list will be empty
        """
        annotation_scene_state = AnnotationSceneStateHelper.get_annotation_state_for_scene(
            annotation_scene=annotation_scene,
            dataset_storage_identifier=dataset_storage_identifier,
            project=project,
        )
        tasks_to_revisit = AnnotationManager._compute_tasks_to_revisit(
            project=project,
            annotation_scene_state=annotation_scene_state,
        )
        return annotation_scene_state, tasks_to_revisit

    @staticmethod
    def _compute_tasks_to_revisit(
        project: Project,
        annotation_scene_state: AnnotationSceneState,
        label_schema_by_task: Mapping[ID, LabelSchema] | None = None,
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
    def get_annotation_state_information_for_scenes(
        dataset_storage: DatasetStorage,
        annotation_scenes: Sequence[AnnotationScene],
        project: Project,
    ) -> tuple[list[AnnotationSceneState], list[list[ID]]]:
        """
        Returns the latest AnnotationSceneState's for a list of AnnotationScene
        instances

        :param dataset_storage: DatasetStorage to which the annotation_scenes belong
        :param annotation_scenes: list of AnnotationScene instances to get the states
            for
        :param project: Project to which the annotation_scenes belong
        :return: A tuple containing:
            - A list of AnnotationSceneState for the annotation_scenes. The states are
                sorted in the same order as the input list in `annotation_scenes`
            - a nested list of task_ids, holding the tasks that should be revisited for
                each annotation scene. If no tasks need revisiting for an annotation
                scene, the entry for that scene will be an empty list
        """
        annotation_scene_states_dict = AnnotationSceneStateHelper.get_annotation_states_for_scenes(
            annotation_scenes=annotation_scenes,
            dataset_storage=dataset_storage,
            project=project,
        )
        annotation_scene_states = [
            annotation_scene_states_dict.get(scene.id_, NullAnnotationSceneState()) for scene in annotation_scenes
        ]
        task_id_to_labels_map = {
            task.id_: [
                label.id_
                for label in LabelSchemaService.get_latest_labels_for_task(
                    project_identifier=project.identifier,
                    task_node_id=task.id_,
                    include_empty=False,
                )
            ]
            for task in project.get_trainable_task_nodes()
        }
        tasks_to_revisit_per_scene: list[list[ID]] = []
        for annotation_scene_state in annotation_scene_states:
            tasks_to_revisit: list[ID] = []
            for task_id, task_labels in task_id_to_labels_map.items():
                if annotation_scene_state.is_media_to_revisit_for_task(task_labels):
                    tasks_to_revisit.append(task_id)
            tasks_to_revisit_per_scene.append(tasks_to_revisit)
        return annotation_scene_states, tasks_to_revisit_per_scene

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
                for ann_label_id in annotation.get_label_ids():
                    if ann_label_id in global_labels_ids_to_revisit_if_present:
                        new_labels_to_revisit_per_ann[annotation.id_].add(ann_label_id)
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
    def publish_annotation_scenes_to_revisit(
        project_id: ID,
        scenes_to_revisit_ids_by_storage: Mapping[ID, Sequence[ID]],
    ) -> None:
        """
        Publish an event to inform the other microservices about new annotation scenes
        with suspended annotations.

        :param project_id: ID of the project containing the scenes
        :param scenes_to_revisit_ids_by_storage: Dict mapping each dataset storage ID to the list
            of IDs of scenes with annotations to revisit in that storage
        """
        workspace_id = CTX_SESSION_VAR.get().workspace_id
        for (
            dataset_storage_id,
            scenes_to_revisit_ids,
        ) in scenes_to_revisit_ids_by_storage.items():
            dataset_storage_identifier = DatasetStorageIdentifier(
                workspace_id=workspace_id,
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
            )
            repo = SuspendedAnnotationScenesRepo(dataset_storage_identifier)
            # Dump the list of scenes to the repo, and get a reference to the document
            suspended_scenes_desc = SuspendedAnnotationScenesDescriptor(
                id_=repo.generate_id(),
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
                scenes_ids=tuple(scenes_to_revisit_ids),
            )
            repo.save(suspended_scenes_desc)

            # Publish to Kafka topic
            publish_event(
                topic="annotation_scenes_to_revisit",
                body={
                    "workspace_id": workspace_id,
                    "project_id": project_id,
                    "dataset_storage_id": dataset_storage_id,
                    "suspended_scenes_descriptor_id": suspended_scenes_desc.id_,
                },
                key=str(suspended_scenes_desc.id_).encode(),
                headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
            )

    @staticmethod
    def publish_annotation_scene(
        annotation_scene_id: ID,
        project_id: ID,
        workspace_id: ID,
        dataset_storage_id: ID,
    ) -> None:
        """
        Publish an event to inform the other microservices about a new or modified annotation scene

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
