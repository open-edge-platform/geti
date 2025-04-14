# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the PredictionToAnnotationConverter services"""

import abc
from collections import defaultdict
from collections.abc import Generator
from typing import Any, NamedTuple

import cv2
import numpy as np
from bson import ObjectId
from geti_types import ID
from model_api.models import SegmentationModel
from model_api.models.utils import (
    AnomalyResult,
    ClassificationResult,
    DetectedKeypoints,
    DetectionResult,
    ImageResultWithSoftPrediction,
    InstanceSegmentationResult,
    ZSLVisualPromptingResult,
)
from sc_sdk.entities.annotation import Annotation
from sc_sdk.entities.label import Domain, Label
from sc_sdk.entities.label_schema import LabelSchema
from sc_sdk.entities.scored_label import ScoredLabel
from sc_sdk.entities.shapes import Ellipse, Keypoint, Point, Polygon, Rectangle, Shape

from jobs_common_extras.evaluation.utils.detection_utils import detection2array
from jobs_common_extras.evaluation.utils.segmentation_utils import create_annotation_from_segmentation_map


class IPredictionToAnnotationConverter(metaclass=abc.ABCMeta):
    """
    Interface for the converter

    :param label_schema: LabelSchema containing the label info of the task
    :param model_api_labels: list of label names or IDs from the ModelAPI configuration (i.e. XML file)
    """

    def __init__(self, label_schema: LabelSchema, model_api_labels: list[str]):
        self.labels = label_schema.get_labels(include_empty=True)
        # If label names consist of numbers, convert them to strings
        model_api_labels = [str(label_str) for label_str in model_api_labels]
        # Create a mapping of label ID to label objects
        self.label_map_ids = {}
        # Legacy OTX (<2.0) model configuration contains label names (without spaces) instead of IDs
        self.legacy_label_map_names = defaultdict(list)

        # get the first empty label
        self.empty_label = next((label for label in self.labels if label.is_empty), None)

        for i, label in enumerate(self.labels):
            self.label_map_ids[str(label.id_)] = label
            # Using a dict of list to handle duplicates label names (e.g. "foo bar", "foo_bar")
            self.legacy_label_map_names[label.name.replace(" ", "_")].append(label)
        self.legacy_label_map_names["otx_empty_lbl"] = [self.empty_label]

        # Create a mapping of ModelAPI label indices to label objects
        self.idx_to_label = {}
        self.model_api_label_map_counts: dict[str, int] = defaultdict(int)
        for i, label_str in enumerate(model_api_labels):
            self.idx_to_label[i] = self.__get_label(label_str, pos_idx=self.model_api_label_map_counts[label_str])
            self.model_api_label_map_counts[label_str] += 1

    def __get_label(self, label_str: str, pos_idx: int) -> Label:
        if label_str in self.label_map_ids:
            return self.label_map_ids[label_str]
        matched_legacy_labels = self.legacy_label_map_names[label_str]
        if pos_idx < len(matched_legacy_labels):
            return matched_legacy_labels[pos_idx]
        raise ValueError(f"Label '{label_str}' (pos_idx={pos_idx}) not found in the label schema")

    def get_label_by_idx(self, label_idx: int) -> Label:
        return self.idx_to_label[label_idx]

    @abc.abstractmethod
    def convert_to_annotations(self, predictions: NamedTuple, **kwargs) -> list[Annotation]:
        """
        Convert raw predictions to Annotation format.

        :param predictions: raw predictions from inference
        :return: lisf of annotation objects containing the shapes obtained from the raw predictions.
        """
        raise NotImplementedError


class ClassificationToAnnotationConverter(IPredictionToAnnotationConverter):
    """Converts ModelAPI Classification predictions to Annotations."""

    def convert_to_annotations(self, predictions: ClassificationResult, **kwargs) -> list[Annotation]:  # noqa: ARG002
        """
        Converts ModelAPI ClassificationResult predictions to sc_sdk annotations.

        :param predictions: classification labels represented in ModelAPI format (label_index, label_name, confidence)
        :return: list of full box annotations objects with corresponding label
        """
        labels = []
        for label_idx, label_name, prob in predictions.top_labels:
            _prob = float(prob)
            label = self.get_label_by_idx(label_idx)
            labels.append(ScoredLabel(label_id=label.id_, is_empty=label.is_empty, probability=_prob))

        if not labels and self.empty_label:
            labels = [ScoredLabel(self.empty_label.id_, is_empty=True, probability=1.0)]

        return [Annotation(Rectangle.generate_full_box(), labels=labels)]


