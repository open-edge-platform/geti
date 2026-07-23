# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from functools import lru_cache
from typing import TYPE_CHECKING

import numpy as np
from loguru import logger
from PIL import Image

from app.utils.singleton import Singleton

if TYPE_CHECKING:
    from model_api.models.result import Result


def _compute_scale(image: np.ndarray) -> float:
    """Compute a font/outline scale factor based on the image's longer edge.

    Uses SCALE_BASELINE (720p longer edge = 1280) as the reference: at 1280px the
    scale is 1.0; at 4K (3840px) the scale is ~3.0. Never shrinks below 1.0.
    """
    from model_api.visualizer.defaults import SCALE_BASELINE

    if image is None or image.size == 0:
        return 1.0
    h, w = image.shape[:2]
    longer_edge = float(max(int(h), int(w)))
    return max(1.0, longer_edge / float(SCALE_BASELINE))


@lru_cache(maxsize=32)
def _merge_project_colors_cached(
    label_names: tuple[str, ...], project_colors: tuple[tuple[str, str], ...]
) -> dict[str, str]:
    """Cached core of :func:`_merge_project_colors`.

    Keyed on hashable, order-preserving representations of the inputs so that the (typically stable)
    palette for a loaded model is only built once instead of on every streamed frame. Returns a copy
    on each call so callers can safely mutate the result without corrupting the cache.
    """
    from model_api.visualizer.utils import get_label_color_mapping

    color_per_label = get_label_color_mapping(list(label_names))
    project_colors_map = dict(project_colors)
    for name in label_names:
        if name in project_colors_map:
            color_per_label[name] = project_colors_map[name]
    return color_per_label


def _merge_project_colors(label_names: list[str], project_colors: dict[str, str]) -> dict[str, str]:
    """Build a label-name to color mapping that prefers the project colors.

    Starts from the Model API default palette (so every predicted label is guaranteed a color)
    and overrides it with the project-defined colors wherever the label name matches. This keeps
    the inference stream colors consistent with the label colors used for human annotations and
    AI predictions elsewhere in the project.

    The merge is memoized on ``(label_names, project_colors)`` since both are typically stable for a
    loaded model, avoiding repeated palette construction on every streamed frame. A fresh copy is
    returned so the caller may mutate it freely.
    """
    merged = _merge_project_colors_cached(tuple(label_names), tuple(sorted((project_colors or {}).items())))
    return dict(merged)


class VisualizerCreator(ABC):
    """Abstract base class for visualizer creators."""

    @abstractmethod
    def create_visualization(
        self,
        original_image: np.ndarray,
        predictions: "Result",
        label_colors: dict[str, str] | None = None,
    ) -> np.ndarray:
        """Create a visualization of the predictions on the original image.

        Args:
            original_image: The image to draw the predictions on.
            predictions: Model API prediction result.
            label_colors: Optional mapping of label name to hex color (e.g. ``"#RRGGBB"``) coming
                from the project definition. When provided, these colors are used so that the
                inference stream matches the label colors shown elsewhere in the project
                (human annotations and AI predictions). Labels absent from this mapping fall back
                to the Model API default palette.
        """


class ClassificationVisualizerCreator(VisualizerCreator):
    """Creator for classification visualizations."""

    def create_visualization(
        self,
        original_image: np.ndarray,
        predictions: "Result",
        label_colors: dict[str, str] | None = None,
    ) -> np.ndarray:
        from model_api.models.result import ClassificationResult
        from model_api.visualizer.defaults import DEFAULT_FONT_SIZE
        from model_api.visualizer.primitive import Label
        from model_api.visualizer.scene import ClassificationScene

        if not isinstance(predictions, ClassificationResult):
            raise TypeError(f"Expected a ClassificationResult, got {type(predictions)}.")
        image_pil = Image.fromarray(original_image)
        scale = _compute_scale(original_image)
        classification_scene = ClassificationScene(
            image=image_pil,
            result=predictions,
            scale=scale,
        )
        # ClassificationScene draws every label with the same default background color. Recolor the
        # labels with the project colors so the stream matches the project's label colors.
        if label_colors and predictions.top_labels:
            labels = []
            for label in predictions.top_labels:
                if label.name is None:
                    continue
                kwargs = {}
                color = label_colors.get(label.name)
                if color:
                    kwargs["bg_color"] = color
                labels.append(
                    Label(label=label.name, score=label.confidence, size=int(DEFAULT_FONT_SIZE * scale), **kwargs)
                )
            classification_scene.label = classification_scene._to_label(labels)
        rendered = classification_scene.render()
        return np.array(rendered)


