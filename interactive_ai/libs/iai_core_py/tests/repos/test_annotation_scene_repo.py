# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import copy
from collections.abc import Sequence
from datetime import datetime

import pytest

from iai_core_py.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind, NullAnnotationScene
from iai_core_py.entities.label import Label
from iai_core_py.entities.scored_label import LabelSource, ScoredLabel
from iai_core_py.entities.shapes import Keypoint, Point, Polygon
from iai_core_py.repos import AnnotationSceneRepo, ImageRepo, LabelSchemaRepo
from tests.test_helpers import generate_random_annotated_project, register_model_template

from geti_types import ID, ImageIdentifier, NullMediaIdentifier, VideoFrameIdentifier


@pytest.fixture
def fxt_annotation_with_model_id(fxt_rectangle_annotation, fxt_ote_id):
    """
    Creates an annotation with a scored label that has a label source with the given
    model ID.
    """

    def _build_annotation(label: Label, model_id: ID = fxt_ote_id(999)) -> Annotation:
        return Annotation(
            shape=fxt_rectangle_annotation.shape,
            labels=[
                ScoredLabel(
                    label_id=label.id_,
                    is_empty=label.is_empty,
                    label_source=LabelSource(model_id=model_id),
                )
            ],
            id_=AnnotationSceneRepo.generate_id(),
        )

    yield _build_annotation