class DetectionToAnnotationConverter(IPredictionToAnnotationConverter):
    """
    Converts ModelAPI Detection objects to Annotations.

    :param label_schema: LabelSchema containing the label info of the task
    :param model_api_labels: list of label names or IDs from the OpenVino configuration (i.e. XML file)
    :param configuration: optional model configuration setting
    """

    def __init__(self, label_schema: LabelSchema, model_api_labels: list[str], configuration: dict[str, Any] = {}):
        super().__init__(label_schema=label_schema, model_api_labels=model_api_labels)
        self.use_ellipse_shapes = configuration.get("use_ellipse_shapes", False)

    def convert_to_annotations(self, predictions: DetectionResult, **kwargs) -> list[Annotation]:
        """
        Convert ModelAPI DetectionResult predictions to sc_sdk annotations.

        :param predictions: detection represented in ModelAPI format (x1, y1, x2, y2, label, confidence).
            Note:
                - `label` can be any integer that can be mapped to `self.labels`
                - `confidence` should be a value between 0 and 1
                - `x1`, `x2`, `y1` and `y2` are expected to be normalized
        :return: list of annotations object containing the boxes obtained from the prediction
        """
        detections = detection2array(predictions.objects)
        metadata = kwargs.get("metadata")
        if metadata:
            detections[:, 2:] /= np.tile(metadata["original_shape"][1::-1], 2)

        annotations = []
        if (len(detections) and detections.shape[1:] < (6,)) or detections.shape[1:] > (7,):
            raise ValueError(
                f"Shape of prediction is not expected, expected (n, 7) or (n, 6) but got {detections.shape}"
            )

        for detection in detections:
            # Some OpenVINO models use an output shape of [7,]
            # If this is the case, skip the first value as it is not used
            _detection = detection[1:] if detection.shape == (7,) else detection

            label_idx = int(_detection[0])
            confidence = _detection[1]
            label = self.get_label_by_idx(label_idx)
            scored_label = ScoredLabel(label_id=label.id_, is_empty=label.is_empty, probability=confidence)
            coords = _detection[2:]
            shape: Ellipse | Rectangle

            if self.use_ellipse_shapes:
                shape = Ellipse(coords[0], coords[1], coords[2], coords[3])
            else:
                shape = Rectangle(coords[0], coords[1], coords[2], coords[3])

            annotation = Annotation(shape, labels=[scored_label])
            annotations.append(annotation)
        return annotations


class RotatedRectToAnnotationConverter(DetectionToAnnotationConverter):
    def get_label_by_idx(self, label_idx: int) -> Label:
        return super().get_label_by_idx(label_idx)

    def convert_to_annotations(self, predictions: InstanceSegmentationResult, **kwargs) -> list[Annotation]:
        """
        Converts ModelAPI instance segmentation predictions to a rotated bounding box annotation format.

        :param predictions: segmentation represented in ModelAPI format
        :return: list of annotations containing the rotated boxes obtained from the segmentation contours
        :raises ValueError: if metadata is missing from the preprocess step
        """
        metadata = kwargs.get("metadata")
        if metadata is None:
            raise ValueError("Cannot convert rotated detection prediction to annotation: missing metadata.")
        height, width, _ = metadata["original_shape"]
        annotations = []
        shape: Polygon | Ellipse
        for obj in predictions.segmentedObjects:
            label = self.get_label_by_idx(obj.id)
            if self.use_ellipse_shapes:
                shape = Ellipse(obj.xmin / width, obj.ymin / height, obj.xmax / width, obj.ymax / height)
                annotations.append(
                    Annotation(
                        shape,
                        labels=[ScoredLabel(label_id=label.id_, is_empty=label.is_empty, probability=float(obj.score))],
                    )
                )
            else:
                mask = obj.mask.astype(np.uint8)
                contours, hierarchies = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
                if hierarchies is None:
                    continue
                for contour, hierarchy in zip(contours, hierarchies[0]):
                    if hierarchy[3] != -1 or len(contour) <= 2 or cv2.contourArea(contour) < 1.0:
                        continue
                    points = [
                        Point(
                            x=point[0] / width,
                            y=point[1] / height,
                        )
                        for point in cv2.boxPoints(cv2.minAreaRect(contour))
                    ]
                    shape = Polygon(points=points)
                    annotations.append(
                        Annotation(
                            shape,
                            labels=[
                                ScoredLabel(label_id=label.id_, is_empty=label.is_empty, probability=float(obj.score))
                            ],
                        )
                    )
        return annotations


