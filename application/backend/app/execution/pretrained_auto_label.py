# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.execution.base import Execution, step
from app.models import (
    DatasetItemAnnotation,
    DatasetItemAnnotationStatus,
    FullImage,
    LabelReference,
    MediaType,
    Point,
    Polygon,
    Rectangle,
    TaskType,
)
from app.models.jobs import PretrainedAutoLabelJobParams
from app.services import BaseWeightsService, DatasetService, LabelService, MediaService, ProjectService
from app.services.dataset_service import DatasetItemFilters


def _tensor_to_list(value: Any) -> list[Any]:
    """Convert either an Ultralytics tensor or its ndarray test double to a Python list."""
    cpu = getattr(value, "cpu", None)
    if callable(cpu):
        value = cpu()
    return value.tolist()


@dataclass(frozen=True)
class PretrainedAutoLabelDependencies:
    base_weights_service: BaseWeightsService
    dataset_service: DatasetService
    label_service: LabelService
    media_service: MediaService
    project_service: ProjectService
    db_session_factory: Callable[[], AbstractContextManager[Session]]


class PretrainedAutoLabel(Execution[PretrainedAutoLabelJobParams]):
    """Run a verified full-head Ultralytics checkpoint and store its predictions for review."""

    params_type = PretrainedAutoLabelJobParams

    def __init__(self, dependencies: PretrainedAutoLabelDependencies) -> None:
        super().__init__()
        self._deps = dependencies

    @step("Run pretrained inference", 95)
    def auto_label(self, params: PretrainedAutoLabelJobParams) -> tuple[int, int]:  # noqa: C901, PLR0912, PLR0915
        from ultralytics import YOLO

        with self._deps.db_session_factory() as db:
            self._deps.project_service.set_db_session(db)
            self._deps.dataset_service.set_db_session(db)
            self._deps.media_service.set_db_session(db)
            project = self._deps.project_service.get_project_by_id(params.project_id)
            media = [
                media_item
                for _, media_item in self._deps.dataset_service.list_dataset_items_with_media(
                    project_id=params.project_id,
                    filters=DatasetItemFilters(
                        limit=100_000,
                        annotation_status=DatasetItemAnnotationStatus.MISSING_ANNOTATIONS,
                    ),
                )
                if media_item.type in {MediaType.IMAGE, MediaType.VIDEO_FRAME}
            ]

        if not media:
            raise ValueError("The project has no unannotated images or extracted video frames to auto-label.")

        weights = self._deps.base_weights_service.get_local_weights_path(
            task=project.task.task_type, model_manifest_id=params.model_architecture_id
        )
        paths = [str(self._deps.media_service.get_media_binary_path(params.project_id, item)) for item in media]
        results = YOLO(str(weights)).predict(paths, conf=params.confidence_threshold, verbose=False, stream=False)

        class_names: set[str] = set()
        for result in results:
            if project.task.task_type is TaskType.CLASSIFICATION and result.probs is not None:
                class_names.add(str(result.names[int(result.probs.top1)]))
            elif result.boxes is not None:
                class_names.update(str(result.names[int(index)]) for index in _tensor_to_list(result.boxes.cls))
        with self._deps.db_session_factory() as db:
            self._deps.label_service.set_db_session(db)
            labels = self._deps.label_service.list_all(params.project_id)
            labels_by_name = {label.name.casefold(): label for label in labels}
            for name in sorted(class_names, key=str.casefold):
                if name.casefold() not in labels_by_name:
                    label = self._deps.label_service.create_label(params.project_id, name, None, None)
                    labels_by_name[name.casefold()] = label

        annotated = 0
        object_count = 0
        for index, (media_item, result) in enumerate(zip(media, results, strict=True)):
            annotations: list[DatasetItemAnnotation] = []
            if project.task.task_type is TaskType.CLASSIFICATION and result.probs is not None:
                class_index = int(result.probs.top1)
                name = str(result.names[class_index])
                annotations.append(
                    DatasetItemAnnotation(
                        shape=FullImage(),
                        labels=[LabelReference(id=labels_by_name[name.casefold()].id)],
                        confidences=[float(result.probs.top1conf)],
                    )
                )
            elif result.boxes is not None:
                boxes = _tensor_to_list(result.boxes.xyxy)
                classes = _tensor_to_list(result.boxes.cls)
                confidences = _tensor_to_list(result.boxes.conf)
                polygons = result.masks.xy if result.masks is not None else None
                for prediction_index, (box, class_index, confidence) in enumerate(
                    zip(boxes, classes, confidences, strict=True)
                ):
                    name = str(result.names[int(class_index)])
                    if project.task.task_type is TaskType.INSTANCE_SEGMENTATION:
                        if polygons is None or prediction_index >= len(polygons) or len(polygons[prediction_index]) < 3:
                            continue
                        shape = Polygon(
                            points=[
                                Point(
                                    x=max(0.0, min(float(media_item.width), float(x))),
                                    y=max(0.0, min(float(media_item.height), float(y))),
                                )
                                for x, y in polygons[prediction_index]
                            ]
                        )
                    else:
                        x1, y1, x2, y2 = box
                        x1 = max(0, min(media_item.width - 1, round(x1)))
                        y1 = max(0, min(media_item.height - 1, round(y1)))
                        x2 = max(x1 + 1, min(media_item.width, round(x2)))
                        y2 = max(y1 + 1, min(media_item.height, round(y2)))
                        shape = Rectangle(
                            x=x1,
                            y=y1,
                            width=x2 - x1,
                            height=y2 - y1,
                        )
                    annotations.append(
                        DatasetItemAnnotation(
                            shape=shape,
                            labels=[LabelReference(id=labels_by_name[name.casefold()].id)],
                            confidences=[float(confidence)],
                        )
                    )

            with self._deps.db_session_factory() as db:
                self._deps.dataset_service.set_db_session(db)
                self._deps.dataset_service.set_dataset_item_annotations(
                    project=project,
                    dataset_item_id=media_item.id,
                    annotations=annotations,
                    user_reviewed=False,
                    prediction_model_id=None,
                )
            annotated += 1
            object_count += len(annotations)
            self.update_progress(10 + 85 * (index + 1) / len(media))

        return annotated, object_count

    def execute(self, params: PretrainedAutoLabelJobParams) -> None:
        annotated, object_count = self.auto_label(params)
        self.update_message(f"Auto-labeled {annotated} images with {object_count} predictions ready for review.")
