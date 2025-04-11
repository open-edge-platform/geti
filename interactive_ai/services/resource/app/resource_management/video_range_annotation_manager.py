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

from managers.annotation_manager import AnnotationManager
from service.label_schema_service import LabelSchemaService

from geti_telemetry_tools import unified_tracing
from geti_types import ID, DatasetStorageIdentifier
from sc_sdk.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from sc_sdk.entities.annotation_scene_state import AnnotationSceneState, AnnotationState, NullAnnotationSceneState
from sc_sdk.entities.label import Label
from sc_sdk.entities.project import Project
from sc_sdk.entities.scored_label import LabelSource, ScoredLabel
from sc_sdk.entities.shapes import Rectangle
from sc_sdk.entities.video import Video
from sc_sdk.entities.video_annotation_range import RangeLabels, VideoAnnotationRange
from sc_sdk.repos import AnnotationSceneRepo, VideoAnnotationRangeRepo
from sc_sdk.utils.identifier_factory import IdentifierFactory

logger = logging.getLogger(__name__)


class VideoRangeAnnotationManager:
    @staticmethod
    @unified_tracing
    def create_global_annotations_for_video(
        project: Project,
        dataset_storage_identifier: DatasetStorageIdentifier,
        video: Video,
        labels: list[Label],
        user_id: ID,
    ) -> dict[ID, AnnotationState]:
        """
        Create annotations for all video frames when a video is uploaded with labels.

        :param project: Project to which the video belongs
        :param dataset_storage_identifier: identifier of the dataset storage
        :param video: Video that is uploaded with labels
        :param labels: Labels that will be used to annotate all frames
        :param user_id: ID of the user who created or updated the annotation
        return: For each trainable task in the project, annotation state of the uploaded video for that task
        """
        frame_identifiers = IdentifierFactory.generate_frame_identifiers_for_video(video)
        scored_labels = [
            ScoredLabel(
                label_id=label.id_, is_empty=label.is_empty, probability=1.0, label_source=LabelSource(user_id=user_id)
            )
            for label in labels
        ]
        annotations = [Annotation(shape=Rectangle.generate_full_box(), labels=scored_labels)]

        label_schema = LabelSchemaService.get_latest_label_schema_for_project(project.identifier)

        label_schema_by_task = {
            task_node.id_: LabelSchemaService.get_latest_label_schema_for_task(
                project_identifier=project.identifier, task_node_id=task_node.id_
            )
            for task_node in project.get_trainable_task_nodes()
        }

        video_annotation_range = VideoAnnotationRange(
            video_id=video.id_,
            range_labels=[
                RangeLabels(
                    start_frame=0,
                    end_frame=video.total_frames,
                    label_ids=[label.id_ for label in labels],
                )
            ],
            id_=VideoAnnotationRangeRepo.generate_id(),
        )
        video_ann_range_repo = VideoAnnotationRangeRepo(dataset_storage_identifier)
        video_ann_range_repo.save(video_annotation_range)

        annotation_scene_state: AnnotationSceneState = NullAnnotationSceneState()
        if len(labels) > 0:
            ann_scenes_to_save: list[AnnotationScene] = [
                AnnotationScene(
                    kind=AnnotationSceneKind.ANNOTATION,
                    media_identifier=identifier,
                    media_height=video.height,
                    media_width=video.width,
                    id_=AnnotationSceneRepo.generate_id(),
                    annotations=annotations,
                )
                for identifier in frame_identifiers
            ]
            # We can take the first created state to compute the state per task, as all states should be the same.
            _, annotation_scene_state, _ = AnnotationManager.save_annotations(
                annotation_scenes=ann_scenes_to_save,
                project=project,
                dataset_storage_identifier=dataset_storage_identifier,
                label_schema=label_schema,
                label_schema_by_task=label_schema_by_task,
                calculate_task_to_revisit=False,
            )[0]
        return annotation_scene_state.state_per_task