class SemanticSegmentationToAnnotationConverter(IPredictionToAnnotationConverter):
    """Converts ModelAPI Segmentation objects to Annotations."""

    def __init__(self, label_schema: LabelSchema, model: SegmentationModel) -> None:
        super().__init__(label_schema=label_schema, model_api_labels=model.labels)
        self.model = model

    def get_label_by_idx(self, label_idx: int) -> Label:
        # NB: index=0 is reserved for the background label
        return super().get_label_by_idx(label_idx - 1)

    def convert_to_annotations(
        self,
        predictions: ImageResultWithSoftPrediction,
        **kwargs,  # noqa: ARG002
    ) -> list[Annotation]:
        """
        Converts ModelAPI semantic segmentation predictions to sc_sdk annotations.

        :param predictions: semantic segmentation represented in ModelAPI format
        :return: list of annotations object containing the contour polygon obtained from the segmentation
        """
        # index=0 is reserved for the background label
        label_map = {label.name: label for label in self.labels}
        contours = self.model.get_contours(predictions)
        empty_label = (self.empty_label and self.empty_label.name) or "Empty"

        annotations: list[Annotation] = []
        height, width = predictions.resultImage.shape[:2]
        for contour in contours:
            if len(contour.shape) > 0 and contour.label != empty_label:
                approx_curve = cv2.approxPolyDP(contour.shape, 1.0, True)
                if len(approx_curve) > 2:
                    points = [Point(x=p[0][0] / (width - 1), y=p[0][1] / (height - 1)) for p in contour.shape]
                    label = label_map[contour.label]
                    annotations.append(
                        Annotation(
                            shape=Polygon(points=points),
                            labels=[
                                ScoredLabel(
                                    label_id=label.id_, is_empty=label.is_empty, probability=contour.probability
                                )
                            ],
                            id_=ID(ObjectId()),
                        )
                    )
        return annotations


class InstanceSegmentationToAnnotationConverter(IPredictionToAnnotationConverter):
    """
    Converts ModelAPI Segmentation objects to Annotations.

    :param label_schema: LabelSchema containing the label info of the task
    :param model_api_labels: list of label names or IDs from the OpenVino configuration (i.e. XML file)
    :param configuration: optional model configuration setting
    """

    def __init__(self, label_schema: LabelSchema, model_api_labels: list[str], configuration: dict[str, Any] = {}):
        super().__init__(label_schema=label_schema, model_api_labels=model_api_labels)
        self.use_ellipse_shapes = configuration.get("use_ellipse_shapes", False)

    def get_label_by_idx(self, label_idx: int) -> Label:
        return super().get_label_by_idx(label_idx)

    def convert_to_annotations(self, predictions: InstanceSegmentationResult, **kwargs) -> list[Annotation]:
        """
        Converts ModelAPI instance segmentation predictions to sc_sdk annotations.

        :param predictions: instance segmentation represented in ModelAPI format
        :return: list of annotations object containing the contour polygon obtained from the segmentation
        """
        annotations = []
        metadata = kwargs.get("metadata")
        if metadata is None:
            raise ValueError("Cannot convert rotated detection prediction to annotation: missing metadata.")
        height, width, _ = metadata["original_shape"]

        shape: Polygon | Ellipse
        for obj in predictions.segmentedObjects:
            label = self.get_label_by_idx(obj.id)
            if self.use_ellipse_shapes:
                shape = Ellipse(obj.xmin / width, obj.ymin / height, obj.xmax / width, obj.ymax / height)
                annotation = Annotation(
                    shape,
                    labels=[ScoredLabel(label_id=label.id_, is_empty=label.is_empty, probability=float(obj.score))],
                )
                annotations.append(annotation)
            else:
                mask = obj.mask.astype(np.uint8)
                contours, hierarchies = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
                if hierarchies is None:
                    continue
                for contour, hierarchy in zip(contours, hierarchies[0]):
                    if hierarchy[3] != -1:
                        continue
                    if len(contour) <= 2 or cv2.contourArea(contour) < 1.0:
                        continue
                    points = [
                        Point(
                            x=point[0][0] / width,
                            y=point[0][1] / height,
                        )
                        for point in list(contour)
                    ]
                    shape = Polygon(points=points)
                    annotation = Annotation(
                        shape,
                        labels=[ScoredLabel(label_id=label.id_, is_empty=label.is_empty, probability=float(obj.score))],
                    )
                    annotations.append(annotation)
        return annotations


