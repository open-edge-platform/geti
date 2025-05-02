# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from copy import deepcopy
from typing import TYPE_CHECKING
from unittest.mock import ANY, call, patch

import pytest

from communication.exceptions import AnnotationSceneNotFoundException, AnnotationsNotFoundException
from managers.annotation_manager import AnnotationManager
from service.label_schema_service import LabelSchemaService

from geti_types import ID, ImageIdentifier, VideoFrameIdentifier
from iai_core_py.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind, NullAnnotationScene
from iai_core_py.entities.annotation_scene_state import AnnotationSceneState, AnnotationState
from iai_core_py.entities.scored_label import LabelSource, ScoredLabel
from iai_core_py.entities.shapes import Rectangle
from iai_core_py.entities.suspended_scenes import SuspendedAnnotationScenesDescriptor
from iai_core_py.repos import (
    AnnotationSceneRepo,
    AnnotationSceneStateRepo,
    LabelSchemaRepo,
    SuspendedAnnotationScenesRepo,
)
from iai_core_py.repos.dataset_storage_filter_repo import DatasetStorageFilterRepo
from iai_core_py.utils.annotation_scene_state_helper import AnnotationSceneStateHelper
from iai_core_py.utils.label_resolver import LabelResolver

if TYPE_CHECKING:
    from iai_core_py.entities.label import Label


@pytest.fixture
def fxt_annotation_scene_state_task_specific(fxt_annotation_scene, fxt_rectangle_annotation, fxt_detection_task):
    yield AnnotationSceneState(
        media_identifier=fxt_annotation_scene.media_identifier,
        annotation_scene_id=fxt_annotation_scene.id_,
        annotation_state_per_task={fxt_detection_task.id_: AnnotationState.ANNOTATED},
        unannotated_rois={},
        labels_to_revisit_full_scene=fxt_rectangle_annotation.get_label_ids(),
        labels_to_revisit_per_annotation={
            fxt_rectangle_annotation.id_: fxt_rectangle_annotation.get_label_ids(),
        },
        id_=AnnotationSceneStateRepo.generate_id(),
    )


@pytest.fixture
def fxt_ann_scene_states_list_task_specific(
    fxt_ann_scenes_list, fxt_detection_task, fxt_rectangle_annotation, fxt_mongo_id
):
    annotation_scene_states: list[AnnotationSceneState] = []
    for i, annotation_scene in enumerate(fxt_ann_scenes_list):
        annotation_scene.id_ = ID(fxt_mongo_id(i))
        state = AnnotationSceneState(
            media_identifier=annotation_scene.media_identifier,
            annotation_scene_id=annotation_scene.id_,
            annotation_state_per_task={fxt_detection_task.id_: AnnotationState.ANNOTATED},
            unannotated_rois={},
            labels_to_revisit_full_scene=fxt_rectangle_annotation.get_label_ids(),
            labels_to_revisit_per_annotation={
                fxt_rectangle_annotation.id_: fxt_rectangle_annotation.get_label_ids(),
            },
            id_=AnnotationSceneStateRepo.generate_id(),
        )
        annotation_scene_states.append(state)
    yield annotation_scene_states