class DetectionVisualizerCreator(VisualizerCreator):
    """Creator for detection visualizations."""

    def create_visualization(
        self,
        original_image: np.ndarray,
        predictions: "Result",
        label_colors: dict[str, str] | None = None,
    ) -> np.ndarray:
        from model_api.models.result import DetectionResult
        from model_api.visualizer import BoundingBox, Flatten, Label
        from model_api.visualizer.scene import DetectionScene

        if not isinstance(predictions, DetectionResult):
            raise TypeError(f"Expected a DetectionResult, got {type(predictions)}.")
        image_pil = Image.fromarray(original_image)
        scale = _compute_scale(original_image)
        detection_scene = DetectionScene(
            image=image_pil,
            result=predictions,
            layout=Flatten(BoundingBox, Label),
            scale=scale,
        )
        # Replace the default palette with the project colors and rebuild the color-dependent
        # bounding boxes so the stream matches the project's label colors.
        if label_colors:
            detection_scene.color_per_label = _merge_project_colors(predictions.label_names, label_colors)
            detection_scene.bounding_box = detection_scene._to_bounding_box(
                detection_scene._get_bounding_boxes(predictions)
            )
        rendered = detection_scene.render()
        return np.array(rendered)


class InstanceSegmentationVisualizerCreator(VisualizerCreator):
    """Creator for instance segmentation visualizations."""

    def create_visualization(
        self,
        original_image: np.ndarray,
        predictions: "Result",
        label_colors: dict[str, str] | None = None,
    ) -> np.ndarray:
        from model_api.models.result import InstanceSegmentationResult
        from model_api.visualizer import Flatten, Label, Polygon
        from model_api.visualizer.scene import InstanceSegmentationScene

        if not isinstance(predictions, InstanceSegmentationResult):
            raise TypeError(f"Expected an InstanceSegmentationResult, got {type(predictions)}.")
        image_pil = Image.fromarray(original_image)
        scale = _compute_scale(original_image)
        segmentation_scene = InstanceSegmentationScene(
            image=image_pil,
            result=predictions,
            layout=Flatten(Polygon, Label),
            scale=scale,
        )
        # Replace the default palette with the project colors and rebuild the color-dependent
        # polygons and labels so the stream matches the project's label colors.
        if label_colors:
            segmentation_scene.color_per_label = _merge_project_colors(predictions.label_names, label_colors)
            segmentation_scene.polygon = segmentation_scene._to_polygon(segmentation_scene._get_polygons(predictions))
            segmentation_scene.label = segmentation_scene._to_label(segmentation_scene._get_labels(predictions))
        rendered = segmentation_scene.render()
        return np.array(rendered)


class VisualizationDispatcher(metaclass=Singleton):
    """Dispatcher for creating visualizations."""

    def __init__(self) -> None:
        from model_api.models.result import ClassificationResult, DetectionResult, InstanceSegmentationResult, Result

        self._creator_map: dict[type[Result], VisualizerCreator] = {
            DetectionResult: DetectionVisualizerCreator(),
            ClassificationResult: ClassificationVisualizerCreator(),
            InstanceSegmentationResult: InstanceSegmentationVisualizerCreator(),
        }

    def create_visualization(
        self,
        original_image: np.ndarray,
        predictions: "Result",
        label_colors: dict[str, str] | None = None,
    ) -> np.ndarray | None:
        if original_image.size == 0:
            raise ValueError("The image provided through the 'original_image' parameter cannot be empty.")

        creator = self._creator_map.get(type(predictions))
        if creator is not None:
            return creator.create_visualization(original_image, predictions, label_colors=label_colors)
        logger.error("Visualization for {} is not supported.", type(predictions))
        return None


class Visualizer:
    @staticmethod
    def overlay_predictions(
        original_image: np.ndarray,
        predictions: "Result",
        label_colors: dict[str, str] | None = None,
    ) -> np.ndarray:
        """Overlay predictions on the original image.

        Args:
            original_image: BGR/RGB numpy image.
            predictions: Model API prediction result.
            label_colors: Optional mapping of label name to hex color (e.g. ``"#RRGGBB"``) from the
                project definition, used so the inference stream colors match the project's labels.
        """
        try:
            visualization = VisualizationDispatcher().create_visualization(
                original_image, predictions, label_colors=label_colors
            )
            if visualization is None:
                return original_image
        except Exception:
            logger.exception("An error occurred while creating visualization, returning original image.")
            return original_image
        return visualization
