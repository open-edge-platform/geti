# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from typing import Any, cast

from communication.constants import MAX_N_ANNOTATIONS_RETURNED
from communication.exceptions import (
    AnnotationsNotFoundException,
    CurrentlyNotImplementedException,
    NotEnoughSpaceException,
)
from communication.limit_check_helpers import check_max_number_of_annotations_and_delete_extra
from communication.rest_data_validator import AnnotationRestValidator
from communication.rest_views.annotation_rest_views import AnnotationRESTViews
from communication.rest_views.video_annotation_range_rest_views import VideoAnnotationRangeRESTViews
from entities.video_annotation_properties import VideoAnnotationProperties
from managers.annotation_manager import AnnotationManager
from managers.project_manager import ProjectManager
from resource_management.media_manager import MediaManager
from service.label_schema_service import LabelSchemaService
from usecases.resolve_label_source_usecase import ResolveLabelSourceUseCase

from geti_telemetry_tools import unified_tracing
from geti_types import (
    ID,
    DatasetStorageIdentifier,
    ImageIdentifier,
    MediaIdentifierEntity,
    VideoFrameIdentifier,
    VideoIdentifier,
)
from iai_core_py.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from iai_core_py.entities.annotation_scene_state import AnnotationSceneState
from iai_core_py.entities.image import Image
from iai_core_py.entities.label_schema import LabelSchema
from iai_core_py.entities.model_template import TaskType
from iai_core_py.entities.project import Project
from iai_core_py.entities.scored_label import LabelSource, ScoredLabel
from iai_core_py.entities.shapes import Rectangle
from iai_core_py.entities.video import Video
from iai_core_py.entities.video_annotation_range import VideoAnnotationRange
from iai_core_py.repos import AnnotationSceneRepo, LabelSchemaRepo, VideoAnnotationRangeRepo, VideoRepo
from iai_core_py.utils.filesystem import check_free_space_for_operation

LATEST = "latest"