class AnomalyToAnnotationConverter(IPredictionToAnnotationConverter):
    """
    Converts ModelAPI AnomalyResult predictions to Annotations.

    :param label_schema: LabelSchema containing the label info of the task
    """

    def __init__(self, label_schema: LabelSchema):
        self.labels = label_schema.get_labels(include_empty=True)
        self.normal_label = next(label for label in self.labels if not label.is_anomalous)
        self.anomalous_label = next(label for label in self.labels if label.is_anomalous)
        self.domain = self.anomalous_label.domain

    def convert_to_annotations(self, predictions: AnomalyResult, **kwargs) -> list[Annotation]:  # noqa: ARG002
        """
        Converts ModelAPI AnomalyResult predictions to sc_sdk annotations.

        :param predictions: anomaly result represented in ModelAPI format (same for all anomaly tasks)
        :return: list of annotation objects based on the specific anomaly task:
            - Classification: single label (normal or anomalous).
            - Segmentation: contour polygon representing the segmentation.
            - Detection: predicted bounding boxes.
        """
        pred_label = predictions.pred_label
        label = self.normal_label if pred_label.lower() == "normal" else self.anomalous_label
        # Add global full box label ["Anomalous", "Normal"]
        scored_label = ScoredLabel(
            label_id=label.id_, is_empty=label.is_empty, probability=float(predictions.pred_score)
        )
        annotations: list[Annotation] = [Annotation(Rectangle.generate_full_box(), labels=[scored_label])]
        match self.domain:
            case Domain.ANOMALY_CLASSIFICATION:
                pass
            case Domain.ANOMALY_SEGMENTATION:
                annotations.extend(
                    create_annotation_from_segmentation_map(
                        hard_prediction=predictions.pred_mask,
                        soft_prediction=predictions.anomaly_map.squeeze()
                        / 255.0,  # anomaly_map has uint8 values [0, 255]
                        label_map={0: self.normal_label, 1: self.anomalous_label},
                    )
                )
            case Domain.ANOMALY_DETECTION:
                image_h, image_w = predictions.pred_mask.shape
                for box in predictions.pred_boxes:
                    annotations.append(
                        Annotation(
                            Rectangle(box[0] / image_w, box[1] / image_h, box[2] / image_w, box[3] / image_h),
                            labels=[
                                ScoredLabel(
                                    label_id=self.anomalous_label.id_,
                                    is_empty=self.anomalous_label.is_empty,
                                    probability=predictions.pred_score,
                                )
                            ],
                        )
                    )
            case _:
                raise ValueError(
                    f"Cannot convert predictions for task '{self.domain.name}'. Only Anomaly tasks are supported."
                )
        return annotations


class KeypointToAnnotationConverter(IPredictionToAnnotationConverter):
    """Converts ModelAPI Keypoint predictions to Annotations."""

    def convert_to_annotations(self, predictions: DetectedKeypoints, **kwargs) -> list[Annotation]:
        """
        Converts ModelAPI DetectedKeypoints predictions to sc_sdk annotations.

        :param predictions: detected keypoints represented in ModelAPI format
        :return: list of annotation objects containing the keypoint coordinates and its label
        """
        annotations = []
        metadata = kwargs.get("metadata")
        if metadata is None:
            raise ValueError("Cannot convert keypoint prediction to annotation: missing metadata.")
        height, width, _ = metadata["original_shape"]
        for keypoint, score, label in zip(predictions.keypoints, predictions.scores, self.labels, strict=True):
            annotations.append(
                Annotation(
                    Keypoint(x=keypoint[0] / width, y=keypoint[1] / height, is_visible=True),
                    labels=[ScoredLabel(label_id=label.id_, is_empty=label.is_empty, probability=score)],
                )
            )

        return annotations


