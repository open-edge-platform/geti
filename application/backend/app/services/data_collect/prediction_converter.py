# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, cast

import cv2
import numpy as np
from loguru import logger

if TYPE_CHECKING:
    from model_api.models import ClassificationResult, DetectionResult, InstanceSegmentationResult
    from model_api.models.result import Result

from app.models import DatasetItemAnnotation, FullImage, Label, LabelReference, Point, Polygon, Rectangle

# Fraction of a contour's perimeter used as the Douglas-Peucker approximation
# tolerance (epsilon) when simplifying instance-segmentation masks into polygons.
# Larger values yield fewer points (more aggressive simplification).
_POLYGON_APPROX_EPSILON_RATIO = 0.0025


def _simplify_contour(contour: np.ndarray) -> np.ndarray:
    """Reduce the number of points in a contour using the Douglas-Peucker algorithm.

    The approximation tolerance is scaled by the contour's perimeter so that
    large and small shapes are simplified proportionally. A closed approximation
    that collapses to fewer than 3 points falls back to the original contour to
    avoid producing a degenerate polygon.

    Args:
        contour: Contour as returned by ``cv2.findContours``, shaped ``(N, 1, 2)``.

    Returns:
        The simplified contour, shaped ``(M, 1, 2)`` with ``M <= N``.
    """
    epsilon = _POLYGON_APPROX_EPSILON_RATIO * cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, epsilon, True)
    if len(approx) < 3:
        return contour
    return approx


# A pair of name → label lookup tables: exact names, and names with spaces mangled to underscores.
# A ``None`` label marks a name that is known, but whose project label no longer exists.
_NameMaps = tuple[Mapping[str, Label | None], Mapping[str, Label | None]]


def _build_name_maps(labels_by_name: Mapping[str, Label | None]) -> _NameMaps:
    """Precompute name→label and unmangled-name→label dicts for O(1) lookup."""
    unmangled_map = {name.replace(" ", "_"): label for name, label in labels_by_name.items() if " " in name}
    return labels_by_name, unmangled_map


def _find_by_name(name_maps: Sequence[_NameMaps], label_name: str) -> tuple[bool, Label | None]:
    """Look a predicted label name up in each pair of lookup tables in turn.

    Returns:
        Whether a table knows the name, and the label it maps to (``None`` if that label no longer exists).
    """
    for name_map, unmangled_map in name_maps:
        if label_name in name_map:
            return True, name_map[label_name]
        # Only attempt unmangled lookup if "_" is present (avoids unnecessary dict lookup noise)
        if "_" in label_name and label_name in unmangled_map:
            return True, unmangled_map[label_name]
    return False, None


def _find_project_label(
    name_maps: Sequence[_NameMaps],
    labels: Sequence[Label],
    label_name: str | None,
    predicted_class_index: int | None = None,
    strict: bool = False,
) -> Label | None:
    """Find a project label matching the predicted label.

    Resolution order:
    1. **Name match** - looks ``label_name`` up in each entry of ``name_maps`` in turn: first as an exact name, then,
       if it contains underscores, as an unmangled name. The latter handles models that serialize label names with
       underscores instead of spaces (e.g. ``"my_cat"`` → ``"my cat"``). The first entry that knows the name decides.
    2. **Index fallback** - if no entry knows the name, returns ``labels[predicted_class_index]`` when the index is a
       non-negative integer within the bounds of ``labels``. This is only a guess: it assumes that the model orders
       its classes like ``labels`` and reports zero-based indices, which does not hold for every model type
       (instance segmentation models report one-based indices). It is therefore never used in strict mode.

    Args:
        name_maps: Name lookup tables, in order of precedence (see ``_build_name_maps``).
        labels: Ordered sequence of project labels, used for the index fallback.
        label_name: The label name as reported by the model. May be ``None`` when the model does not provide a name,
            in which case stage 1 is skipped.
        predicted_class_index: Class index produced by the model. Used only when name-based lookup fails.
            Defaults to ``None``, which disables the index fallback.
        strict: Raise ValueError instead of guessing by class index or skipping an unresolved label.

    Returns:
        The matched ``Label``, or ``None`` if no stage produced a match.
    """
    name_known, label = (False, None) if label_name is None else _find_by_name(name_maps, label_name)
    if label is not None:
        return label

    if not strict and not name_known and predicted_class_index is not None and 0 <= predicted_class_index < len(labels):
        return labels[predicted_class_index]
    if strict:
        raise ValueError(f"Prediction label {label_name!r} (index {predicted_class_index}) cannot be resolved")
    return None


def _convert_classification_prediction(
    labels: Sequence[Label],
    name_maps: Sequence[_NameMaps],
    prediction: "ClassificationResult",
    strict: bool = False,
) -> list[DatasetItemAnnotation]:
    predicted_labels: list[LabelReference] = []
    predicted_confidences: list[float] = []
    if prediction.top_labels is None:
        raise RuntimeError("The prediction is malformed because it does not contain labels")
    for predicted_label in prediction.top_labels:
        label_name = predicted_label.name
        label = _find_project_label(
            name_maps=name_maps,
            labels=labels,
            label_name=label_name,
            predicted_class_index=predicted_label.id,
            strict=strict,
        )
        if not label:
            logger.warning("Prediction label {} cannot be found in the project", label_name)
            continue
        confidence = predicted_label.confidence
        if confidence is None:
            logger.warning("The predicted label {} does not have a confidence score; assuming 1.0", label_name)
            confidence = 1.0
        predicted_labels.append(LabelReference(id=label.id))
        predicted_confidences.append(confidence)
    if not predicted_labels:
        return []
    return [DatasetItemAnnotation(labels=predicted_labels, shape=FullImage(), confidences=predicted_confidences)]


