# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from unittest.mock import patch
from uuid import UUID

import numpy as np
import pytest
from model_api.models import ClassificationResult, DetectionResult, InstanceSegmentationResult
from model_api.models.result import Label as PredictedLabel
from model_api.models.result import Result
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.datumaro_converter import SampleMode
from app.db.schema import DatasetItemDB, DatasetItemLabelDB, MediaDB
from app.models import (
    DataCollectionConfig,
    DatasetItemAnnotationStatus,
    FixedRateDataCollectionPolicy,
    Pipeline,
    Project,
    TaskType,
)
from app.services.data_collect.data_collector import DataCollector, FixedRatePolicyChecker
from app.services.dataset_service import AnnotationValidationError, DatasetService
from app.services.media_service import MediaService
from app.stream.stream_data import InferenceData


@pytest.fixture
def fxt_capture(
    request,
    db_session,
    fxt_db_projects,
    fxt_db_models,
    fxt_db_labels,
    fxt_project_service,
    fxt_event_bus,
    fxt_projects_dir: Path,
    monkeypatch,
) -> tuple[DataCollector, Project, UUID]:
    task_type, exclusive_labels = getattr(request, "param", (TaskType.DETECTION, True))
    db_project = fxt_db_projects[0]
    db_project.task_type = task_type
    db_project.exclusive_labels = exclusive_labels
    db_session.add(db_project)
    db_session.flush()
    db_model = fxt_db_models[0]
    db_model.project_id = db_project.id
    for label in fxt_db_labels:
        label.project_id = db_project.id
    db_session.add_all([db_model, *fxt_db_labels])
    db_session.flush()
    project = fxt_project_service.get_project_by_id(UUID(db_project.id))
    monkeypatch.setattr(
        "app.db.engine.SessionLocal",
        sessionmaker(bind=db_session.connection(), join_transaction_mode="create_savepoint"),
    )
    with patch.object(DataCollector, "_load_pipeline"):
        collector = DataCollector(fxt_projects_dir.parent, fxt_event_bus)
    collector.active_pipeline_data = (
        Pipeline(project_id=project.id, data_collection=DataCollectionConfig(save_predictions=True)),
        project,
    )
    return collector, project, UUID(db_model.id)


def _prediction(task_type: TaskType, scenario: str) -> Result:
    empty = scenario == "empty"
    label_id, label_name = (99, "unknown") if scenario == "unknown" else (0, "cat")
    if task_type == TaskType.CLASSIFICATION:
        return ClassificationResult(
            top_labels=[] if empty else [PredictedLabel(id=label_id, name=label_name, confidence=0.9)]
        )
    extent = 24 if scenario == "out_of_bounds" else 19
    boxes = np.empty((0, 4)) if empty else np.array([[0, 0, extent, extent]])
    labels = np.array([] if empty else [label_id], dtype=np.int64)
    scores = np.array([] if empty else [0.9])
    names = [] if empty else [label_name]
    if task_type == TaskType.INSTANCE_SEGMENTATION:
        return InstanceSegmentationResult(
            bboxes=boxes,
            labels=labels,
            scores=scores,
            label_names=names,
            masks=np.ones((len(labels), extent + 1, extent + 1), dtype=np.uint8),
        )
    return DetectionResult(bboxes=boxes, labels=labels, scores=scores, label_names=names)