class TestAnnotationSceneRepo:
    @staticmethod
    def __annotation_list_mapped_per_media_id(
        annotations: Sequence[AnnotationScene],
    ) -> dict[ID, list[AnnotationScene]]:
        """
        Turns a list of annotations into a dict with media_id : [annotations].

        :param annotations: List of AnnotationScene entities
        :return: Dict mapping media id to annotation list
        """
        predictions_per_media_id: dict[ID, list[AnnotationScene]] = {}
        for p in annotations:
            media_id = p.media_identifier.media_id
            if media_id in predictions_per_media_id:
                predictions_per_media_id[p.media_identifier.media_id].append(p)
            else:
                predictions_per_media_id[p.media_identifier.media_id] = [p]
        return predictions_per_media_id

    def test_get_latest_annotations_by_kind_and_identifiers(self, request) -> None:
        """
        <b>Description:</b>
        Check that annotations can be retrieved by most recent

        <b>Input data:</b>
        Project with 2 images
        Two predictions

        <b>Expected results:</b>
        Test passes if the most recent annotations can be retrieved correctly
        and a non existing ID return NullMediaIdentifier

        <b>Steps</b>
        1. Create Project and extra predictions
        2. Retrieve all annotations
        3. Retrieve most recent predictions
        4. Retrieve recent predictions together with non-existing prediction
        """
        register_model_template(request, type(None), "classification", "CLASSIFICATION", trainable=True)
        project = generate_random_annotated_project(
            test_case=request,
            name="__Test annotation repo",
            description="TestRepos()",
            model_template_id="classification",
            number_of_images=2,
            number_of_videos=0,
        )[0]
        dataset_storage = project.get_training_dataset_storage()
        ann_scene_repo = AnnotationSceneRepo(dataset_storage.identifier)

        images = list(ImageRepo(dataset_storage.identifier).get_all())
        assert len(images) == 2
        annotation_scenes = list(ann_scene_repo.get_all())
        assert len(annotation_scenes) == 2

        # Make "PREDICTION" for each of the two images. For the first image, make two predictions.
        # For the second image, just make 1 prediction
        predictions = []
        newest_prediction_first_image = None
        for i, annotation_scene in enumerate(annotation_scenes):
            prediction = AnnotationScene(
                kind=AnnotationSceneKind.PREDICTION,
                media_identifier=annotation_scene.media_identifier,
                media_height=annotation_scene.media_height,
                media_width=annotation_scene.media_width,
                id_=AnnotationSceneRepo.generate_id(),
                annotations=annotation_scene.annotations,
            )
            predictions.append(prediction)
            # Insert prediction for first image twice. Simulate 2 predictions
            if i == 0:
                newest_prediction_first_image = copy.deepcopy(prediction)
                newest_prediction_first_image.id_ = AnnotationSceneRepo.generate_id()
                predictions.append(newest_prediction_first_image)

        for p in predictions:
            ann_scene_repo.save(p)
        assert len(predictions) == 3

        # Get all annotation entities. Confirm there are 2 annotations, 2 + 1 predictions
        all_annotation_entities = list(ann_scene_repo.get_all())
        assert len(all_annotation_entities) == 5

        # Get most recent predictions for the two images in the dataset.
        # Must be the one most recent for the first image, one most recent for the second
        most_recent_predictions = ann_scene_repo.get_latest_annotations_by_kind_and_identifiers(
            media_identifiers=[i.media_identifier for i in images],
            annotation_kind=AnnotationSceneKind.PREDICTION,
        )
        assert newest_prediction_first_image in most_recent_predictions, (
            "Expected the newest prediction for image 0 in the set"
        )

        # This step could be simplified, but easy debugging > speed in a unit test
        predictions_per_media_id = self.__annotation_list_mapped_per_media_id(most_recent_predictions)

        assert len(predictions_per_media_id.keys()) == 2, (
            "Expected one prediction for image 0, and one prediction for image 1"
        )

        # Test by requesting the media identifiers twice, and with a non existing ID.
        # The function should return the same annotation again if the media identifier is given again
        # It should return NullAnnotationScene for the non-existing identifier

        id_dont_exist = ID("aaaaaaaaaaaaaaaaaaaaaaaa")
        most_recent_predictions_non_exist = ann_scene_repo.get_latest_annotations_by_kind_and_identifiers(
            media_identifiers=[i.media_identifier for i in images] * 2 + [ImageIdentifier(image_id=id_dont_exist)],
            annotation_kind=AnnotationSceneKind.PREDICTION,
        )

        assert len(most_recent_predictions_non_exist) == 5, (
            "Expected two predictions for image 0, "
            "and two prediction for image 1 and a NullAnnotation for a NullMediaIdentifier"
        )

    def test_save_no_media_identifier(self, fxt_dataset_storage) -> None:
        """
        <b>Description:</b>
        Tests that an AnnotationScene cannot be saved without a media identifier

        <b>Input data:</b>
        AnnotationScene with NullMediaIdentifier.

        <b>Expected results:</b>
        AnnotationSceneRepo raises ValueError on saving the AnnotationScene.

        <b>Steps</b>
        1. Generate AnnotationSceneRepo
        2. Generate AnnotationScene with NullMediaIdentifier
        3. Save AnnotationScene in AnnotationSceneRepo
        """
        annotation_repo = AnnotationSceneRepo(fxt_dataset_storage.identifier)
        annotation = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=NullMediaIdentifier(),
            media_height=640,
            media_width=480,
            id_=AnnotationSceneRepo.generate_id(),
        )

        with pytest.raises(ValueError) as exc:
            annotation_repo.save(annotation)

        assert str(exc.value) == "Cannot save annotation that does not belong to a Media."

    def test_get_frame_indices_by_video_id(
        self,
        request,
        fxt_video_entity,
        fxt_dataset_storage,
        fxt_rectangle_annotation,
        fxt_mongo_id,
    ):
        """
        Test repo to get annotated frame indices by video id. Also asserts that an unannotated
        frame is not returned.
        """
        # Indices at 0 and 30 are within frame stride, 45 is not to verify if non stride
        # based frames are returned.
        frame_indices = (0, 30, 45)

        ann_scene_repo = AnnotationSceneRepo(fxt_dataset_storage.identifier)
        request.addfinalizer(lambda: ann_scene_repo.delete_all())

        for frame_index in frame_indices:
            media_identifier = VideoFrameIdentifier(
                video_id=fxt_video_entity.id_,
                frame_index=frame_index,
            )

            annotation_scene = AnnotationScene(
                kind=AnnotationSceneKind.ANNOTATION,
                media_identifier=media_identifier,
                media_height=fxt_video_entity.height,
                media_width=fxt_video_entity.width,
                id_=AnnotationSceneRepo.generate_id(),
                last_annotator_id="Test",
                annotations=[fxt_rectangle_annotation],
            )
            ann_scene_repo.save(annotation_scene)

        # Unannotated frame
        media_identifier = VideoFrameIdentifier(
            video_id=fxt_video_entity.id_,
            frame_index=60,
        )

        annotation_scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=media_identifier,
            media_height=fxt_video_entity.height,
            media_width=fxt_video_entity.width,
            id_=AnnotationSceneRepo.generate_id(),
            last_annotator_id="Test",
        )
        ann_scene_repo.save(annotation_scene)

        annotated_frame_indices = ann_scene_repo.get_annotated_video_frame_identifiers_by_video_id(
            video_id=fxt_video_entity.id_
        )

        assert annotated_frame_indices == [
            VideoFrameIdentifier(video_id=fxt_video_entity.id_, frame_index=frame_index)
            for frame_index in frame_indices
        ]

    def test_get_frame_annotations_by_video_id(
        self,
        request,
        fxt_video_entity,
        fxt_dataset_storage,
        fxt_rectangle_annotation,
        fxt_mongo_id,
    ):
        """
        Test repo to get annotated frame indices by video id. Also asserts that an unannotated
        frame is not returned.
        """
        # Indices at 0, 30, 90 and 120 are within frame stride, 45 is not to verify if non stride
        # based frames are returned.
        frame_indices = (0, 30, 45, 90, 120, 150, 180)
        start_frame = 30
        end_frame = 150
        frame_skip = 30
        limit = 3

        ann_scene_repo = AnnotationSceneRepo(fxt_dataset_storage.identifier)
        request.addfinalizer(lambda: ann_scene_repo.delete_all())

        expected_annotations = []
        for frame_index in frame_indices:
            media_identifier = VideoFrameIdentifier(
                video_id=fxt_video_entity.id_,
                frame_index=frame_index,
            )

            annotation_scene = AnnotationScene(
                kind=AnnotationSceneKind.ANNOTATION,
                media_identifier=media_identifier,
                media_height=fxt_video_entity.height,
                media_width=fxt_video_entity.width,
                id_=AnnotationSceneRepo.generate_id(),
                last_annotator_id="Test",
                annotations=[fxt_rectangle_annotation],
            )
            ann_scene_repo.save(annotation_scene)
            if frame_index % frame_skip == 0 and start_frame <= frame_index <= end_frame:
                expected_annotations.append(ann_scene_repo.get_by_id(annotation_scene.id_))

        # Unannotated frame
        media_identifier = VideoFrameIdentifier(
            video_id=fxt_video_entity.id_,
            frame_index=60,
        )

        annotation_scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=media_identifier,
            media_height=fxt_video_entity.height,
            media_width=fxt_video_entity.width,
            id_=AnnotationSceneRepo.generate_id(),
            last_annotator_id="Test",
        )
        ann_scene_repo.save(annotation_scene)

        annotated_frame_annotations, count = ann_scene_repo.get_video_frame_annotations_by_video_id(
            video_id=fxt_video_entity.id_,
            start_frame=start_frame,
            end_frame=end_frame,
            frame_skip=frame_skip,
            limit=limit,
        )

        assert annotated_frame_annotations == expected_annotations[:limit]
        assert count == len(expected_annotations)

    def test_get_annotation_object_sizes(
        self,
        request,
        fxt_dataset_storage,
        fxt_rectangle_annotation,
        fxt_scored_label,
        fxt_label_2,
        fxt_label_3,
        fxt_ote_id,
    ) -> None:
        # Arrange
        label1 = fxt_scored_label
        label2 = ScoredLabel(
            label_id=fxt_label_2.id_,
            is_empty=fxt_label_2.is_empty,
            probability=0.7,
        )
        label3 = ScoredLabel(
            label_id=fxt_label_3.id_,
            probability=0.8,
        )
        ann_scene_repo = AnnotationSceneRepo(fxt_dataset_storage.identifier)
        media_identifier = ImageIdentifier(
            image_id=fxt_ote_id(0),
        )
        dummy_label_id = fxt_ote_id(3)
        dummy_width = 100
        dummy_height = 100
        polygon_shape = Polygon(points=[Point(0.1, 0.4), Point(0.01, 0.3), Point(0.2, 0.8)])
        visible_keypoint_shape = Keypoint(x=0.1, y=0.4, is_visible=True)
        invisible_keypoint_shape = Keypoint(x=0.2, y=0.5, is_visible=False)

        scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=media_identifier,
            media_height=dummy_height,
            media_width=dummy_width,
            id_=AnnotationSceneRepo.generate_id(),
            last_annotator_id="Test",
            annotations=[
                fxt_rectangle_annotation,
                Annotation(shape=polygon_shape, labels=[label1], id_=fxt_ote_id(1)),
                Annotation(shape=polygon_shape, labels=[label2], id_=fxt_ote_id(2)),
                Annotation(shape=visible_keypoint_shape, labels=[label3], id_=fxt_ote_id(4)),
                Annotation(shape=invisible_keypoint_shape, labels=[label3], id_=fxt_ote_id(5)),
            ],
        )
        ann_scene_repo.save(scene)

        # Act
        result, _, _ = ann_scene_repo.get_annotation_count_and_object_sizes(
            label_ids=[label1.id_, label2.id_, label3.id_, dummy_label_id],
            max_object_sizes_per_label=100,
        )

        # Assert
        rectangle_shape = fxt_rectangle_annotation.shape
        rectangle_object_size = (
            int((rectangle_shape.x2 - rectangle_shape.x1) * dummy_width),
            int((rectangle_shape.y2 - rectangle_shape.y1) * dummy_height),
        )
        polygon_object_size = (
            int((polygon_shape.max_x - polygon_shape.min_x) * dummy_width),
            int((polygon_shape.max_y - polygon_shape.min_y) * dummy_height),
        )
        assert result[label1.id_] == (rectangle_object_size, polygon_object_size)
        assert result[label2.id_] == (polygon_object_size,)
        assert result[label3.id_] == ((1, 1),)  # Keypoints are a single pixel
        assert dummy_label_id not in result

    def test_count_label_occurrence(
        self,
        request,
        fxt_dataset_storage,
        fxt_rectangle_annotation,
        fxt_anomalous_rectangle_annotation,
        fxt_annotation_scene_prediction,
        fxt_scored_label,
        fxt_ote_id,
    ) -> None:
        # Arrange
        label_id = fxt_scored_label.id_
        ann_scene_repo = AnnotationSceneRepo(fxt_dataset_storage.identifier)
        ann_scene_repo.delete_all()
        request.addfinalizer(lambda: ann_scene_repo.delete_all())
        media_identifier1 = ImageIdentifier(image_id=fxt_ote_id(0))
        media_identifier2 = ImageIdentifier(image_id=fxt_ote_id(1))
        dummy_width = 100
        dummy_height = 100

        visible_keypoint_shape = Keypoint(x=0.1, y=0.4, is_visible=True)
        invisible_keypoint_shape = Keypoint(x=0.2, y=0.5, is_visible=False)

        scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=media_identifier1,
            media_height=dummy_height,
            media_width=dummy_width,
            id_=AnnotationSceneRepo.generate_id(),
            last_annotator_id="Test",
            creation_date=datetime(2022, 1, 1),
            annotations=[
                fxt_rectangle_annotation,
                fxt_rectangle_annotation,
                fxt_anomalous_rectangle_annotation,
                Annotation(
                    shape=visible_keypoint_shape,
                    labels=[fxt_scored_label],
                    id_=fxt_ote_id(4),
                ),
                Annotation(
                    shape=invisible_keypoint_shape,
                    labels=[fxt_scored_label],
                    id_=fxt_ote_id(5),
                ),
            ],
        )
        ann_scene_repo.save(scene)

        # AnnotationSceneKind other than ANNOTATION should be excluded, even if latest
        fxt_annotation_scene_prediction.creation_date = datetime(2022, 1, 2)
        fxt_annotation_scene_prediction.media_identifier = media_identifier2
        ann_scene_repo.save(fxt_annotation_scene_prediction)

        # Act
        # Both the count_label_occurrence and counting in get_annotation_count_and_object_sizes are tested.
        (
            count_annotation_scene_level,
            count_shape_level,
        ) = ann_scene_repo.count_label_occurrence([label_id])

        (
            _,
            count_annotation_scene_level_facet,
            count_shape_level_facet,
        ) = ann_scene_repo.get_annotation_count_and_object_sizes([label_id], max_object_sizes_per_label=1)

        # Assert
        assert count_annotation_scene_level == {label_id: 1}
        assert count_shape_level == {label_id: 3}
        assert count_annotation_scene_level == count_annotation_scene_level_facet
        assert count_shape_level == count_shape_level_facet

    def test_get_latest_prediction_by_model_ids(self, request, fxt_ote_id, fxt_annotation_with_model_id) -> None:
        """
        <b>Description:</b>
        Check that the latest annotations can be retrieved by model IDs

        <b>Input data:</b>
        Project with 2 images
        Two predictions

        <b>Expected results:</b>
        Test passes if the most recent annotations can be retrieved correctly filtered
        by model_ids and a non-existing ID return NullAnnotationScene

        <b>Steps</b>
        1. Create Project and two extra predictions
        2. Retrieve most recent predictions by model ID
        """
        register_model_template(request, type(None), "classification", "CLASSIFICATION", trainable=True)
        project = generate_random_annotated_project(
            test_case=request,
            name="__Test annotation repo",
            description="TestRepos()",
            model_template_id="classification",
            number_of_images=2,
            number_of_videos=0,
        )[0]
        dataset_storage = project.get_training_dataset_storage()
        annotation_repo = AnnotationSceneRepo(dataset_storage.identifier)
        request.addfinalizer(lambda: annotation_repo.delete_all())

        images = list(ImageRepo(dataset_storage.identifier).get_all())
        assert len(images) == 2
        annotation_scenes = list(annotation_repo.get_all())
        assert len(annotation_scenes) == 2

        label_schema_repo = LabelSchemaRepo(project.identifier)
        sample_label = list(label_schema_repo.get_all())[0].get_labels(include_empty=True)[0]
        sample_annotation_scene = annotation_scenes[0]

        model_id_1 = fxt_ote_id(100)
        model_id_2 = fxt_ote_id(101)
        model_id_3 = fxt_ote_id(102)

        annotation_1 = fxt_annotation_with_model_id(label=sample_label, model_id=model_id_1)
        annotation_2 = fxt_annotation_with_model_id(label=sample_label, model_id=model_id_2)
        prediction_1 = AnnotationScene(
            kind=AnnotationSceneKind.PREDICTION,
            media_identifier=sample_annotation_scene.media_identifier,
            media_height=sample_annotation_scene.media_height,
            media_width=sample_annotation_scene.media_width,
            id_=AnnotationSceneRepo.generate_id(),
            annotations=[annotation_1, annotation_2],
        )
        prediction_2 = AnnotationScene(
            kind=AnnotationSceneKind.PREDICTION,
            media_identifier=sample_annotation_scene.media_identifier,
            media_height=sample_annotation_scene.media_height,
            media_width=sample_annotation_scene.media_width,
            id_=AnnotationSceneRepo.generate_id(),
            annotations=[annotation_2],
        )

        annotation_repo.save(prediction_1)
        annotation_repo.save(prediction_2)

        # Prediction 1 has both model_1 and model_2, while prediction 2 only has model_2
        latest_prediction_model_1 = annotation_repo.get_latest_annotation_by_kind_and_identifier(
            media_identifier=sample_annotation_scene.media_identifier,
            annotation_kind=AnnotationSceneKind.PREDICTION,
            model_ids={model_id_1},
        )
        assert model_id_1 in latest_prediction_model_1.get_model_ids(include_user_annotations=False)
        assert latest_prediction_model_1 == prediction_1

        latest_prediction_model_2 = annotation_repo.get_latest_annotation_by_kind_and_identifier(
            media_identifier=sample_annotation_scene.media_identifier,
            annotation_kind=AnnotationSceneKind.PREDICTION,
            model_ids={model_id_2},
        )
        assert model_id_2 in latest_prediction_model_2.get_model_ids(include_user_annotations=False)
        assert latest_prediction_model_2 == prediction_2

        # Test get prediction by media_id
        pred_by_media_id = annotation_repo.get_latest_annotations_by_kind_and_media_id(
            media_id=sample_annotation_scene.media_identifier.media_id,
            annotation_kind=AnnotationSceneKind.PREDICTION,
            model_ids={model_id_1},
        )
        assert pred_by_media_id[0] == latest_prediction_model_1

        # There are no annotations with model_3, hence NullAnnotationScene is returned
        latest_prediction_model_3 = annotation_repo.get_latest_annotation_by_kind_and_identifier(
            media_identifier=sample_annotation_scene.media_identifier,
            annotation_kind=AnnotationSceneKind.PREDICTION,
            model_ids={model_id_3},
        )
        assert isinstance(latest_prediction_model_3, NullAnnotationScene)

    def test_get_latest_prediction_by_model_ids_task_chain(
        self, request, fxt_ote_id, fxt_annotation_with_model_id
    ) -> None:
        """
        <b>Description:</b>
        Check that the latest annotations can be retrieved by model IDs for task chain.
        When one of the task chain's model has changed, only predictions containing the
        latest models should be returned.

        <b>Input data:</b>
        Project with 2 images
        Two predictions

        <b>Expected results:</b>
        Test passes only if the most recent annotations containing both task chain's
        model IDs are returned.

        <b>Steps</b>
        1. Create Project and two extra predictions
        2. Retrieve most recent predictions by the task chain's model IDs
        """
        register_model_template(request, type(None), "classification", "CLASSIFICATION", trainable=True)
        project = generate_random_annotated_project(
            test_case=request,
            name="__Test annotation repo",
            description="TestRepos()",
            model_template_id="classification",
            number_of_images=2,
            number_of_videos=0,
        )[0]
        dataset_storage = project.get_training_dataset_storage()
        annotation_repo = AnnotationSceneRepo(dataset_storage.identifier)
        request.addfinalizer(lambda: annotation_repo.delete_all())

        images = list(ImageRepo(dataset_storage.identifier).get_all())
        assert len(images) == 2
        annotation_scenes = list(annotation_repo.get_all())
        assert len(annotation_scenes) == 2

        label_schema_repo = LabelSchemaRepo(project.identifier)
        sample_label = list(label_schema_repo.get_all())[0].get_labels(include_empty=True)[0]
        sample_annotation_scene = annotation_scenes[0]

        model_id_detection_1 = fxt_ote_id(100)
        model_id_classification_1 = fxt_ote_id(101)
        model_id_detection_2 = fxt_ote_id(102)

        annotation_1 = fxt_annotation_with_model_id(label=sample_label, model_id=model_id_detection_1)
        annotation_2 = fxt_annotation_with_model_id(label=sample_label, model_id=model_id_classification_1)
        annotation_3 = fxt_annotation_with_model_id(label=sample_label, model_id=model_id_detection_2)
        prediction_a = AnnotationScene(
            kind=AnnotationSceneKind.PREDICTION,
            media_identifier=sample_annotation_scene.media_identifier,
            media_height=sample_annotation_scene.media_height,
            media_width=sample_annotation_scene.media_width,
            id_=AnnotationSceneRepo.generate_id(),
            annotations=[annotation_2, annotation_3],
        )
        prediction_b = AnnotationScene(
            kind=AnnotationSceneKind.PREDICTION,
            media_identifier=sample_annotation_scene.media_identifier,
            media_height=sample_annotation_scene.media_height,
            media_width=sample_annotation_scene.media_width,
            id_=AnnotationSceneRepo.generate_id(),
            annotations=[annotation_1, annotation_2],
        )

        annotation_repo.save(prediction_a)
        annotation_repo.save(prediction_b)

        # Prediction A is the one generated by the latest task chain models
        task_chain_latest_model_ids = {model_id_detection_2, model_id_classification_1}
        latest_prediction = annotation_repo.get_latest_annotation_by_kind_and_identifier(
            media_identifier=sample_annotation_scene.media_identifier,
            annotation_kind=AnnotationSceneKind.PREDICTION,
            model_ids=task_chain_latest_model_ids,
        )
        assert task_chain_latest_model_ids == latest_prediction.get_model_ids(include_user_annotations=False)
        assert latest_prediction == prediction_a

        # Test get prediction by media_id
        pred_by_media_id = annotation_repo.get_latest_annotations_by_kind_and_media_id(
            media_id=sample_annotation_scene.media_identifier.media_id,
            annotation_kind=AnnotationSceneKind.PREDICTION,
            model_ids={model_id_detection_2, model_id_classification_1},
        )
        assert len(pred_by_media_id) == 1
        assert pred_by_media_id[0] == latest_prediction

    @pytest.mark.skip(reason="Performance test, too slow for CI")
    def test_get_latest_prediction_by_model_ids_performance(
        self, request, fxt_ote_id, fxt_annotation_with_model_id
    ) -> None:
        """
        <b>Description:</b>
        Check that retrieving the latest annotations by model IDs is fast enough

        <b>Input data:</b>
        Project with 2 images
        N predictions with M models

        <b>Expected results:</b>
        Test passes if the predictions can be retrieved within the margin of tolerance
        compared to no filtering on a set of model IDs

        <b>Steps</b>
        1. Create Project and N extra predictions
        2. Measure performance for retrieving the latest prediction for a given model
        """

        register_model_template(request, type(None), "classification", "CLASSIFICATION", trainable=True)
        project = generate_random_annotated_project(
            test_case=request,
            name="__Test annotation repo",
            description="TestRepos()",
            model_template_id="classification",
            number_of_images=2,
            number_of_videos=0,
        )[0]
        dataset_storage = project.get_training_dataset_storage()
        annotation_repo = AnnotationSceneRepo(dataset_storage.identifier)
        request.addfinalizer(lambda: annotation_repo.delete_all())

    def test_count_all_by_media_id_and_annotation_kind(self, request, fxt_ote_id, fxt_annotation_with_model_id) -> None:
        """
        <b>Description:</b>
        Check that the count of annotations can be retrieved depending on the media ID

        <b>Input data:</b>
        Project with 2 images
        Two predictions

        <b>Expected results:</b>
        Test passes only if the correct number of annotations are retrieved

        <b>Steps</b>
        1. Create Project and two extra predictions
        2. Retrieve most recent predictions by the task chain's model IDs
        """
        register_model_template(request, type(None), "classification", "CLASSIFICATION", trainable=True)
        project = generate_random_annotated_project(
            test_case=request,
            name="__Test annotation repo",
            description="TestRepos()",
            model_template_id="classification",
            number_of_images=1,
            number_of_videos=0,
        )[0]
        dataset_storage = project.get_training_dataset_storage()
        annotation_repo = AnnotationSceneRepo(dataset_storage.identifier)
        request.addfinalizer(lambda: annotation_repo.delete_all())

        label_schema_repo = LabelSchemaRepo(project.identifier)
        sample_label = list(label_schema_repo.get_all())[0].get_labels(include_empty=True)[0]
        annotation_scenes = list(annotation_repo.get_all())
        sample_annotation_scene = annotation_scenes[0]

        annotation_1 = fxt_annotation_with_model_id(label=sample_label, model_id=fxt_ote_id(100))
        prediction_a = AnnotationScene(
            kind=AnnotationSceneKind.PREDICTION,
            media_identifier=sample_annotation_scene.media_identifier,
            media_height=sample_annotation_scene.media_height,
            media_width=sample_annotation_scene.media_width,
            id_=AnnotationSceneRepo.generate_id(),
            annotations=[annotation_1],
        )
        prediction_b = AnnotationScene(
            kind=AnnotationSceneKind.PREDICTION,
            media_identifier=sample_annotation_scene.media_identifier,
            media_height=sample_annotation_scene.media_height,
            media_width=sample_annotation_scene.media_width,
            id_=AnnotationSceneRepo.generate_id(),
            annotations=[annotation_1],
        )

        annotation_repo.save(prediction_a)
        annotation_repo.save(prediction_b)

        all_annotation_scenes = list(annotation_repo.get_all())
        user_annotation_scenes = annotation_repo.count_all_by_identifier_and_annotation_kind(
            media_identifier=sample_annotation_scene.media_identifier,
            annotation_kind=AnnotationSceneKind.ANNOTATION,
        )
        pred_annotation_scenes = annotation_repo.count_all_by_identifier_and_annotation_kind(
            media_identifier=sample_annotation_scene.media_identifier,
            annotation_kind=AnnotationSceneKind.PREDICTION,
        )
        assert user_annotation_scenes == 1
        assert pred_annotation_scenes == 2
        assert len(all_annotation_scenes) == user_annotation_scenes + pred_annotation_scenes
