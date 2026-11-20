# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from abc import ABCMeta, abstractmethod
from pathlib import Path

import cv2
import numpy as np
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db import get_db_session
from app.models import (
    ConfidenceThresholdDataCollectionPolicy,
    DatasetItemAnnotation,
    FixedRateDataCollectionPolicy,
    Pipeline,
    Project,
)
from app.models.media import ImageFormat
from app.services.data_collect.prediction_converter import convert_prediction, get_confidence_scores
from app.services.event.event_bus import EventBus, EventType
from app.services.media_service import ImageMetadata
from app.stream.stream_data import InferenceData


class PolicyChecker(metaclass=ABCMeta):
    @abstractmethod
    def should_collect(self, timestamp: float, confidence_scores: list[float]) -> bool:
        """
        Determines whether a dispatched image should be collected to the project dataset.

        Args:
            timestamp: Floating-point timestamp representing when the image was
                    dispatched, in seconds since epoch.
            confidence_scores: Floating-point timestamp predictions confidence scores.

        Returns:
            bool: True if the image meets the collection criteria and should be
                added to the dataset, False otherwise.

        Note:
            This is an abstract method and must be implemented by subclasses.
            Different policy implementations may use different strategies such as
            time-based sampling, random sampling, or condition-based triggering.
        """


class FixedRatePolicyChecker(PolicyChecker):
    """
    Fixed rate data collection policy checker.
    Checks when the last image has been collected against collection rate.
    """

    def __init__(self, policy: FixedRateDataCollectionPolicy):
        if policy.rate is None or policy.rate <= 0:
            raise ValueError(f"Collection rate must be a positive float, got {policy.rate} instead.")
        self.min_interval = 1.0 / policy.rate
        self.last_collect_time = 0.0

    def should_collect(self, timestamp: float, confidence_scores: list[float]) -> bool:
        time_since_last = timestamp - self.last_collect_time
        if time_since_last < self.min_interval:
            return False
        self.last_collect_time = timestamp
        return True


class ConfidenceThresholdPolicyChecker(PolicyChecker):
    """
    Confidence threshold data collection policy checker.
    Collects only images where any prediction confidence is lower than predefined threshold.
    To prevent the collection of multiple, almost identical frames in rapid succession, it also checks image timestamp
    with min_sampling_interval.
    """

    def __init__(self, policy: ConfidenceThresholdDataCollectionPolicy):
        self.confidence_threshold = policy.confidence_threshold
        self.min_sampling_interval = policy.min_sampling_interval
        self.last_collect_time = 0.0

    def should_collect(self, timestamp: float, confidence_scores: list[float]) -> bool:
        time_since_last = timestamp - self.last_collect_time

        if (
            all(confidence >= self.confidence_threshold for confidence in confidence_scores)
            or time_since_last < self.min_sampling_interval
        ):
            return False
        self.last_collect_time = timestamp
        return True