class TestAnnotationManager:
    @pytest.mark.parametrize(
        "annotation_kind",
        [AnnotationSceneKind.ANNOTATION, AnnotationSceneKind.INTERMEDIATE],
    )
    def test_get_annotation_by_id(self, annotation_kind, fxt_dataset_storage, fxt_annotation_scene):
        # Arrange
        ANNOTATION_ID = ID("annotation_id_123")
        fxt_annotation_scene.kind = annotation_kind

        # Act
        with patch.object(
            AnnotationSceneRepo,
            "get_by_id",
            return_value=fxt_annotation_scene,
        ) as patched_get_by_id:
            result = AnnotationManager().get_annotation_scene_by_id(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                annotation_scene_id=ANNOTATION_ID,
                media_id=fxt_annotation_scene.media_identifier.media_id,
            )

        # Assert
        patched_get_by_id.assert_called_once_with(ANNOTATION_ID)
        assert result == fxt_annotation_scene

    def test_get_annotation_by_id_wrong_kind(self, fxt_dataset_storage, fxt_annotation_scene):
        # Arrange
        ANNOTATION_ID = ID("annotation_id_123")
        fxt_annotation_scene.kind = AnnotationSceneKind.PREDICTION

        # Act
        with (
            patch.object(
                AnnotationSceneRepo,
                "get_by_id",
                return_value=fxt_annotation_scene,
            ),
            pytest.raises(AnnotationSceneNotFoundException),
        ):
            AnnotationManager().get_annotation_scene_by_id(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                annotation_scene_id=ANNOTATION_ID,
                media_id=fxt_annotation_scene.media_identifier.media_id,
            )

    def test_get_annotation_by_id_error(self, fxt_dataset_storage):
        # Arrange
        ANNOTATION_ID = ID("annotation_id_123")

        # Act
        with (
            patch.object(
                AnnotationSceneRepo,
                "get_by_id",
                return_value=NullAnnotationScene(),
            ),
            pytest.raises(AnnotationSceneNotFoundException),
        ):
            AnnotationManager().get_annotation_scene_by_id(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                annotation_scene_id=ANNOTATION_ID,
                media_id=ID("super_cool_id"),
            )

    def test_latest_annotation_for_media(self, fxt_dataset_storage, fxt_annotation_scene):
        # Arrange
        IMAGE_ID = ID("image_id_123")
        MEDIA_IDENTIFIER = ImageIdentifier(image_id=IMAGE_ID)

        # Act
        with patch.object(
            AnnotationSceneRepo,
            "get_latest_annotation_by_kind_and_identifier",
            return_value=fxt_annotation_scene,
        ) as patched_get_latest_annotation:
            result = AnnotationManager().get_latest_annotation_scene_for_media(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                media_identifier=MEDIA_IDENTIFIER,
            )

        # Assert
        patched_get_latest_annotation.assert_called_once_with(MEDIA_IDENTIFIER, AnnotationSceneKind.ANNOTATION)
        assert result == fxt_annotation_scene

    def test_latest_annotation_for_media_error(self, fxt_dataset_storage):
        # Arrange
        IMAGE_ID = ID("image_id_123")
        MEDIA_IDENTIFIER = ImageIdentifier(image_id=IMAGE_ID)

        # Act
        with (
            patch.object(
                AnnotationSceneRepo,
                "get_latest_annotation_by_kind_and_identifier",
                return_value=NullAnnotationScene(),
            ),
            pytest.raises(AnnotationsNotFoundException),
        ):
            AnnotationManager().get_latest_annotation_scene_for_media(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                media_identifier=MEDIA_IDENTIFIER,
            )

    def test_save_annotations(
        self,
        fxt_project,
        fxt_label_schema,
        fxt_annotation_scene_1,
        fxt_annotation_scene_2,
        fxt_annotation_scene_state_1,
        fxt_annotation_scene_state_2,
    ) -> None:
        task_id = fxt_project.get_trainable_task_nodes()[0].id_
        with (
            patch.object(LabelResolver, "complete_labels"),
            patch.object(
                AnnotationSceneStateHelper,
                "compute_annotation_scene_state",
                side_effect=(
                    fxt_annotation_scene_state_1,
                    fxt_annotation_scene_state_2,
                ),
            ),
            patch.object(AnnotationManager, "_compute_tasks_to_revisit", return_value=[task_id]),
            patch.object(AnnotationSceneRepo, "save_many") as mock_ann_repo_save_many,
            patch.object(AnnotationSceneStateRepo, "save_many") as mock_ann_state_repo_save_many,
            patch.object(AnnotationManager, "publish_annotation_scene") as mock_publish,
        ):
            output = AnnotationManager.save_annotations(
                annotation_scenes=[fxt_annotation_scene_1, fxt_annotation_scene_2],
                project=fxt_project,
                dataset_storage_identifier=fxt_project.get_training_dataset_storage().identifier,
                label_schema=fxt_label_schema,
                chunk_size=1,
            )

        mock_ann_repo_save_many.assert_has_calls(
            [
                call([fxt_annotation_scene_1]),
                call([fxt_annotation_scene_2]),
            ]
        )
        mock_ann_state_repo_save_many.assert_has_calls(
            [
                call([fxt_annotation_scene_state_1]),
                call([fxt_annotation_scene_state_2]),
            ]
        )
        assert mock_publish.call_count == 2
        expected_output = (
            (fxt_annotation_scene_1, fxt_annotation_scene_state_1, [task_id]),
            (fxt_annotation_scene_2, fxt_annotation_scene_state_2, [task_id]),
        )
        assert output == expected_output

    def test_create_annotation_scenes_with_labels_for_images(
        self,
        fxt_project,
        fxt_dataset_storage,
        fxt_label,
        fxt_image_entity,
        fxt_annotation_scene_state,
        fxt_label_schema,
    ) -> None:
        shape = Rectangle.generate_full_box()
        shape.modification_date = ANY
        expected_annotations = [
            Annotation(
                shape=shape,
                labels=[
                    ScoredLabel(
                        label_id=fxt_label.id_,
                        is_empty=fxt_label.is_empty,
                        probability=1.0,
                        label_source=LabelSource(user_id=ID("dummy_user")),
                    )
                ],
                id_=ANY,
            )
        ]
        expected_annotation_scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=ImageIdentifier(image_id=fxt_image_entity.id_),
            media_height=fxt_image_entity.height,
            media_width=fxt_image_entity.width,
            id_=ANY,
            last_annotator_id=ID("dummy_user"),
            creation_date=ANY,
            annotations=expected_annotations,
        )
        with (
            patch.object(
                LabelSchemaRepo,
                "get_latest",
                return_value=fxt_label_schema,
            ),
            patch.object(
                AnnotationManager,
                "save_annotations",
                return_value=((0, fxt_annotation_scene_state, 0),),
            ) as patched_save_annotations,
        ):
            AnnotationManager.create_global_annotations_for_image(
                project=fxt_project,
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                labels=[fxt_label],
                user_id=ID("dummy_user"),
                image=fxt_image_entity,
            )
        patched_save_annotations.assert_called_once_with(
            annotation_scenes=[expected_annotation_scene],
            project=fxt_project,
            dataset_storage_identifier=fxt_dataset_storage.identifier,
            label_schema=fxt_label_schema,
            calculate_task_to_revisit=False,
        )

    def test_get_annotation_state_information_for_scene(
        self,
        fxt_annotation_scene,
        fxt_annotation_scene_state_task_specific,
        fxt_project,
        fxt_label,
    ):
        dataset_storage = fxt_project.get_training_dataset_storage()
        # Act
        with (
            patch.object(
                AnnotationSceneStateHelper,
                "get_annotation_state_for_scene",
                return_value=fxt_annotation_scene_state_task_specific,
            ) as mock_get_ann_state,
            patch.object(
                LabelSchemaService,
                "get_latest_labels_for_task",
                return_value=[fxt_label],
            ) as mock_get_latest_labels,
        ):
            (
                annotation_scene_state,
                tasks_to_revisit,
            ) = AnnotationManager().get_annotation_state_information_for_scene(
                dataset_storage_identifier=dataset_storage.identifier,
                annotation_scene=fxt_annotation_scene,
                project=fxt_project,
            )

        # Assert
        mock_get_ann_state.assert_called_once_with(
            annotation_scene=fxt_annotation_scene,
            dataset_storage_identifier=dataset_storage.identifier,
            project=fxt_project,
        )
        mock_get_latest_labels.assert_called()
        assert annotation_scene_state == fxt_annotation_scene_state_task_specific
        assert tasks_to_revisit == [fxt_project.get_trainable_task_nodes()[0].id_]

    def test_get_annotation_state_information_for_scenes(
        self,
        request,
        fxt_ann_scenes_list,
        fxt_ann_scene_states_list_task_specific,
        fxt_project,
        fxt_annotation_scene_1,
        fxt_annotation_scene_2,
        fxt_label,
    ):
        # Arrange
        task_id = fxt_project.get_trainable_task_nodes()[0].id_
        expected_tasks_to_revisit = [[task_id], [task_id]]

        # Act
        with (
            patch.object(
                AnnotationSceneStateHelper,
                "get_annotation_states_for_scenes",
                return_value={state.annotation_scene_id: state for state in fxt_ann_scene_states_list_task_specific},
            ) as mock_get_ann_state,
            patch.object(
                LabelSchemaService,
                "get_latest_labels_for_task",
                return_value=[fxt_label],
            ) as mock_get_latest_labels,
        ):
            (
                annotation_scene_states,
                tasks_to_revisit,
            ) = AnnotationManager().get_annotation_state_information_for_scenes(
                dataset_storage=fxt_project.get_training_dataset_storage(),
                annotation_scenes=fxt_ann_scenes_list,
                project=fxt_project,
            )

        # Assert
        mock_get_ann_state.assert_called_once_with(
            annotation_scenes=fxt_ann_scenes_list,
            dataset_storage=fxt_project.get_training_dataset_storage(),
            project=fxt_project,
        )
        mock_get_latest_labels.assert_called()
        assert annotation_scene_states == fxt_ann_scene_states_list_task_specific
        assert tasks_to_revisit == expected_tasks_to_revisit

    def test_suspend_annotations_by_labels(
        self,
        fxt_mongo_id,
        fxt_project,
        fxt_dataset_storage,
        fxt_detection_label_schema_factory,
        fxt_classification_label_schema_factory,
        fxt_rectangle_shape,
        fxt_media_identifier_1,
        fxt_media_identifier_2,
    ) -> None:
        """
        Test AnnotationManager.suspend_annotations_by_labels

        Scenario:
          - detection -> classification task chain
          - detection has 1 label
          - classification has 3 labels
          - two annotation scenes, one of which is the default one for unannotated media
          - the non-default annotation scene has two annotations:
            - the first with detection label and the first classification label
            - the second with detection label and the second classification label
          - the first classification label is already marked 'to revisit' for the
            first annotation
          - the input is a request to suspend the detection label on a full ROI level,
            the second classification label where present and the third one always.

        Expected result:
          - the second annotation scene is skipped because its media is unannotated
          - the first annotation is marked to revisit for the first and third label
            (first because already so, third because suspended unconditionally)
          - the second annotation is marked to revisit for the second and third label
            (second because present, third because suspended unconditionally)
          - the detection label is suspended at the scene level
        """
        # Arrange
        det_label_schema = fxt_detection_label_schema_factory(num_labels=1)
        cls_label_schema = fxt_classification_label_schema_factory(num_labels=3)
        det_label: Label = det_label_schema.get_labels(False)[0]
        cls_label_0: Label = cls_label_schema.get_labels(False)[0]
        cls_label_1: Label = cls_label_schema.get_labels(False)[1]
        cls_label_2: Label = cls_label_schema.get_labels(False)[2]
        det_label.id_ = fxt_mongo_id(10)
        cls_label_0.id_ = fxt_mongo_id(20)
        cls_label_1.id_ = fxt_mongo_id(21)
        cls_label_2.id_ = fxt_mongo_id(22)
        scored_det_label = ScoredLabel(label_id=det_label.id_, is_empty=det_label.is_empty, probability=0.6)
        scored_cls_label_0 = ScoredLabel(label_id=cls_label_0.id_, is_empty=cls_label_0.is_empty, probability=0.7)
        scored_cls_label_1 = ScoredLabel(label_id=cls_label_1.id_, is_empty=cls_label_1.is_empty, probability=0.8)
        ann_1 = Annotation(
            shape=fxt_rectangle_shape,
            labels=[scored_det_label, scored_cls_label_0],
            id_=fxt_mongo_id(1),
        )
        ann_2 = Annotation(
            shape=fxt_rectangle_shape,
            labels=[scored_det_label, scored_cls_label_1],
            id_=fxt_mongo_id(2),
        )
        ann_scene_1 = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=fxt_media_identifier_1,
            media_height=400,
            media_width=800,
            id_=fxt_mongo_id(3),
            annotations=[ann_1, ann_2],
        )
        ann_scene_state_1 = AnnotationSceneState(
            media_identifier=fxt_media_identifier_1,
            annotation_scene_id=ann_scene_1.id_,
            annotation_state_per_task={},
            unannotated_rois={},
            labels_to_revisit_per_annotation={ann_1.id_: [cls_label_0.id_]},
            labels_to_revisit_full_scene=[],
            id_=AnnotationSceneStateRepo.generate_id(),
        )
        assert ann_scene_state_1.get_state_media_level() == AnnotationState.TO_REVISIT
        ann_scene_2 = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=fxt_media_identifier_2,
            media_height=400,
            media_width=800,
            id_=fxt_mongo_id(4),
            annotations=[],
        )
        ann_scene_state_2 = AnnotationSceneState(
            media_identifier=fxt_media_identifier_2,
            annotation_scene_id=ann_scene_2.id_,
            annotation_state_per_task={},
            unannotated_rois={},
            labels_to_revisit_per_annotation={},
            labels_to_revisit_full_scene=[],
            id_=AnnotationSceneStateRepo.generate_id(),
        )
        assert ann_scene_state_2.get_state_media_level() == AnnotationState.NONE

        with (
            patch.object(
                fxt_project.training_dataset_storage_adapter,
                "get",
                return_value=fxt_dataset_storage,
            ),
            patch.object(AnnotationSceneRepo, "__init__", return_value=None),
            patch.object(
                AnnotationSceneRepo,
                "get_all_by_kind",
                return_value=[ann_scene_1, ann_scene_2],
            ),
            patch.object(AnnotationSceneStateRepo, "save", return_value=None),
            patch.object(
                AnnotationSceneStateRepo,
                "get_latest_for_annotation_scene",
                side_effect=[ann_scene_state_1, ann_scene_state_2],
            ),
            patch.object(
                AnnotationSceneStateHelper,
                "compute_annotation_scene_state",
                return_value=None,
            ) as mock_compute_ann_scene_state,
            patch.object(
                DatasetStorageFilterRepo,
                "update_annotation_scenes_to_revisit",
                return_value=None,
            ) as mock_update_dataset_storage_filter_data,
        ):
            # Act
            scene_to_revisit_ids_by_storage = AnnotationManager.suspend_annotations_by_labels(
                project=fxt_project,
                global_labels_to_revisit_if_present=[cls_label_1],
                global_labels_to_revisit_unconditionally=[cls_label_2],
                local_labels_to_revisit=[det_label],
            )

        # Assert
        assert set(scene_to_revisit_ids_by_storage.keys()) == {fxt_dataset_storage.id_}
        scenes_to_revisit_ids = scene_to_revisit_ids_by_storage[fxt_dataset_storage.id_]
        assert scenes_to_revisit_ids == (fxt_mongo_id(3),)
        expected_labels_to_revisit_per_annotation = {
            ann_1.id_: {cls_label_0.id_, cls_label_2.id_},
            ann_2.id_: {cls_label_1.id_, cls_label_2.id_},
        }
        expected_labels_to_revisit_full_scene = {det_label.id_}
        mock_compute_ann_scene_state.assert_called_once_with(
            annotation_scene=ann_scene_1,
            project=fxt_project,
            labels_to_revisit_per_annotation=expected_labels_to_revisit_per_annotation,
            labels_to_revisit_full_scene=expected_labels_to_revisit_full_scene,
        )
        mock_update_dataset_storage_filter_data.assert_called_once_with(annotation_scene_ids=scenes_to_revisit_ids)

    def test_notify_about_annotation_scenes_to_revisit(
        self,
        fxt_mongo_id,
        fxt_project,
    ):
        def mock_save(self, instance: SuspendedAnnotationScenesDescriptor):
            instance.id_ = fxt_mongo_id(100)

        # Arrange
        dataset_storage_id = fxt_project.training_dataset_storage_id
        with (
            patch.object(SuspendedAnnotationScenesRepo, "__init__", return_value=None),
            patch.object(SuspendedAnnotationScenesRepo, "save", new=mock_save),
            patch(
                "managers.annotation_manager.publish_event",
                return_value=None,
            ) as mock_publish_event,
        ):
            ids_to_revisit = (fxt_mongo_id(1), fxt_mongo_id(2))

            # Act
            AnnotationManager.publish_annotation_scenes_to_revisit(
                project_id=fxt_project.id_,
                scenes_to_revisit_ids_by_storage={dataset_storage_id: ids_to_revisit},
            )

        # Assert
        mock_publish_event.assert_called_once_with(
            topic="annotation_scenes_to_revisit",
            body={
                "workspace_id": fxt_project.workspace_id,
                "project_id": fxt_project.id_,
                "dataset_storage_id": dataset_storage_id,
                "suspended_scenes_descriptor_id": str(fxt_mongo_id(100)),
            },
            key=str(fxt_mongo_id(100)).encode(),
            headers_getter=ANY,
        )

    def test_get_filtered_frame_annotation_scenes(
        self,
        fxt_dataset_storage,
        fxt_video_identifier,
        fxt_annotation_scene,
    ) -> None:
        video_id = fxt_video_identifier.media_id
        dummy_frame_annotations = []
        for i in (0, 1, 2, 3, 4, 5):
            annotation_scene = deepcopy(fxt_annotation_scene)
            annotation_scene.media_identifier = VideoFrameIdentifier(video_id=video_id, frame_index=i)
            dummy_frame_annotations.append(annotation_scene)
        dummy_frames_filtered = [
            annotation_scene
            for annotation_scene in dummy_frame_annotations
            if annotation_scene.media_identifier.frame_index in (2, 4)
        ]
        start_frame = 1
        end_frame = 4
        frameskip = 2
        with patch.object(
            AnnotationSceneRepo,
            "get_video_frame_annotations_by_video_id",
            side_effect=[(dummy_frame_annotations, -1), (dummy_frames_filtered, -1)],
        ) as mock_repo_frame_annotations:
            result_unfiltered, count = AnnotationManager.get_filtered_frame_annotation_scenes(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                video_id=video_id,
                frameskip=1,
            )
            result_filtered, count = AnnotationManager.get_filtered_frame_annotation_scenes(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                video_id=video_id,
                start_frame=start_frame,
                end_frame=end_frame,
                frameskip=frameskip,
            )

        assert result_unfiltered == dummy_frame_annotations
        assert result_filtered == dummy_frames_filtered
        assert count == -1
        mock_repo_frame_annotations.assert_has_calls(
            calls=[
                call(
                    video_id=video_id,
                    annotation_kind=AnnotationSceneKind.ANNOTATION,
                    task_id=None,
                    model_ids=None,
                    start_frame=None,
                    end_frame=None,
                    frame_skip=1,
                    limit=None,
                ),
                call(
                    video_id=video_id,
                    annotation_kind=AnnotationSceneKind.ANNOTATION,
                    task_id=None,
                    model_ids=None,
                    start_frame=start_frame,
                    end_frame=end_frame,
                    frame_skip=frameskip,
                    limit=None,
                ),
            ]
        )