def _convert_detection_prediction(
    labels: Sequence[Label],
    name_maps: Sequence[_NameMaps],
    prediction: "DetectionResult",
    strict: bool = False,
) -> list[DatasetItemAnnotation]:
    result = []
    prediction_scores_list = prediction.scores.tolist()
    for idx, box in enumerate(prediction.bboxes):
        label_name = prediction.label_names[idx]
        bbox_confidence = prediction_scores_list[idx]
        label = _find_project_label(
            name_maps=name_maps,
            labels=labels,
            label_name=label_name,
            predicted_class_index=int(prediction.labels[idx]),
            strict=strict,
        )
        if not label:
            logger.warning("Prediction label {} cannot be found in the project", label_name)
            continue
        x1, y1, x2, y2 = box.tolist()
        annotation = DatasetItemAnnotation(
            labels=[LabelReference(id=label.id)],
            shape=Rectangle(x=x1, y=y1, width=(x2 - x1), height=(y2 - y1)),
            confidences=[bbox_confidence],
        )
        result.append(annotation)
    return result


def _convert_segmentation_prediction(
    labels: Sequence[Label],
    name_maps: Sequence[_NameMaps],
    prediction: "InstanceSegmentationResult",
    strict: bool = False,
) -> list[DatasetItemAnnotation]:
    result = []
    prediction_scores_list = prediction.scores.tolist()
    for idx, box in enumerate(prediction.bboxes):
        label_name = prediction.label_names[idx]
        polygon_confidence = prediction_scores_list[idx]
        label = _find_project_label(
            name_maps=name_maps,
            labels=labels,
            label_name=label_name,
            predicted_class_index=int(prediction.labels[idx]),
            strict=strict,
        )
        if not label:
            logger.warning("Prediction label {} cannot be found in the project", label_name)
            continue
        mask = prediction.masks[idx].astype(np.uint8)
        contours, hierarchies = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        if hierarchies is None:
            continue
        for contour, hierarchy in zip(contours, hierarchies[0]):
            if hierarchy[3] != -1:
                continue
            if len(contour) <= 2 or cv2.contourArea(contour) < 1.0:
                continue
            simplified_contour = _simplify_contour(contour)
            polygon = Polygon(points=[Point(x=point[0][0], y=point[0][1]) for point in simplified_contour])
            annotation = DatasetItemAnnotation(
                labels=[LabelReference(id=label.id)], shape=polygon, confidences=[polygon_confidence]
            )
            result.append(annotation)
    return result


def get_confidence_scores(prediction: "Result") -> list[float]:
    """
    Gets model prediction confidence scores depending on the
    specific type of prediction result (segmentation, detection, or classification).

    Args:
        prediction: Prediction result object containing model outputs, which can
                   be one of: InstanceSegmentationResult, DetectionResult, or
                   ClassificationResult.

    Returns:
        list[float]: List of confidence scores.
    """
    from model_api.models import ClassificationResult, DetectionResult, InstanceSegmentationResult

    match prediction:
        case InstanceSegmentationResult() | DetectionResult():
            return prediction.scores.tolist()
        case ClassificationResult():
            if prediction.top_labels is None:
                raise RuntimeError("The prediction is malformed because it does not contain labels")
            return [cast(float, label.confidence) for label in prediction.top_labels]
    return []


def convert_prediction(
    labels: Sequence[Label],
    prediction: "Result",
    *,
    strict: bool = False,
    trained_labels: Mapping[str, Label | None] | None = None,
) -> list[DatasetItemAnnotation]:
    """
    Converts model predictions to dataset annotations based on prediction type.

    Routes the conversion process to appropriate handlers depending on the
    specific type of prediction result (segmentation, detection, or classification).

    Args:
        labels: List of Label objects available in the project for annotation.
        prediction: Prediction result object containing model outputs, which can
                   be one of: InstanceSegmentationResult, DetectionResult, or
                   ClassificationResult.
        strict: Reject unresolved labels and unsupported prediction types instead of skipping them, and never
            guess a label from its class index.
        trained_labels: Project labels keyed by the name they had when the model was trained, with ``None`` for
            labels deleted since. These names take precedence over the current ones, so that predictions of a
            label renamed after training still resolve to it.

    Returns:
        list[DatasetItemAnnotation]: List of annotations converted from the
        prediction results. Returns empty list if prediction type is not recognized.

    Note:
        The function uses pattern matching to dispatch to appropriate conversion
        methods based on the prediction type. Each prediction type has its own
        specialized conversion logic.

    Example:
        >>> annotations = convert_prediction(
        ...     labels=project_labels,
        ...     prediction=detection_result
        ... )
    """
    from model_api.models import ClassificationResult, DetectionResult, InstanceSegmentationResult

    name_maps = [_build_name_maps({label.name: label for label in labels})]
    if trained_labels is not None:
        name_maps.insert(0, _build_name_maps(trained_labels))
    match prediction:
        case InstanceSegmentationResult():
            return _convert_segmentation_prediction(
                labels=labels, name_maps=name_maps, prediction=prediction, strict=strict
            )
        case DetectionResult():
            return _convert_detection_prediction(
                labels=labels, name_maps=name_maps, prediction=prediction, strict=strict
            )
        case ClassificationResult():
            return _convert_classification_prediction(
                labels=labels, name_maps=name_maps, prediction=prediction, strict=strict
            )
    if strict:
        raise ValueError(f"Unsupported prediction type: {type(prediction).__name__}")
    return []
