# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import call, patch

import pytest

from communication.exceptions import NoPredictionsFoundException, PredictionNotFoundException
from entities import PredictionType
from service.prediction_service import PredictionService

from geti_types import ID, ImageIdentifier
from sc_sdk.entities.annotation import AnnotationSceneKind, NullAnnotationScene
from sc_sdk.repos import AnnotationSceneRepo


@pytest.fixture
def patched_repo():
    with patch.object(AnnotationSceneRepo, "__init__", return_value=None):
        yield

    AnnotationSceneRepo._instances = {}


class TestPredictionService:
    def test_get_prediction_by_id(
        self,
        patched_repo,
        fxt_annotation_scene,
        fxt_dataset_storage,
        fxt_media_identifier,
        fxt_mongo_id,
    ) -> None:
        """
        <b>Description:</b>
        Test successful pulling prediction by id.

        <b>Input data:</b>
        Random prediction ID, dataset_storage and media_identifier

        <b>Expected results:</b>
        Annotation scene is returned.

        <b>Steps</b>
        1. Mock AnnotationSceneRepo to return proper annotation scene.
        2. Call get_prediction_by_id
        3. Check if annotation_scene is returned.
        """
        prediction_id = fxt_mongo_id(0)
        fxt_annotation_scene.media_identifier = fxt_media_identifier
        fxt_annotation_scene.kind = AnnotationSceneKind.PREDICTION

        with patch.object(AnnotationSceneRepo, "get_by_id", return_value=fxt_annotation_scene) as patched_get_by_id:
            result = PredictionService.get_prediction_by_id(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                prediction_id=prediction_id,
                media_identifier=fxt_media_identifier,
            )

        patched_get_by_id.assert_called_once_with(prediction_id)
        assert result == fxt_annotation_scene

    def test_get_prediction_by_id_error(
        self,
        patched_repo,
        fxt_annotation_scene,
        fxt_dataset_storage,
        fxt_media_identifier,
        fxt_mongo_id,
    ) -> None:
        """
        <b>Description:</b>
        Test unsuccessful pulling prediction by id.

        <b>Input data:</b>
        Random prediction ID, dataset_storage and media_identifier

        <b>Expected results:</b>
        Annotation scene is returned.

        <b>Steps</b>
        1. Mock AnnotationSceneRepo to return wrong annotation scene.
        2. Call get_prediction_by_id
        3. Check if error with correct message is returned.
        """
        prediction_id = fxt_mongo_id(0)

        with (
            patch.object(AnnotationSceneRepo, "get_by_id", return_value=NullAnnotationScene()),
            pytest.raises(PredictionNotFoundException) as error,
        ):
            PredictionService.get_prediction_by_id(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                prediction_id=prediction_id,
                media_identifier=fxt_media_identifier,
            )
        assert error.value.message == (
            f"The requested prediction could not be found. Prediction ID: `{prediction_id}`."
        )

        fxt_annotation_scene.media_identifier = ImageIdentifier(image_id=ID("not_what_your_looking_for"))
        with (
            patch.object(AnnotationSceneRepo, "get_by_id", return_value=fxt_annotation_scene),
            pytest.raises(PredictionNotFoundException) as error,
        ):
            PredictionService.get_prediction_by_id(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                prediction_id=prediction_id,
                media_identifier=fxt_media_identifier,
            )
        assert error.value.message == (
            f"The requested prediction does not belong to this media. "
            f"Prediction ID: `{prediction_id}`, Media Identifier: `{fxt_media_identifier}`."
        )

        fxt_annotation_scene.media_identifier = fxt_media_identifier
        with (
            patch.object(AnnotationSceneRepo, "get_by_id", return_value=fxt_annotation_scene),
            pytest.raises(PredictionNotFoundException) as error,
        ):
            PredictionService.get_prediction_by_id(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                prediction_id=prediction_id,
                media_identifier=fxt_media_identifier,
            )
        assert error.value.message == (
            f"The requested prediction is not a PREDICTION, "
            f"instead it is a {fxt_annotation_scene.kind}. "
            f"Prediction ID: `{prediction_id}`"
        )

    def test_get_prediction_by_prediction_type(
        self,
        fxt_project,
        fxt_annotation_scene,
        fxt_dataset_storage,
        fxt_media_identifier,
        fxt_mongo_id,
    ) -> None:
        """
        <b>Description:</b>
        Test successful pulling prediction by prediction type.

        <b>Input data:</b>
        Prediction type, dataset_storage and media_identifier

        <b>Expected results:</b>
        Annotation scene is returned.

        <b>Steps</b>
        1. Mock AnnotationSceneRepo to return proper annotation scene.
        2. Call get_prediction_by_id
        3. Check if annotation_scene is returned.
        """
        prediction_type = PredictionType.LATEST
        task_id = fxt_mongo_id(1)
        model_ids = {fxt_mongo_id(3)}

        with patch.object(
            PredictionService, "_get_single_prediction", return_value=fxt_annotation_scene
        ) as patched_get_single_prediction:
            result = PredictionService.get_prediction_by_type(
                project=fxt_project,
                dataset_storage=fxt_dataset_storage,
                media_identifier=fxt_media_identifier,
                prediction_type=prediction_type,
                task_id=task_id,
                model_ids=model_ids,
            )

        patched_get_single_prediction.assert_called_once_with(
            project=fxt_project,
            dataset_storage=fxt_dataset_storage,
            media_identifier=fxt_media_identifier,
            prediction_type=prediction_type,
            task_id=task_id,
            model_ids=model_ids,
        )
        assert result == fxt_annotation_scene

    def test_get_prediction_by_prediction_type_error(
        self,
        fxt_project,
        fxt_dataset_storage,
        fxt_media_identifier,
        fxt_mongo_id,
    ) -> None:
        """
        <b>Description:</b>
        Test successful pulling prediction by prediction type.

        <b>Input data:</b>
        Prediction type, dataset_storage and media_identifier

        <b>Expected results:</b>
        Error is raised

        <b>Steps</b>
        1. Mock AnnotationSceneRepo to return NullAnnotationScene()
        2. Call get_prediction_by_prediction_type
        3. Check if error is raised.
        """
        prediction_type = PredictionType.LATEST
        task_id = fxt_mongo_id(1)

        with (
            patch.object(PredictionService, "_get_single_prediction", return_value=NullAnnotationScene()),
            pytest.raises(NoPredictionsFoundException) as error,
        ):
            PredictionService.get_prediction_by_type(
                project=fxt_project,
                dataset_storage=fxt_dataset_storage,
                media_identifier=fxt_media_identifier,
                prediction_type=prediction_type,
                task_id=task_id,
            )

        assert error.value.message == (
            f"There are no predictions that belong to the requested media. Media ID: `{fxt_media_identifier.media_id}`."
        )

    def test_get_single_prediction_latest(
        self,
        fxt_project,
        fxt_dataset_storage,
        fxt_media_identifier,
        fxt_annotation_scene_prediction,
        fxt_mongo_id,
    ) -> None:
        # Arrange
        model_ids = {fxt_mongo_id(1)}

        # Act
        with (
            patch.object(
                AnnotationSceneRepo,
                "get_latest_annotation_by_kind_and_identifier",
                return_value=fxt_annotation_scene_prediction,
            ) as mock_get_annotations,
        ):
            result = PredictionService._get_single_prediction(
                project=fxt_project,
                dataset_storage=fxt_dataset_storage,
                media_identifier=fxt_media_identifier,
                prediction_type=PredictionType.LATEST,
                model_ids={fxt_mongo_id(1)},
            )

        # Assert
        mock_get_annotations.assert_called_once_with(
            media_identifier=fxt_media_identifier,
            annotation_kind=AnnotationSceneKind.PREDICTION,
            task_id=None,
            model_ids=model_ids,
        )
        assert result == fxt_annotation_scene_prediction

    def test_get_single_prediction_task_prediction(
        self,
        fxt_chain_project,
        fxt_dataset_storage,
        fxt_media_identifier,
        fxt_annotation_scene_prediction,
        fxt_mongo_id,
    ) -> None:
        # Arrange
        model_ids = {fxt_mongo_id(1)}

        # Act
        with (
            patch.object(
                AnnotationSceneRepo,
                "get_latest_annotation_by_kind_and_identifier",
                return_value=fxt_annotation_scene_prediction,
            ) as mock_get_annotations,
        ):
            result = PredictionService._get_single_prediction(
                project=fxt_chain_project,
                dataset_storage=fxt_dataset_storage,
                media_identifier=fxt_media_identifier,
                prediction_type=PredictionType.LATEST,
                model_ids=model_ids,
            )

        # Assert
        mock_get_annotations.assert_called_once_with(
            media_identifier=fxt_media_identifier,
            annotation_kind=AnnotationSceneKind.TASK_PREDICTION,
            task_id=None,
            model_ids=model_ids,
        )
        assert result == fxt_annotation_scene_prediction

    def test_get_single_prediction_auto(
        self,
        fxt_project,
        fxt_dataset_storage,
        fxt_media_identifier,
        fxt_annotation_scene_prediction,
        fxt_mongo_id,
    ) -> None:
        # Arrange
        model_ids = {fxt_mongo_id(1)}

        # Act
        with (
            patch.object(
                AnnotationSceneRepo,
                "get_latest_annotation_by_kind_and_identifier",
                side_effect=[fxt_annotation_scene_prediction],
            ) as mock_get_annotations,
        ):
            result = PredictionService._get_single_prediction(
                project=fxt_project,
                dataset_storage=fxt_dataset_storage,
                media_identifier=fxt_media_identifier,
                prediction_type=PredictionType.AUTO,
                model_ids={fxt_mongo_id(1)},
            )

        # Assert
        mock_get_annotations.assert_has_calls(
            calls=[
                call(
                    media_identifier=fxt_media_identifier,
                    annotation_kind=AnnotationSceneKind.PREDICTION,
                    task_id=None,
                    model_ids=model_ids,
                )
            ]
        )
        assert result == fxt_annotation_scene_prediction
