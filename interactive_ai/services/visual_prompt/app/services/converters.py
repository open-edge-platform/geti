# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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
from collections.abc import Callable, Generator, Iterable

import cv2
import numpy as np
from model_api.models.utils import PredictedMask
from model_api.models.visual_prompting import Prompt, VisualPromptingFeatures

from entities.reference_feature import ReferenceFeature, ReferenceMediaInfo

from geti_types import ID
from sc_sdk.entities.annotation import Annotation, AnnotationScene
from sc_sdk.entities.label import Label
from sc_sdk.entities.scored_label import LabelSource, ScoredLabel
from sc_sdk.entities.shapes import Ellipse, Point, Polygon, Rectangle, Shape

logger = logging.getLogger(__name__)


class LabelIndexConverter:
    """
    Utility class for converting label IDs to and from integer indices.

    This is useful for interacting with ModelAPI's visual prompting entities, which require labels in integer format.

    :param label_ids: List of label IDs to map
    """

    def __init__(self, label_ids: list[ID]) -> None:
        self._label_map = {}
        # sorting is label IDs is needed since ModelAPI represents label with positional index
        self._label_ids = sorted(label_ids)
        for i, label_id in enumerate(self._label_ids):
            self._label_map[label_id] = i

    def label_id_to_index(self, label_id: ID) -> int:
        return self._label_map[label_id]

    def index_to_label_id(self, index: int) -> ID:
        return self._label_ids[index]


class VisualPromptingFeaturesConverter(LabelIndexConverter):
    """Utility class for converting visual prompting features to and from reference features."""

    def convert_to_visual_prompting_features(
        self, reference_features: Iterable[ReferenceFeature]
    ) -> VisualPromptingFeatures:
        """
        Convert reference features to visual prompting features in ModelAPI's format.

        :param reference_features: List of reference features entities
        :return: Visual prompting features in ModelAPI's format
        """
        # ModelAPI expects len(feature_vectors) == num of labels
        feature_vectors: list[np.ndarray | None] = [None] * len(self._label_ids)
        used_indices = []
        for ref in reference_features:
            idx = self.label_id_to_index(ref.label_id)
            feature_vectors[idx] = ref.numpy
            used_indices.append(idx)
        return VisualPromptingFeatures(feature_vectors=feature_vectors, used_indices=used_indices)

    def convert_to_reference_features(
        self, visual_prompting_features: VisualPromptingFeatures, reference_media_info: ReferenceMediaInfo, task_id: ID
    ) -> list[ReferenceFeature]:
        """
        Converts ModelAPI's visual prompting features to reference feature entities.

        :param visual_prompting_features: ModelAPI's visual prompting features
        :param reference_media_info: Reference media info
        :param task_id: Task ID of the learned label
        :return: List of reference features
        """
        reference_features = []
        feature_vectors = visual_prompting_features.feature_vectors
        used_indices = visual_prompting_features.used_indices

        for used_index in used_indices:
            feature_vec = feature_vectors[used_index]
            label_id = self.index_to_label_id(used_index)
            reference_features.append(
                ReferenceFeature(task_id=task_id, label_id=label_id, numpy=feature_vec, media_info=reference_media_info)
            )
        return reference_features


class PromptConverter(LabelIndexConverter):
    """Utility class for converting annotations to visual prompts"""

    def extract_polygon_prompts(self, annotation_scene: AnnotationScene, height: int, width: int) -> list[Prompt]:
        """
        Extract polygon prompts from annotation shapes (polygon shapes only).

        :param annotation_scene: Annotation scene containing the annotations to extract prompts from
        :param height: Height of the image in pixels
        :param width: Width of the image in pixels
        :return: List of extracted polygon prompts
        """
        prompts = []
        for annotation in annotation_scene.annotations:
            shape = annotation.shape
            if not isinstance(shape, Polygon):
                continue
            data = np.array([[point.x * width, point.y * height] for point in shape.points])
            for label in annotation.get_labels():
                if label.id_ not in self._label_map:
                    continue
                prompts.append(Prompt(data=data, label=self.label_id_to_index(label.id_)))
        return prompts

    def extract_bbox_prompts(self, annotation_scene: AnnotationScene, height: int, width: int) -> list[Prompt]:
        """
        Extract rectangle bounding box prompts from annotation shapes (ellipse and rectangle shapes only).

        :param annotation_scene: Annotation scene containing the annotations to extract prompts from
        :param height: Height of the image in pixels
        :param width: Width of the image in pixels
        :return: List of extracted bounding box prompts (in XYXY torchvision format)
        """
        prompts = []
        for annotation in annotation_scene.annotations:
            shape = annotation.shape
            if not isinstance(shape, Ellipse | Rectangle):
                continue
            data = np.array([shape.x1 * width, shape.y1 * height, shape.x2 * width, shape.y2 * height])
            for label in annotation.get_labels():
                if label.id_ not in self._label_map:
                    continue
                prompts.append(Prompt(data=data, label=self.label_id_to_index(label.id_)))
        return prompts


