# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import numpy as np
import pydantic_core
import pytest
import time_machine
from sqlalchemy.exc import SQLAlchemyError

from app.models import (
    ConfidenceThresholdDataCollectionPolicy,
    DataCollectionConfig,
    DatasetItemAnnotation,
    FixedRateDataCollectionPolicy,
    Label,
    LabelReference,
    Rectangle,
    Task,
    TaskType,
)
from app.models.media import ImageFormat
from app.services import DatasetService, MediaService
from app.services.data_collect.data_collector import (
    ConfidenceThresholdPolicyChecker,
    DataCollector,
    FixedRatePolicyChecker,
)
from app.services.media_service import ImageMetadata


class TestFixedRatePolicyCheckerUnit:
    """Unit tests for FixedRatePolicyChecker."""

    def test_zero_rate_raises_error_in_policy(self):
        # Arrange, Act and Assert
        with pytest.raises(pydantic_core.ValidationError):
            FixedRateDataCollectionPolicy(rate=0)  # type: ignore[bad_argument_type]

    def test_zero_rate_raises_error_in_checker(self):
        # Arrange
        policy = FixedRateDataCollectionPolicy(rate=0.1)
        policy.rate = 0

        # Act and Assert
        with pytest.raises(ValueError):
            FixedRatePolicyChecker(policy)

    def test_should_collect_true(self):
        # Arrange
        policy = FixedRateDataCollectionPolicy(rate=0.1)

        # Act
        should_collect = FixedRatePolicyChecker(policy).should_collect(100, [50.0])

        # Assert
        assert should_collect is True

    def test_should_collect_false(self):
        # Arrange
        policy = FixedRateDataCollectionPolicy(rate=0.1)

        # Act
        should_collect = FixedRatePolicyChecker(policy).should_collect(9, [50.0])

        # Assert
        assert should_collect is False


class TestConfidenceThresholdDataCollectionPolicyUnit:
    """Unit tests for ConfidenceThresholdDataCollectionPolicy."""

    def test_should_collect_true(self):
        # Arrange
        policy = ConfidenceThresholdDataCollectionPolicy(confidence_threshold=30.0, min_sampling_interval=5)

        # Act
        should_collect = ConfidenceThresholdPolicyChecker(policy).should_collect(6, [25.0])

        # Assert
        assert should_collect is True

    def test_should_collect_high_confidence(self):
        # Arrange
        policy = ConfidenceThresholdDataCollectionPolicy(confidence_threshold=30.0, min_sampling_interval=5)

        # Act
        should_collect = ConfidenceThresholdPolicyChecker(policy).should_collect(6, [35.0])

        # Assert
        assert should_collect is False

    def test_should_collect_sampling_interval(self):
        # Arrange
        policy = ConfidenceThresholdDataCollectionPolicy(confidence_threshold=30.0, min_sampling_interval=5)

        # Act
        should_collect = ConfidenceThresholdPolicyChecker(policy).should_collect(3, [25.0])

        # Assert
        assert should_collect is False


@pytest.fixture
def fxt_data_collector(fxt_event_bus) -> DataCollector:
    """Fixture to create a DataCollector instance with mocked dependencies."""
    with patch("app.services.data_collect.data_collector.DataCollector._load_pipeline"):
        return DataCollector(Path("data"), fxt_event_bus)