class VisualPromptingToAnnotationConverter(IPredictionToAnnotationConverter):
    """Converts ModelAPI VisualPromptingResult predictions to Annotations."""

    def convert_to_annotations(self, predictions: ZSLVisualPromptingResult, **kwargs) -> list[Annotation]:
        """
        Converts ModelAPI VisualPromptingResult predictions to sc_sdk annotations.

        :param predictions: visual prompting represented in ModelAPI format
        :return: list of annotations object containing the shapes obtained from the raw predictions
        """
        height, width, _ = kwargs.get("metadata", {}).get("original_shape", (None, None, None))
        if height is None or width is None:
            raise ValueError("Cannot convert VisualPrompting predictions to annotations: missing height and width.")

        annotations = []
        for label_index, predicted_mask in predictions.data.items():
            # skip on empty masks
            if not predicted_mask.mask:
                continue
            label = self.get_label_by_idx(label_index)
            masks = np.array(predicted_mask.mask).astype(np.uint8)
            scores = predicted_mask.scores
            for contour, score in zip(self._generate_object_contours(masks), scores):
                shape = self._contour_to_shape(contour, height, width, label)
                annotation = Annotation(
                    shape=shape, labels=[ScoredLabel(label_id=label.id_, is_empty=label.is_empty, probability=score)]
                )
                annotations.append(annotation)
        return annotations

    @staticmethod
    def _contour_to_shape(contour: np.ndarray, height: int, width: int, label: Label) -> Shape:
        """
        Convert a contour to a shape based on the label domain.

        :param contour: contour polygon
        :param height: image height
        :param width: image width
        :param label: label
        :return: shape object
        """
        match label.domain:
            case Domain.DETECTION:
                x, y, w, h = cv2.boundingRect(contour)
                return Rectangle(
                    x1=x / width,
                    y1=y / height,
                    x2=(x + w) / width,
                    y2=(y + h) / height,
                )
            case Domain.ROTATED_DETECTION:
                points = [
                    Point(
                        x=point[0] / width,
                        y=point[1] / height,
                    )
                    for point in cv2.boxPoints(cv2.minAreaRect(contour))
                ]
                return Polygon(points=points)
            case Domain.SEGMENTATION | Domain.INSTANCE_SEGMENTATION:
                points = [
                    Point(
                        x=point[0][0] / width,
                        y=point[0][1] / height,
                    )
                    for point in contour
                ]
                return Polygon(points=points)
        raise ValueError(f"Unsupported label domain: {label.domain} for visual prompting")

    @staticmethod
    def _generate_object_contours(
        segmentation_masks: np.ndarray | list[np.ndarray],
    ) -> Generator[np.ndarray, None, None]:
        """
        Generate object contours from segmentation masks.

        :param segmentation_masks: Segmentation masks
        :return: Generator of object contours
        """
        masks = np.array(segmentation_masks).astype(np.uint8)
        for mask in masks:
            # adding a border to the mask to avoid edge cases
            _mask = cv2.copyMakeBorder(mask, top=1, bottom=1, left=1, right=1, borderType=cv2.BORDER_CONSTANT, value=0)  # type: ignore[call-overload]
            mask_area = _mask.shape[0] * _mask.shape[1]
            min_contour_size_threshold = mask_area * 0.001  # 0.1% of the image size
            max_contour_area_threshold = mask_area * 0.9  # 90% of the image size
            max_bbox_area_threshold = mask_area * 0.98  # 98% of the image size
            contours, hierarchies = cv2.findContours(_mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE, offset=(-1, -1))
            if not contours:
                continue
            for contour, hierarchy in zip(contours, hierarchies[0]):
                # filter out: contour of the background, contours with <= 2 points, small contours
                contour_area = cv2.contourArea(contour)
                _, _, w, h = cv2.boundingRect(contour)
                bbox_area = w * h
                if (
                    hierarchy[3] != -1
                    or len(contour) <= 2
                    or contour_area < min_contour_size_threshold
                    or contour_area > max_contour_area_threshold
                    or bbox_area > max_bbox_area_threshold
                ):
                    continue
                yield contour