class DataCollector:
    def __init__(self, data_dir: Path, event_bus: EventBus) -> None:
        self.should_collect_next_frame = False
        self.data_dir = data_dir
        self.event_bus = event_bus
        self.active_pipeline_data: tuple[Pipeline, Project] | None = None
        self.policy_checkers: list[PolicyChecker] = []

        self._load_pipeline()
        event_bus.subscribe(
            [
                EventType.PIPELINE_STATUS_CHANGED,
                EventType.PIPELINE_DATASET_COLLECTION_POLICIES_CHANGED,
                EventType.SOURCE_CHANGED,
            ],
            self._load_pipeline,
        )

    def _load_pipeline(self) -> None:
        from app.services import LabelService, ModelService, PipelineService, ProjectService, SystemService

        with get_db_session() as db:
            label_service = LabelService(db_session=db)
            system_service = SystemService()
            pipeline_service = PipelineService(
                event_bus=self.event_bus,
                db_session=db,
                system_service=system_service,
                model_service=ModelService(data_dir=self.data_dir, db_session=db),
            )
            pipeline = pipeline_service.get_active_pipeline()
            if pipeline is None:
                logger.info("No active pipeline found, disabling data collection")
                self.active_pipeline_data = None
                self.policy_checkers = []
                return

            project_service = ProjectService(
                data_dir=self.data_dir, db_session=db, label_service=label_service, pipeline_service=pipeline_service
            )
            project = project_service.get_project_by_id(pipeline.project_id)

            self.active_pipeline_data = pipeline, project
            logger.info(
                "Data collection config set to {}, source: {}",
                pipeline.data_collection,
                pipeline.source_id,
            )

            policies = [policy for policy in pipeline.data_collection.policies if policy.enabled]
            self.policy_checkers = []
            for policy in policies:
                checker: PolicyChecker | None = None
                match policy:
                    case FixedRateDataCollectionPolicy():
                        checker = FixedRatePolicyChecker(policy)
                    case ConfidenceThresholdDataCollectionPolicy():
                        checker = ConfidenceThresholdPolicyChecker(policy)
                if checker is not None:
                    self.policy_checkers.append(checker)

    def collect(
        self,
        timestamp: float,
        frame_data: np.ndarray,
        inference_data: InferenceData,
    ) -> None:
        """
        Collects dispatched images to project dataset based on policy checkers.

        Evaluates automated collection policies and the manual next-frame trigger to determine if image
        should be added to dataset. Stores the image without annotations by default, or with the
        frame's model predictions as reviewed annotations when save_predictions is enabled.

        Args:
            timestamp: Floating-point timestamp of the captured image, used for item naming.
            frame_data: Image data in numpy ndarray format (expected in BGR color space).
            inference_data: Inference data containing model predictions and model identifier.

        Returns:
            None: Method performs operations with side effects but returns no value.

        Note:
            Collection occurs if any policy checker returns True OR if the
            should_collect_next_frame flag is set. Timestamp is formatted to string
            with 4 decimal places for use as dataset item name.
            Collection is skipped if max_dataset_size is set and the dataset has reached that limit.
        """
        if self.active_pipeline_data is None:
            return
        pipeline, project = self.active_pipeline_data
        from app.services import DatasetService, LabelService, MediaService

        manual_capture = self.should_collect_next_frame
        self.should_collect_next_frame = False
        confidence_scores = get_confidence_scores(prediction=inference_data.prediction)
        should_collect = (
            any(
                checker.should_collect(timestamp=timestamp, confidence_scores=confidence_scores)
                for checker in self.policy_checkers
            )
            or manual_capture
        )
        if not should_collect:
            return
        # Convert only 3-channel BGR images to RGB; pass grayscale / other formats through.
        if frame_data.ndim == 3 and frame_data.shape[2] == 3:
            frame_data = cv2.cvtColor(frame_data, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
        image_paths: tuple[Path, ...] = ()
        try:
            with get_db_session() as session:
                label_service = LabelService(db_session=session)
                media_service = MediaService(data_dir=self.data_dir, db_session=session)
                dataset_service = DatasetService(
                    label_service=label_service, media_service=media_service, db_session=session
                )

                max_dataset_size = pipeline.data_collection.max_dataset_size
                if max_dataset_size is not None:
                    current_count = dataset_service.count_dataset_items(project=project)
                    if current_count >= max_dataset_size:
                        logger.debug(
                            "Dataset has reached max size limit ({}/{}), skipping data collection",
                            current_count,
                            max_dataset_size,
                        )
                        return

                annotations = None
                if pipeline.data_collection.save_predictions:
                    annotations = self._convert_predictions(
                        session=session, project=project, inference_data=inference_data, frame_data=frame_data
                    )

                media = media_service.create_image(
                    ImageMetadata(
                        project_id=project.id,
                        data=frame_data,
                        name=f"{timestamp:.4f}".replace(".", "_"),
                        image_format=ImageFormat.JPG,
                        source_id=pipeline.source_id,
                    )
                )
                image_paths = (
                    media_service.get_media_binary_path(project_id=project.id, media=media),
                    media_service.get_media_thumbnail_path(project=project, media=media),
                )
                dataset_service.create_dataset_item(
                    project_id=project.id,
                    task=project.task,
                    media=media,
                    user_reviewed=annotations is not None,
                    prediction_model_id=inference_data.model_id if annotations is not None else None,
                    annotations=annotations,
                )
        except Exception:
            self._discard_capture_artifacts(image_paths)
            raise

    def _convert_predictions(
        self, session: Session, project: Project, inference_data: InferenceData, frame_data: np.ndarray
    ) -> list[DatasetItemAnnotation] | None:
        """
        Converts the predictions of a frame to the annotations to save with it.

        Returns:
            The annotations, or None if the predictions cannot be saved as annotations: the frame is then
            collected without them.
        """
        from app.services import DatasetService, LabelService, ModelService
        from app.services.base import ResourceNotFoundError
        from app.services.dataset_service import AnnotationValidationError

        labels = LabelService(db_session=session).list_all(project_id=project.id)
        try:
            trained_label_ids = ModelService(data_dir=self.data_dir, db_session=session).get_trained_label_ids(
                project_id=project.id, model_id=inference_data.model_id
            )
            labels_by_id = {label.id: label for label in labels}
            annotations = convert_prediction(
                labels=labels,
                prediction=inference_data.prediction,
                strict=True,
                # The model reports the label names it was trained with: a label renamed since then is
                # found through its ID, and one deleted since then maps to None (unresolvable).
                trained_labels={name: labels_by_id.get(label_id) for name, label_id in trained_label_ids.items()},
            )
            DatasetService.validate_annotations(
                annotations=annotations,
                task=project.task,
                labels=labels,
                media_width=frame_data.shape[1],
                media_height=frame_data.shape[0],
            )
        except SQLAlchemyError:
            # A database failure is not a prediction problem: abort the capture before writing any file.
            raise
        except (AnnotationValidationError, ResourceNotFoundError, ValueError) as error:
            logger.warning("Saving captured frame without invalid predictions: {}", error)
        except Exception:
            # Saving the predictions is optional: an unexpected failure must not cost the frame itself.
            logger.exception("Could not convert predictions; saving captured frame without them")
        else:
            return annotations
        return None

    @staticmethod
    def _discard_capture_artifacts(image_paths: tuple[Path, ...]) -> None:
        for path in image_paths:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                logger.exception("Could not remove failed capture artifact {}", path)

    def collect_next_frame(self) -> None:
        """
        Request one collection attempt for the next available frame, without retrying failures automatically.
        """
        self.should_collect_next_frame = True