class AnnotationConverter:
    """Utility class for converting segmentation mask to annotations"""

    @staticmethod
    def generate_object_contours(
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

    @classmethod
    def _convert_to_annotation(
        cls,
        predicted_mask: PredictedMask,
        predicted_label: Label,
        contour_forward_map: Callable[[np.ndarray, int, int], Shape],
        label_source: LabelSource,
    ) -> list[Annotation]:
        """
        Convert predicted mask to annotations.

        :param predicted_mask: Predicted mask
        :param predicted_label: Predicted label
        :param contour_forward_map: Function to convert contour to shape
        :param label_source: the source of the label
        :return: List of annotations
        """
        if not predicted_mask.mask:
            return []

        masks = np.array(predicted_mask.mask).astype(np.uint8)
        scores = predicted_mask.scores
        height, width = masks.shape[1:]

        annotations = []
        for contour, score in zip(cls.generate_object_contours(masks), scores):
            shape = contour_forward_map(contour, height, width)
            annotation = Annotation(
                shape=shape,
                labels=[
                    ScoredLabel(
                        label_id=predicted_label.id_,
                        is_empty=predicted_label.is_empty,
                        probability=score,
                        label_source=label_source,
                    )
                ],
            )
            annotations.append(annotation)
        return annotations

    @classmethod
    def convert_to_bboxes(
        cls, predicted_mask: PredictedMask, predicted_label: Label, label_source: LabelSource
    ) -> list[Annotation]:
        """
        Convert predicted mask to annotations with bounding boxes.

        :param predicted_mask: Inference result from ModelAPI, consisting of a list of segmentation masks
            for each detected object and a list of corresponding scores
        :param predicted_label: the label of the segmentation masks
        :param label_source: the source of the label
        :return: List of bounding box annotations
        """

        def contour_to_bbox(contour: np.ndarray, height: int, width: int) -> Shape:
            x, y, w, h = cv2.boundingRect(contour)
            return Rectangle(
                x1=x / width,
                y1=y / height,
                x2=(x + w) / width,
                y2=(y + h) / height,
            )

        return cls._convert_to_annotation(predicted_mask, predicted_label, contour_to_bbox, label_source=label_source)

    @classmethod
    def convert_to_rotated_bboxes(
        cls, predicted_mask: PredictedMask, predicted_label: Label, label_source: LabelSource
    ) -> list[Annotation]:
        """
        Convert predicted mask to annotations with rotated bounding boxes.

        :param predicted_mask: Inference result from ModelAPI, consisting of a list of segmentation masks
            for each detected object and a list of corresponding scores
        :param predicted_label: the label of the segmentation masks
        :param label_source: the source of the label
        :return: List of rotated bounding box annotations
        """

        def contour_to_rotated_rect(contour: np.ndarray, height: int, width: int) -> Shape:
            points = [
                Point(
                    x=point[0] / width,
                    y=point[1] / height,
                )
                for point in cv2.boxPoints(cv2.minAreaRect(contour))
            ]
            return Polygon(points=points)

        return cls._convert_to_annotation(
            predicted_mask, predicted_label, contour_to_rotated_rect, label_source=label_source
        )

    @classmethod
    def convert_to_polygons(
        cls, predicted_mask: PredictedMask, predicted_label: Label, label_source: LabelSource
    ) -> list[Annotation]:
        """
        Convert predicted mask to annotations with polygons.

        :param predicted_mask: Inference result from ModelAPI, consisting of a list of segmentation masks
            for each detected object and a list of corresponding scores
        :param predicted_label: the label of the segmentation masks
        :param label_source: the source of the label
        :return: List of polygon annotations
        """

        def contour_to_polygon(contour: np.ndarray, height: int, width: int) -> Shape:
            points = [
                Point(
                    x=point[0][0] / width,
                    y=point[0][1] / height,
                )
                for point in contour
            ]
            return Polygon(points=points)

        return cls._convert_to_annotation(
            predicted_mask, predicted_label, contour_to_polygon, label_source=label_source
        )