class TestDataCollectorUnit:
    """Unit tests for DataCollector."""

    def test_save_predictions_disabled_by_default(self):
        assert DataCollectionConfig.model_validate({}).save_predictions is False

    def test_collect_no(self, fxt_data_collector):
        """
        No images should be collected if policy conditions aren't met
        """
        # Arrange
        frame_data = np.random.rand(100, 100, 3)
        inference_data = MagicMock()

        now = datetime.timestamp(datetime.now())

        policy_checker = MagicMock()
        policy_checker.should_collect.return_value = False
        fxt_data_collector.policy_checkers = [policy_checker]

        # Act
        with (
            patch.object(DatasetService, "create_dataset_item") as mock_create_dataset_item,
        ):
            fxt_data_collector.collect(
                timestamp=now + 1,
                frame_data=frame_data,
                inference_data=inference_data,
            )

        # Assert
        mock_create_dataset_item.assert_not_called()

    @time_machine.travel("2025-01-01 00:00:01 +0000", tick=False)
    def test_collect_by_flag(self, fxt_data_collector):
        """
        Image should be collected if should_collect_next_frame flag has been set
        """
        # Arrange
        pipeline = MagicMock()
        pipeline.data_collection = DataCollectionConfig()
        project = MagicMock()
        frame_data = np.random.randint(low=0, high=255, size=(100, 100), dtype=np.uint8)
        inference_data = MagicMock()

        media = MagicMock()

        now = datetime.timestamp(datetime.now())

        policy_checker = MagicMock()
        policy_checker.should_collect.return_value = False
        fxt_data_collector.active_pipeline_data = pipeline, project
        fxt_data_collector.policy_checkers = [policy_checker]
        fxt_data_collector.should_collect_next_frame = True

        # Act
        with (
            patch.object(MediaService, "create_image") as mock_create_image,
            patch.object(DatasetService, "create_dataset_item") as mock_create_dataset_item,
        ):
            mock_create_image.return_value = media
            fxt_data_collector.collect(
                timestamp=now,
                frame_data=frame_data,
                inference_data=inference_data,
            )

        # Assert
        mock_create_image.assert_called_once()
        metadata: ImageMetadata = mock_create_image.call_args.args[0]
        assert metadata.project_id == project.id
        assert metadata.name == "1735689601_0000"
        assert metadata.image_format == ImageFormat.JPG
        assert metadata.source_id == pipeline.source_id
        assert metadata.data is not None
        mock_create_dataset_item.assert_called_once_with(
            project_id=project.id,
            task=project.task,
            media=media,
            user_reviewed=False,
            prediction_model_id=None,
            annotations=None,
        )

    @pytest.mark.parametrize("save_predictions", [False, True])
    @pytest.mark.parametrize("manual_capture", [False, True])
    @pytest.mark.parametrize("has_predictions", [False, True])
    @time_machine.travel("2025-01-01 00:00:01 +0000", tick=False)
    def test_collect(self, fxt_data_collector, save_predictions, manual_capture, has_predictions):
        """
        Image should be collected if policy conditions are met
        """
        # Arrange
        pipeline = MagicMock()
        pipeline.data_collection = DataCollectionConfig(save_predictions=save_predictions)
        project = MagicMock(id=uuid4(), task=Task(task_type=TaskType.DETECTION))
        frame_data = np.random.randint(low=0, high=255, size=(100, 100), dtype=np.uint8)
        inference_data = MagicMock()
        labels = [Label(id=uuid4(), project_id=project.id, name="cat", color="#ff0000", hotkey="")]
        trained_label_ids = {"gone": uuid4(), "old name": labels[0].id}
        annotations = (
            [
                DatasetItemAnnotation(
                    shape=Rectangle(x=10, y=10, width=20, height=20),
                    labels=[LabelReference(id=labels[0].id)],
                    confidences=[0.9],
                )
            ]
            if has_predictions
            else []
        )

        media = MagicMock()

        now = datetime.timestamp(datetime.now())

        policy_checker = MagicMock()
        policy_checker.should_collect.return_value = not manual_capture
        fxt_data_collector.active_pipeline_data = pipeline, project
        fxt_data_collector.policy_checkers = [policy_checker]
        fxt_data_collector.should_collect_next_frame = manual_capture

        # Act
        with (
            patch.object(MediaService, "create_image") as mock_create_image,
            patch.object(DatasetService, "create_dataset_item") as mock_create_dataset_item,
            patch("app.services.LabelService.list_all", return_value=labels) as mock_list_labels,
            patch(
                "app.services.ModelService.get_trained_label_ids", return_value=trained_label_ids
            ) as mock_get_trained_label_ids,
            patch(
                "app.services.data_collect.data_collector.convert_prediction", return_value=annotations
            ) as mock_convert_prediction,
        ):
            mock_create_image.return_value = media
            fxt_data_collector.collect(
                timestamp=now,
                frame_data=frame_data,
                inference_data=inference_data,
            )

        # Assert
        mock_create_image.assert_called_once()
        metadata: ImageMetadata = mock_create_image.call_args.args[0]
        assert metadata.project_id == project.id
        assert metadata.name == "1735689601_0000"
        assert metadata.image_format == ImageFormat.JPG
        assert metadata.source_id == pipeline.source_id
        assert metadata.data is not None
        mock_create_dataset_item.assert_called_once_with(
            project_id=project.id,
            task=project.task,
            media=media,
            user_reviewed=save_predictions,
            prediction_model_id=inference_data.model_id if save_predictions else None,
            annotations=annotations if save_predictions else None,
        )
        if save_predictions:
            mock_list_labels.assert_called_once_with(project_id=project.id)
            mock_get_trained_label_ids.assert_called_once_with(project_id=project.id, model_id=inference_data.model_id)
            mock_convert_prediction.assert_called_once_with(
                labels=labels,
                prediction=inference_data.prediction,
                strict=True,
                trained_labels={"gone": None, "old name": labels[0]},
            )
        else:
            mock_list_labels.assert_not_called()
            mock_get_trained_label_ids.assert_not_called()
            mock_convert_prediction.assert_not_called()
        assert fxt_data_collector.should_collect_next_frame is False

    @pytest.mark.parametrize(
        "error, frame_saved",
        [(ValueError("boom"), True), (RuntimeError("boom"), True), (SQLAlchemyError("boom"), False)],
        ids=["invalid_predictions", "unexpected_failure", "database_failure"],
    )
    def test_collect_with_failing_prediction_conversion(self, fxt_data_collector, error, frame_saved):
        """
        The frame should still be collected, without annotations, if its predictions cannot be converted
        """
        # Arrange
        pipeline = MagicMock()
        pipeline.data_collection = DataCollectionConfig(save_predictions=True)
        project = MagicMock(id=uuid4(), task=Task(task_type=TaskType.DETECTION))
        frame_data = np.random.randint(low=0, high=255, size=(100, 100), dtype=np.uint8)
        inference_data = MagicMock()
        media = MagicMock()
        fxt_data_collector.active_pipeline_data = pipeline, project
        fxt_data_collector.should_collect_next_frame = True

        # Act
        with (
            patch.object(MediaService, "create_image", return_value=media) as mock_create_image,
            patch.object(DatasetService, "create_dataset_item") as mock_create_dataset_item,
            patch("app.services.LabelService.list_all", return_value=[]),
            patch("app.services.ModelService.get_trained_label_ids", return_value={}),
            patch("app.services.data_collect.data_collector.convert_prediction", side_effect=error),
        ):
            if frame_saved:
                fxt_data_collector.collect(timestamp=1.0, frame_data=frame_data, inference_data=inference_data)
            else:
                with pytest.raises(type(error)):
                    fxt_data_collector.collect(timestamp=1.0, frame_data=frame_data, inference_data=inference_data)

        # Assert
        if frame_saved:
            mock_create_dataset_item.assert_called_once_with(
                project_id=project.id,
                task=project.task,
                media=media,
                user_reviewed=False,
                prediction_model_id=None,
                annotations=None,
            )
        else:
            mock_create_image.assert_not_called()
            mock_create_dataset_item.assert_not_called()

    @pytest.mark.parametrize("manual_capture", [False, True])
    @time_machine.travel("2025-01-01 00:00:01 +0000", tick=False)
    def test_collect_max_dataset_size_reached(self, fxt_data_collector, manual_capture):
        """
        No images should be collected if max_dataset_size limit has been reached
        """
        # Arrange
        pipeline = MagicMock()
        pipeline.data_collection = DataCollectionConfig(max_dataset_size=100, save_predictions=True)
        project = MagicMock()
        frame_data = np.random.randint(low=0, high=255, size=(100, 100), dtype=np.uint8)
        inference_data = MagicMock()

        now = datetime.timestamp(datetime.now())

        policy_checker = MagicMock()
        policy_checker.should_collect.return_value = True
        fxt_data_collector.active_pipeline_data = pipeline, project
        fxt_data_collector.policy_checkers = [policy_checker]
        fxt_data_collector.should_collect_next_frame = manual_capture

        # Act
        with (
            patch.object(DatasetService, "create_dataset_item") as mock_create_dataset_item,
            patch.object(DatasetService, "count_dataset_items", return_value=100) as mock_count_dataset_items,
            patch("app.services.LabelService.list_all") as mock_list_labels,
            patch("app.services.data_collect.data_collector.convert_prediction") as mock_convert_prediction,
        ):
            fxt_data_collector.collect(
                timestamp=now,
                frame_data=frame_data,
                inference_data=inference_data,
            )

        # Assert: should check count but not create item because limit is reached
        mock_count_dataset_items.assert_called_once_with(project=project)
        mock_create_dataset_item.assert_not_called()
        mock_list_labels.assert_not_called()
        mock_convert_prediction.assert_not_called()
        assert fxt_data_collector.should_collect_next_frame is False

    @time_machine.travel("2025-01-01 00:00:01 +0000", tick=False)
    def test_collect_max_dataset_size_not_reached(self, fxt_data_collector):
        """
        Images should be collected if max_dataset_size limit has not been reached
        """
        # Arrange
        pipeline = MagicMock()
        pipeline.data_collection = DataCollectionConfig(max_dataset_size=100)
        project = MagicMock()
        frame_data = np.random.randint(low=0, high=255, size=(100, 100), dtype=np.uint8)
        inference_data = MagicMock()

        media = MagicMock()

        now = datetime.timestamp(datetime.now())

        policy_checker = MagicMock()
        policy_checker.should_collect.return_value = True
        fxt_data_collector.active_pipeline_data = pipeline, project
        fxt_data_collector.policy_checkers = [policy_checker]
        fxt_data_collector.should_collect_next_frame = False

        # Act
        with (
            patch.object(MediaService, "create_image") as mock_create_image,
            patch.object(DatasetService, "create_dataset_item") as mock_create_dataset_item,
            patch.object(DatasetService, "count_dataset_items", return_value=50) as mock_count_dataset_items,
        ):
            mock_create_image.return_value = media
            fxt_data_collector.collect(
                timestamp=now,
                frame_data=frame_data,
                inference_data=inference_data,
            )

        # Assert: should check count and create item because under limit
        mock_count_dataset_items.assert_called_once_with(project=project)
        mock_create_dataset_item.assert_called_once()
        mock_create_image.assert_called_once()