class AnnotationRESTController:
    @staticmethod
    def get_annotation(
        dataset_storage_identifier: DatasetStorageIdentifier,
        annotation_id: ID,
        media_identifier: MediaIdentifierEntity,
        label_only: bool = False,
    ) -> dict[str, Any]:
        """
        Get an annotation for an image or video frame.

        If annotation_id is 'latest', the newest annotations will be pulled. Otherwise,
        the specified annotation_id will be pulled.

        :param dataset_storage_identifier: Identifier of the dataset storage
            containing the media and its annotation
        :param annotation_id: ID of annotation
        :param media_identifier: MediaIdentifierEntity of image or video frame
        :param label_only: if set to true, do not return the shape
        :return: REST View or error responses
        """
        project = ProjectManager.get_project_by_id(project_id=dataset_storage_identifier.project_id)

        if annotation_id == LATEST:
            annotation_scene = AnnotationManager.get_latest_annotation_scene_for_media(
                dataset_storage_identifier=dataset_storage_identifier,
                media_identifier=media_identifier,
            )
        else:
            annotation_scene = AnnotationManager.get_annotation_scene_by_id(
                dataset_storage_identifier=dataset_storage_identifier,
                annotation_scene_id=annotation_id,
                media_id=media_identifier.media_id,
            )

        if not annotation_scene.annotations:
            raise AnnotationsNotFoundException(media_identifier=media_identifier)

        (
            annotation_scene_state,
            tasks_to_revisit,
        ) = AnnotationManager.get_annotation_state_information_for_scene(
            dataset_storage_identifier=dataset_storage_identifier,
            annotation_scene=annotation_scene,
            project=project,
        )

        is_rotated_detection = AnnotationRESTController._project_is_rotated_detection_task(project)
        deleted_label_ids = LabelSchemaRepo(project.identifier).get_deleted_label_ids()

        return AnnotationRESTViews.media_2d_annotation_to_rest(
            annotation_scene=annotation_scene,
            label_only=label_only,
            annotation_scene_state=annotation_scene_state,
            tasks_to_revisit=tasks_to_revisit,
            is_rotated_detection=is_rotated_detection,
            deleted_label_ids=deleted_label_ids,
        )

    @staticmethod
    def make_image_annotation(
        dataset_storage_identifier: DatasetStorageIdentifier,
        image_id: ID,
        data: dict,
        user_id: ID,
    ) -> dict[str, Any]:
        """
        Create a new annotation for a given image.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the image
        :param image_id: ID of the image to add the annotation to
        :param data: Dictionary containing the annotation data
        :param user_id: ID of the user who created or updated the annotation
        :return: REST View or error responses
        """
        check_free_space_for_operation(operation="Annotate image", exception_type=NotEnoughSpaceException)

        image_identifier = ImageIdentifier(image_id=image_id)
        check_max_number_of_annotations_and_delete_extra(
            dataset_storage_identifier=dataset_storage_identifier,
            media_identifier=image_identifier,
        )

        project = ProjectManager.get_project_by_id(project_id=dataset_storage_identifier.project_id)

        image = MediaManager.get_image_by_id(dataset_storage_identifier, image_id)

        (
            annotation_scene,
            annotation_scene_state,
            tasks_to_revisit,
        ) = AnnotationRESTController._make_annotation_scene_for_2d_media(
            data=data,
            dataset_storage_identifier=dataset_storage_identifier,
            media=image,
            media_identifier=image.media_identifier,
            project=project,
            user_id=user_id,
        )

        is_rotated_detection = AnnotationRESTController._project_is_rotated_detection_task(project)
        return AnnotationRESTViews.media_2d_annotation_to_rest(
            annotation_scene,
            annotation_scene_state=annotation_scene_state,
            tasks_to_revisit=tasks_to_revisit,
            is_rotated_detection=is_rotated_detection,
        )

    @staticmethod
    @unified_tracing
    def _make_annotation_scene_for_2d_media(
        data: dict,
        dataset_storage_identifier: DatasetStorageIdentifier,
        media: Image | Video,
        media_identifier: MediaIdentifierEntity,
        project: Project,
        user_id: ID,
    ) -> tuple[AnnotationScene, AnnotationSceneState, list[ID]]:
        project_label_schema = LabelSchemaService.get_latest_label_schema_for_project(project.identifier)
        label_schema_by_task = {
            task_node.id_: LabelSchemaService.get_latest_label_schema_for_task(
                project_identifier=project.identifier,
                task_node_id=task_node.id_,
            )
            for task_node in project.get_trainable_task_nodes()
        }
        label_per_id = {
            label.id_: label
            for label_schema in label_schema_by_task.values()
            for label in label_schema.get_labels(include_empty=True)
        }

        AnnotationRestValidator().validate_annotation_scene(
            annotation_scene_rest=data,
            project=project,
            media_identifier=media_identifier,
            media_height=media.height,
            media_width=media.width,
            label_schema_by_task=label_schema_by_task,
        )

        (
            annotation_scene,
            annotation_revisit_state,
        ) = AnnotationRESTViews.media_2d_annotation_from_rest(
            annotation_dict=data,
            label_per_id=label_per_id,  # type: ignore
            kind=AnnotationSceneKind.ANNOTATION,
            last_annotator_id=user_id,
            media_identifier=media_identifier,
            media_height=media.height,
            media_width=media.width,
        )

        ResolveLabelSourceUseCase.resolve_label_source_for_annotations(
            annotation_scene=annotation_scene,
            dataset_storage_identifier=dataset_storage_identifier,
            user_id=user_id,
        )
        # TODO: can be sped up by only using label_schema_by_task and not project_label_schema
        #   we can then remove the call to project_label_schema altogether in _make_annotation_scene_for_2d_media
        return AnnotationManager.save_annotations(
            annotation_scenes=[annotation_scene],
            project=project,
            dataset_storage_identifier=dataset_storage_identifier,
            label_schema=project_label_schema,
            label_schema_by_task=label_schema_by_task,
            labels_to_revisit_per_annotation=[annotation_revisit_state.labels_to_revisit_per_annotation],
            labels_to_revisit_full_scene=[annotation_revisit_state.labels_to_revisit_full_scene],
        )[0]

    # Video frame annotations
    @staticmethod
    def get_video_frame_annotations(  # noqa: PLR0913
        project_id: ID,
        dataset_storage_id: ID,
        video_id: ID,
        annotation_id: ID,
        label_only: bool = True,
        start_frame: int | None = None,
        end_frame: int | None = None,
        frameskip: int = 1,
        limit_annotations: int = MAX_N_ANNOTATIONS_RETURNED,
    ) -> dict[str, Any]:
        """
        Get all latest annotations for all frames in a given video.

        This makes it possible to pull a different annotation revision over REST.

        :param project_id: The project's id to get the video frame annotations for
        :param dataset_storage_id: The DS containing video frame
        :param video_id: ID of video
        :param annotation_id: ID of annotation
        :param label_only: if set to true, do not return the shape of the annotation
        :param start_frame: If searching within a range of frames, first index of the range (inclusive).
            A value of None is used to indicate the start of the video.
        :param end_frame: If searching within a range of frames, last index of the range (inclusive).
            A value of None is used to indicate the end of the video.
        :param frameskip: Stride to use for the search; only frames whose indices are multiple
            of this stride will be considered.
        :param limit_annotations: max number of annotations to return per page
        :return: REST View or 404 response
        """

        if annotation_id != LATEST:
            raise CurrentlyNotImplementedException(message="Only latest annotation can be served currently")

        project = ProjectManager.get_project_by_id(project_id=project_id)
        dataset_storage = ProjectManager.get_dataset_storage_by_id(project, dataset_storage_id)
        is_rotated_detection = AnnotationRESTController._project_is_rotated_detection_task(project)
        deleted_label_ids = LabelSchemaRepo(project.identifier).get_deleted_label_ids()

        annotation_scenes, total_matching_annotation_scenes = AnnotationManager.get_filtered_frame_annotation_scenes(
            dataset_storage_identifier=dataset_storage.identifier,
            video_id=video_id,
            start_frame=start_frame,
            end_frame=end_frame,
            frameskip=frameskip,
            limit=limit_annotations,
        )

        actual_start_frame: int | None = None
        actual_end_frame: int | None = None
        if annotation_scenes:
            start_identifier = annotation_scenes[0].media_identifier
            end_identifier = annotation_scenes[-1].media_identifier
            actual_start_frame = (
                start_identifier.frame_index if isinstance(start_identifier, VideoFrameIdentifier) else None
            )
            actual_end_frame = end_identifier.frame_index if isinstance(end_identifier, VideoFrameIdentifier) else None

        if len(annotation_scenes) == 0:
            raise AnnotationsNotFoundException(media_identifier=VideoIdentifier(video_id=video_id))

        (
            annotation_scene_states,
            tasks_to_revisit_per_scene,
        ) = AnnotationManager.get_annotation_state_information_for_scenes(
            dataset_storage=dataset_storage,
            annotation_scenes=annotation_scenes,
            project=project,
        )

        video_annotation_properties = VideoAnnotationProperties(
            total_count=len(annotation_scenes),
            start_frame=actual_start_frame,
            end_frame=actual_end_frame,
            total_requested_count=total_matching_annotation_scenes,
            requested_start_frame=start_frame,
            requested_end_frame=end_frame,
        )
        return AnnotationRESTViews.media_2d_annotations_to_rest(
            annotation_scenes=annotation_scenes,
            label_only=label_only,
            annotation_scene_states=annotation_scene_states,
            tasks_to_revisit_per_scene=tasks_to_revisit_per_scene,
            is_rotated_detection=is_rotated_detection,
            deleted_label_ids=deleted_label_ids,
            annotation_properties=video_annotation_properties,
        )

    @staticmethod
    def get_video_range_annotation(
        dataset_storage_identifier: DatasetStorageIdentifier,
        video_id: ID,
    ) -> dict[str, Any]:
        """
        Get the latest video annotation range for a given video.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the video
        :param video_id: ID of video
        :return: JSON representation of the retrieved video annotation range
        """
        video_ann_range_repo = VideoAnnotationRangeRepo(dataset_storage_identifier)
        video_ann_range = video_ann_range_repo.get_latest_by_video_id(video_id=video_id)

        return VideoAnnotationRangeRESTViews.video_annotation_range_to_rest(video_annotation_range=video_ann_range)

    @staticmethod
    def make_video_range_annotation(
        video_annotation_range_data: dict[str, Any],
        dataset_storage_identifier: DatasetStorageIdentifier,
        video_id: ID,
        user_id: ID,
        skip_frame: int = 0,
    ) -> dict[str, Any]:
        """
        Create a video annotation range.

        Range annotations are only allowed for classification or anomaly task projects.

        :param video_annotation_range_data: JSON representation of the video annotation range to create
        :param dataset_storage_identifier: Identifier of the dataset storage that contains the video
        :param user_id: ID of the user who submitted the annotation
        :param video_id: ID of the annotated video
        :param skip_frame: Stride to use for annotating frames; only frames whose indices are multiple of this
            value will be annotated. If 0, the video FPS will be used as value instead.
        :return: JSON representation of the created video annotation range.
        """
        check_free_space_for_operation(operation="Annotate video frame range", exception_type=NotEnoughSpaceException)

        project = ProjectManager.get_project_by_id(project_id=dataset_storage_identifier.project_id)
        label_schema = LabelSchemaService.get_latest_label_schema_for_project(project.identifier)
        video = VideoRepo(dataset_storage_identifier).get_by_id(video_id)

        # Validate the request payload
        AnnotationRestValidator().validate_video_annotation_range(
            video_annotation_range_rest=video_annotation_range_data,
            label_schema=label_schema,
            video_total_frames=video.total_frames,
        )

        # Validate the project type
        # If this condition is changed, please modify `export_dataset_task` @ dataset_ie job.
        tasks = project.get_trainable_task_nodes()
        if not (len(tasks) == 1 and (tasks[0].task_properties.is_global or tasks[0].task_properties.is_anomaly)):
            raise NotImplementedError("Only single global/anomaly task projects can upload a VideoAnnotationRange")

        # Fetch the latest VideoAnnotationRange for the video, if any
        video_ann_range_repo = VideoAnnotationRangeRepo(dataset_storage_identifier)
        old_video_ann_range = video_ann_range_repo.get_latest_by_video_id(video_id=video_id)

        # Parse and save the new VideoAnnotationRange
        new_video_ann_range = VideoAnnotationRangeRESTViews.video_annotation_range_from_rest(
            video_annotation_range_data=video_annotation_range_data, video_id=video_id
        )
        video_ann_range_repo.save(new_video_ann_range)

        # Create AnnotationScene objects for the key frames, where necessary
        AnnotationRESTController.create_annotations_for_video_range(
            new_video_annotation_range=new_video_ann_range,
            old_video_annotation_range=old_video_ann_range,
            video=video,
            project=project,
            dataset_storage_identifier=dataset_storage_identifier,
            label_schema=label_schema,
            user_id=user_id,
            skip_frame=(skip_frame if skip_frame else int(video.fps)),
        )

        return VideoAnnotationRangeRESTViews.video_annotation_range_to_rest(video_annotation_range=new_video_ann_range)

    @staticmethod
    @unified_tracing
    def create_annotations_for_video_range(  # noqa: PLR0913
        new_video_annotation_range: VideoAnnotationRange,
        old_video_annotation_range: VideoAnnotationRange,
        video: Video,
        project: Project,
        dataset_storage_identifier: DatasetStorageIdentifier,
        label_schema: LabelSchema,
        user_id: ID,
        skip_frame: int,
    ) -> None:
        """
        Create and save AnnotationScene objects based on a VideoAnnotationRange at the desired stride.

        :param new_video_annotation_range: VideoAnnotationRange object to use as a reference to create the annotations
        :param old_video_annotation_range: Previous VideoAnnotationRange object, used to determine which annotations
            already exist (and can be reused) and which must be created from scratch.
        :param video: Video relative to the VideoAnnotationRange
        :param project: Project that contains the video
        :param dataset_storage_identifier: Identifier of the dataset storage that contains the video
        :param label_schema: Current LabelSchema for the project
        :param user_id: ID of the user who submitted the annotation
        :param skip_frame: interval at which to create annotations
        """

        def create_ann_scene_for_frame(frame_index: int, label_ids: set[ID]) -> AnnotationScene:
            media_identifier = VideoFrameIdentifier(
                video_id=video.id_,
                frame_index=frame_index,
            )
            if label_ids:
                scored_labels = [
                    ScoredLabel(
                        label_id=label_id,
                        probability=1,
                        label_source=label_source,
                    )
                    for label_id in label_ids
                ]
                annotations = [Annotation(shape=full_box_rect, labels=scored_labels)]
            else:
                annotations = []
            return AnnotationScene(
                kind=AnnotationSceneKind.ANNOTATION,
                media_identifier=media_identifier,
                media_height=video.height,
                media_width=video.width,
                id_=AnnotationSceneRepo.generate_id(),
                last_annotator_id=user_id,
                annotations=annotations,
            )

        full_box_rect = Rectangle.generate_full_box()
        label_source = LabelSource(user_id=user_id)
        label_schema_by_task = {
            task_node.id_: LabelSchemaService.get_latest_label_schema_for_task(
                project_identifier=project.identifier, task_node_id=task_node.id_
            )
            for task_node in project.get_trainable_task_nodes()
        }
        ann_scene_repo = AnnotationSceneRepo(dataset_storage_identifier)

        # Iterate over the key points, i.e. frames indices that are a multiple of the skip_frame
        annotations_to_save = []
        for key_frame_index in range(0, video.total_frames, skip_frame):
            labels_new = new_video_annotation_range.get_labels_at_frame_index(key_frame_index)
            labels_old = old_video_annotation_range.get_labels_at_frame_index(key_frame_index)
            # Create/update the annotations for key frames if the new labels are different from the previous ones
            if labels_new != labels_old:
                annotation_scene = create_ann_scene_for_frame(frame_index=key_frame_index, label_ids=labels_new)
                annotations_to_save.append(annotation_scene)
            # If there are annotations for non-key frames between this key point and the next one, update them
            non_key_annotations, _ = ann_scene_repo.get_video_frame_annotations_by_video_id(
                video_id=video.id_,
                start_frame=key_frame_index + 1,
                end_frame=min(key_frame_index + skip_frame, video.total_frames) - 1,
                annotation_kind=AnnotationSceneKind.ANNOTATION,
            )

            for non_key_ann_scene in non_key_annotations:
                ann_scene_label_ids = non_key_ann_scene.get_label_ids(include_empty=True)
                if ann_scene_label_ids == labels_new:
                    continue
                non_key_frame_index = cast("VideoFrameIdentifier", non_key_ann_scene.media_identifier).frame_index
                annotation_scene = create_ann_scene_for_frame(frame_index=non_key_frame_index, label_ids=labels_new)
                annotations_to_save.append(annotation_scene)
        AnnotationManager.save_annotations(
            annotation_scenes=annotations_to_save,
            project=project,
            dataset_storage_identifier=dataset_storage_identifier,
            label_schema=label_schema,
            label_schema_by_task=label_schema_by_task,
            calculate_task_to_revisit=False,
        )

    @staticmethod
    def make_video_frame_annotation(
        data: dict,
        dataset_storage_identifier: DatasetStorageIdentifier,
        video_id: ID,
        frame_index: int,
        user_id: ID,
    ) -> dict[str, Any]:
        """
        Create an annotation for a video frame.

        :param data: rest view of an annotation
        :param dataset_storage_identifier: Identifier of the dataset storage containing the video
        :param video_id: ID of the video to add the annotation to
        :param frame_index: index of the frame in the video
        :param user_id: ID of the user who created or updated the annotation
        :return: REST view or error response
        """
        # Get video and validate that video frame exists.
        video = MediaManager.validate_video_frame_exists(
            dataset_storage_identifier=dataset_storage_identifier,
            video_id=video_id,
            frame_index=frame_index,
        )
        media_identifier = VideoFrameIdentifier(video_id=video_id, frame_index=frame_index)

        check_max_number_of_annotations_and_delete_extra(
            dataset_storage_identifier=dataset_storage_identifier,
            media_identifier=media_identifier,
        )

        check_free_space_for_operation(operation="Annotate video frame", exception_type=NotEnoughSpaceException)

        project = ProjectManager.get_project_by_id(project_id=dataset_storage_identifier.project_id)
        is_rotated_detection = AnnotationRESTController._project_is_rotated_detection_task(project)

        (
            annotation_scene,
            annotation_scene_state,
            tasks_to_revisit,
        ) = AnnotationRESTController._make_annotation_scene_for_2d_media(
            data=data,
            dataset_storage_identifier=dataset_storage_identifier,
            media=video,
            media_identifier=media_identifier,
            project=project,
            user_id=user_id,
        )

        # If it is a single global task project, update the VideoAnnotationRange for the
        # video if an annotation is uploaded
        trainable_tasks = project.get_trainable_task_nodes()
        if len(trainable_tasks) == 1 and (
            trainable_tasks[0].task_properties.task_type.is_global
            or trainable_tasks[0].task_properties.task_type.is_anomaly
        ):
            video_ann_range_repo = VideoAnnotationRangeRepo(dataset_storage_identifier)
            video_ann_range = video_ann_range_repo.get_latest_by_video_id(video_id)
            if len(annotation_scene.annotations) > 0:
                label_ids = list(annotation_scene.annotations[0].get_label_ids(include_empty=True))
            else:
                label_ids = []
            video_ann_range.set_labels_at_frame_index(
                frame_index=frame_index,
                label_ids=label_ids,
            )
            video_ann_range_repo.save(video_ann_range)

        return AnnotationRESTViews.media_2d_annotation_to_rest(
            annotation_scene,
            annotation_scene_state=annotation_scene_state,
            tasks_to_revisit=tasks_to_revisit,
            is_rotated_detection=is_rotated_detection,
        )

    @staticmethod
    def _project_is_rotated_detection_task(project: Project) -> bool:
        """
        Checks if a project is a single task which is of type ROTATED_DETECTION.
        """
        trainable_tasks = project.get_trainable_task_nodes()
        return len(trainable_tasks) == 1 and trainable_tasks[0].task_properties.task_type == TaskType.ROTATED_DETECTION