class TestDataCollectorIntegration:
    @pytest.mark.parametrize(
        "fxt_capture",
        [
            pytest.param((TaskType.CLASSIFICATION, True), id="multiclass"),
            pytest.param((TaskType.CLASSIFICATION, False), id="multilabel"),
            pytest.param((TaskType.DETECTION, True), id="detection"),
            pytest.param((TaskType.INSTANCE_SEGMENTATION, True), id="segmentation"),
        ],
        indirect=True,
    )
    @pytest.mark.parametrize("scenario", ["valid", "empty", "unknown"])
    @pytest.mark.parametrize("manual_capture", [True, False])
    @pytest.mark.parametrize("save_predictions", [True, False])
    def test_capture_real_predictions(
        self,
        fxt_capture,
        fxt_dataset_service,
        fxt_media_service,
        db_session: Session,
        fxt_projects_dir: Path,
        scenario: str,
        manual_capture: bool,
        save_predictions: bool,
    ) -> None:
        collector, project, model_id = fxt_capture
        pipeline, _ = collector.active_pipeline_data
        pipeline.data_collection.save_predictions = save_predictions
        if manual_capture:
            collector.collect_next_frame()
        else:
            collector.policy_checkers = [FixedRatePolicyChecker(FixedRateDataCollectionPolicy(rate=1))]
        frame = np.zeros((20, 20), dtype=np.uint8)
        collector.collect(
            timestamp=1,
            frame_data=frame,
            inference_data=InferenceData(
                prediction=_prediction(project.task.task_type, scenario),
                visualized_prediction=np.full_like(frame, 255),
                model_id=model_id,
            ),
        )

        item = db_session.scalars(select(DatasetItemDB).where(DatasetItemDB.project_id == str(project.id))).one()
        reviewed = (
            save_predictions
            and scenario != "unknown"
            and not (
                scenario == "empty"
                and project.task.task_type == TaskType.CLASSIFICATION
                and project.task.exclusive_labels
            )
        )
        assert item.user_reviewed is reviewed
        assert item.prediction_model_id == (str(model_id) if reviewed else None)
        if reviewed and scenario == "valid":
            assert item.annotation_data is not None
            assert len(item.annotation_data) == 1
            assert item.annotation_data[0]["confidences"] is None
            cat = next(label for label in project.task.labels if label.name == "cat")
            assert item.annotation_data[0]["labels"] == [{"id": str(cat.id)}]
        else:
            assert item.annotation_data == ([] if reviewed else None)
        links = db_session.scalars(
            select(DatasetItemLabelDB).where(DatasetItemLabelDB.dataset_item_id == item.id)
        ).all()
        assert len(links) == (1 if reviewed and scenario == "valid" else 0)
        media = fxt_media_service.get_media_by_id(project_id=project.id, media_id=UUID(item.id))
        image_path = fxt_media_service.get_media_binary_path(project_id=project.id, media=media)
        thumbnail_path = fxt_media_service.get_media_thumbnail_path(project=project, media=media)
        assert set((fxt_projects_dir / str(project.id) / "dataset").iterdir()) == {image_path, thumbnail_path}
        with Image.open(image_path) as saved_image:
            np.testing.assert_array_equal(np.asarray(saved_image), frame)
        assert collector.should_collect_next_frame is False
        for sample_mode in SampleMode:
            dataset = fxt_dataset_service.get_dm_dataset(
                project_id=project.id,
                task=project.task,
                annotation_status=DatasetItemAnnotationStatus.WITH_ANNOTATIONS,
                sample_mode=sample_mode,
            )
            assert len(list(dataset)) == int(reviewed)

    @pytest.mark.parametrize(
        "fxt_capture", [(TaskType.DETECTION, True), (TaskType.INSTANCE_SEGMENTATION, True)], indirect=True
    )
    def test_invalid_coordinates_are_checked_before_writing(
        self, fxt_capture, db_session: Session, fxt_projects_dir: Path
    ) -> None:
        collector, project, model_id = fxt_capture
        frame = np.zeros((20, 20), dtype=np.uint8)
        dataset_dir = fxt_projects_dir / str(project.id) / "dataset"
        validate = DatasetService.validate_annotations

        def validate_before_write(*args, **kwargs) -> None:
            assert list(dataset_dir.glob("*.jpg")) == []
            validate(*args, **kwargs)

        collector.collect_next_frame()
        with patch.object(DatasetService, "validate_annotations", side_effect=validate_before_write) as validation:
            collector.collect(
                timestamp=1,
                frame_data=frame,
                inference_data=InferenceData(
                    prediction=_prediction(project.task.task_type, "out_of_bounds"),
                    visualized_prediction=frame,
                    model_id=model_id,
                ),
            )
        validation.assert_called_once()
        item = db_session.scalars(select(DatasetItemDB).where(DatasetItemDB.project_id == str(project.id))).one()
        assert item.user_reviewed is False
        assert item.annotation_data is None
        assert item.prediction_model_id is None
        assert len(list(dataset_dir.glob("*.jpg"))) == 2
        assert collector.should_collect_next_frame is False

    @pytest.mark.parametrize("failure", ["validation", "database", "commit"])
    def test_failed_capture_removes_files_and_does_not_retry(
        self, fxt_capture, db_session: Session, fxt_projects_dir: Path, failure: str
    ) -> None:
        collector, project, model_id = fxt_capture
        dataset_dir = fxt_projects_dir / str(project.id) / "dataset"
        frame = np.zeros((20, 20), dtype=np.uint8)
        inference = InferenceData(
            prediction=_prediction(project.task.task_type, "valid"), visualized_prediction=frame, model_id=model_id
        )
        error = (
            AnnotationValidationError("injected failure")
            if failure == "validation"
            else RuntimeError("injected failure")
        )

        def fail_after_writing(*args, **kwargs) -> None:
            assert len(list(dataset_dir.glob("*.jpg"))) == 2
            raise error

        target, method = (Session, "commit") if failure == "commit" else (DatasetService, "create_dataset_item")
        collector.collect_next_frame()
        with (
            patch.object(target, method, side_effect=fail_after_writing),
            pytest.raises(type(error), match="injected failure"),
        ):
            collector.collect(timestamp=1, frame_data=frame, inference_data=inference)

        assert collector.should_collect_next_frame is False
        assert list(dataset_dir.glob("*.jpg")) == []
        assert db_session.scalars(select(MediaDB).where(MediaDB.project_id == str(project.id))).all() == []
        assert db_session.scalars(select(DatasetItemDB).where(DatasetItemDB.project_id == str(project.id))).all() == []
        collector.collect(timestamp=2, frame_data=frame, inference_data=inference)
        assert list(dataset_dir.glob("*.jpg")) == []

    def test_capture_preserves_new_manual_request(self, fxt_capture) -> None:
        collector, project, model_id = fxt_capture
        create_image = MediaService.create_image

        def create_and_request(service, metadata):
            collector.collect_next_frame()
            return create_image(service, metadata)

        frame = np.zeros((20, 20), dtype=np.uint8)
        collector.collect_next_frame()
        with patch.object(MediaService, "create_image", autospec=True, side_effect=create_and_request):
            collector.collect(
                timestamp=1,
                frame_data=frame,
                inference_data=InferenceData(
                    prediction=_prediction(project.task.task_type, "valid"),
                    visualized_prediction=frame,
                    model_id=model_id,
                ),
            )
        assert collector.should_collect_next_frame is True
