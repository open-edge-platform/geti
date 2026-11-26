"""Tests for the optional label colour mapping."""

# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import numpy as np
import pytest
from model_api.models.result import (
    AnomalyResult,
    ClassificationResult,
    DetectionResult,
    InstanceSegmentationResult,
)
from model_api.models.result.classification import Label
from model_api.visualizer import Visualizer
from model_api.visualizer.primitive import Polygon
from model_api.visualizer.scene.anomaly import AnomalyScene
from model_api.visualizer.scene.classification import ClassificationScene
from model_api.visualizer.scene.detection import DetectionScene
from model_api.visualizer.scene.segmentation.instance_segmentation import InstanceSegmentationScene
from model_api.visualizer.utils import COLOR_PALETTE, get_label_color_mapping, to_rgb, validate_label_colors
from PIL import Image


@pytest.fixture
def detection_result() -> DetectionResult:
    return DetectionResult(
        bboxes=np.array([[0, 0, 64, 64], [32, 32, 96, 96]]),
        labels=np.array([0, 1]),
        label_names=["car", "person"],
        scores=np.array([0.85, 0.75]),
        saliency_map=None,
    )


@pytest.fixture
def instance_segmentation_result() -> InstanceSegmentationResult:
    return InstanceSegmentationResult(
        bboxes=np.array([[0, 0, 64, 64], [32, 32, 96, 96]]),
        labels=np.array([0, 1]),
        masks=np.array([
            np.ones((100, 100), dtype=np.uint8),
            np.ones((100, 100), dtype=np.uint8),
        ]),
        scores=np.array([0.85, 0.75]),
        label_names=["car", "person"],
        saliency_map=None,
        feature_vector=np.array([1, 2, 3]),
    )


@pytest.fixture
def classification_result() -> ClassificationResult:
    return ClassificationResult(
        top_labels=[
            Label(name="cat", confidence=0.95),
            Label(name="dog", confidence=0.90),
        ],
        saliency_map=None,
    )


@pytest.fixture
def anomaly_result(mock_image: Image) -> AnomalyResult:
    mask = np.zeros(mock_image.size, dtype=np.uint8)
    mask[32:96, 32:96] = 255
    return AnomalyResult(
        anomaly_map=None,
        pred_boxes=np.array([[0, 0, 64, 64]]),
        pred_label="Anomaly",
        pred_mask=mask,
        pred_score=0.85,
    )


class TestValidateLabelColors:
    """Tests for validate_label_colors()."""

    def test_none_returns_empty_mapping(self):
        assert validate_label_colors(None) == {}

    @pytest.mark.parametrize("color", ["#FF0000", "red", (12, 34, 56)])
    def test_accepts_valid_colors(self, color):
        assert validate_label_colors({"car": color}) == {"car": color}

    def test_returns_a_copy(self):
        source = {"car": "#FF0000"}
        validated = validate_label_colors(source)
        validated["person"] = "#00FF00"
        assert source == {"car": "#FF0000"}

    @pytest.mark.parametrize(
        "color",
        [
            "not-a-colour",
            (1, 2),
            (1, 2, 3, 4),
            (1, 2, 300),
            (1, 2, -1),
            (1, 2, "3"),
            123,
            None,
        ],
    )
    def test_rejects_invalid_colors(self, color):
        with pytest.raises(ValueError, match="car"):
            validate_label_colors({"car": color})


class TestGetLabelColorMapping:
    """Tests for get_label_color_mapping()."""

    def test_without_overrides_uses_palette(self):
        mapping = get_label_color_mapping(["person", "car"])
        assert mapping == {"car": COLOR_PALETTE[0], "person": COLOR_PALETTE[1]}

    def test_overrides_replace_palette_colors(self):
        mapping = get_label_color_mapping(["person", "car"], overrides={"car": "#123456"})
        assert mapping["car"] == "#123456"
        assert mapping["person"] == COLOR_PALETTE[1]

    def test_overrides_accept_rgb_tuples(self):
        mapping = get_label_color_mapping(["car"], overrides={"car": (1, 2, 3)})
        assert mapping["car"] == (1, 2, 3)

    def test_unknown_override_keys_are_ignored(self):
        mapping = get_label_color_mapping(["car"], overrides={"bicycle": "#123456"})
        assert mapping == {"car": COLOR_PALETTE[0]}

    def test_none_overrides_behave_like_no_overrides(self):
        assert get_label_color_mapping(["car"], overrides=None) == get_label_color_mapping(["car"])


class TestVisualizerLabelColors:
    """Tests for the Visualizer label_colors argument."""

    def test_defaults_to_empty_mapping(self):
        assert Visualizer().label_colors == {}

    def test_validates_eagerly(self):
        with pytest.raises(ValueError, match="car"):
            Visualizer(label_colors={"car": "not-a-colour"})

    def test_forwards_mapping_to_detection_scene(self, mock_image: Image, detection_result: DetectionResult):
        visualizer = Visualizer(label_colors={"car": "#123456"})
        scene = visualizer._scene_from_result(mock_image, detection_result)  # noqa: SLF001
        assert isinstance(scene, DetectionScene)
        assert scene.color_per_label["car"] == "#123456"

    def test_renders_with_mapping(self, mock_image: Image, detection_result: DetectionResult):
        visualizer = Visualizer(label_colors={"car": "#123456"})
        assert isinstance(visualizer.render(mock_image, detection_result), Image.Image)


class TestDetectionSceneColors:
    """Tests for label colours in the detection scene."""

    def test_mapped_label_uses_custom_color(self, mock_image: Image, detection_result: DetectionResult):
        scene = DetectionScene(mock_image, detection_result, label_colors={"car": "#123456"})
        assert scene.bounding_box is not None
        assert scene.color_per_label["car"] == "#123456"
        assert scene.bounding_box[0].color == "#123456"

    def test_unmapped_label_keeps_palette_color(self, mock_image: Image, detection_result: DetectionResult):
        scene = DetectionScene(mock_image, detection_result, label_colors={"car": "#123456"})
        assert scene.bounding_box is not None
        assert scene.color_per_label["person"] == COLOR_PALETTE[1]
        assert scene.bounding_box[1].color == COLOR_PALETTE[1]

    def test_without_mapping_uses_palette(self, mock_image: Image, detection_result: DetectionResult):
        scene = DetectionScene(mock_image, detection_result)
        assert scene.color_per_label == {"car": COLOR_PALETTE[0], "person": COLOR_PALETTE[1]}


class TestInstanceSegmentationSceneColors:
    """Tests for label colours in the instance segmentation scene."""

    def test_polygons_use_custom_color(
        self,
        mock_image: Image,
        instance_segmentation_result: InstanceSegmentationResult,
    ):
        scene = InstanceSegmentationScene(
            mock_image,
            instance_segmentation_result,
            label_colors={"car": "#123456"},
        )
        assert scene.polygon is not None
        assert scene.polygon[0].color == "#123456"

    def test_label_chips_use_custom_color(
        self,
        mock_image: Image,
        instance_segmentation_result: InstanceSegmentationResult,
    ):
        scene = InstanceSegmentationScene(
            mock_image,
            instance_segmentation_result,
            label_colors={"car": "#123456"},
        )
        assert scene.label is not None
        colors = {label.label: label.bg_color for label in scene.label}
        assert colors["car"] == "#123456"
        assert colors["person"] == COLOR_PALETTE[1]

    def test_bounding_boxes_use_custom_color(
        self,
        mock_image: Image,
        instance_segmentation_result: InstanceSegmentationResult,
    ):
        scene = InstanceSegmentationScene(
            mock_image,
            instance_segmentation_result,
            label_colors={"car": "#123456"},
        )
        assert scene._get_bounding_boxes(instance_segmentation_result)[0].color == "#123456"  # noqa: SLF001


class TestClassificationSceneColors:
    """Tests for label colours in the classification scene."""

    def test_mapped_label_uses_custom_background(
        self,
        mock_image: Image,
        classification_result: ClassificationResult,
    ):
        scene = ClassificationScene(mock_image, classification_result, label_colors={"cat": "#123456"})
        assert scene.label is not None
        assert scene.label[0].bg_color == "#123456"

    def test_unmapped_label_keeps_default_background(
        self,
        mock_image: Image,
        classification_result: ClassificationResult,
    ):
        scene = ClassificationScene(mock_image, classification_result, label_colors={"cat": "#123456"})
        assert scene.label is not None
        assert scene.label[1].bg_color == "yellow"

    def test_without_mapping_keeps_default_background(
        self,
        mock_image: Image,
        classification_result: ClassificationResult,
    ):
        scene = ClassificationScene(mock_image, classification_result)
        assert scene.label is not None
        assert [label.bg_color for label in scene.label] == ["yellow", "yellow"]


class TestAnomalySceneColors:
    """Tests for label colours in the anomaly scene."""

    def test_mapped_label_colors_primitives(self, mock_image: Image, anomaly_result: AnomalyResult):
        scene = AnomalyScene(mock_image, anomaly_result, label_colors={"Anomaly": "#123456"})
        assert scene.label is not None
        assert scene.bounding_box is not None
        assert scene.polygon is not None
        assert scene.label[0].bg_color == "#123456"
        assert scene.bounding_box[0].color == "#123456"
        assert scene.polygon[0].color == "#123456"

    def test_unmapped_label_keeps_defaults(self, mock_image: Image, anomaly_result: AnomalyResult):
        scene = AnomalyScene(mock_image, anomaly_result, label_colors={"Normal": "#123456"})
        assert scene.label is not None
        assert scene.bounding_box is not None
        assert scene.polygon is not None
        assert scene.label[0].bg_color == "yellow"
        assert scene.bounding_box[0].color == "blue"
        assert scene.polygon[0].color == "blue"

    def test_without_mapping_keeps_defaults(self, mock_image: Image, anomaly_result: AnomalyResult):
        scene = AnomalyScene(mock_image, anomaly_result)
        assert scene.label is not None
        assert scene.bounding_box is not None
        assert scene.polygon is not None
        assert scene.label[0].bg_color == "yellow"
        assert scene.bounding_box[0].color == "blue"
        assert scene.polygon[0].color == "blue"

    def test_missing_pred_label_is_ignored(self, mock_image: Image):
        result = AnomalyResult(
            anomaly_map=None,
            pred_boxes=np.array([[0, 0, 64, 64]]),
            pred_label=None,
            pred_mask=np.zeros((100, 100), dtype=np.uint8),
            pred_score=None,
        )
        scene = AnomalyScene(mock_image, result, label_colors={"Anomaly": "#123456"})
        assert scene.bounding_box is not None
        assert scene.label == []
        assert scene.bounding_box[0].color == "blue"


class TestRgbTupleColors:
    """Tuple colours must render as well as string colours.

    Regression test: Polygon used PIL's ImageColor.getrgb(), which only accepts
    strings, so RGB tuples raised "'tuple' object has no attribute 'lower'" for any
    result that draws polygons (e.g. MaskRCNN instance segmentation).
    """

    def test_polygon_primitive_accepts_rgb_tuple(self, mock_image: Image):
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[10:90, 10:90] = 1
        polygon = Polygon(mask=mask, color=(18, 52, 86))
        assert isinstance(polygon.compute(mock_image.copy()), Image.Image)

    def test_polygon_primitive_tuple_matches_hex(self, mock_image: Image):
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[10:90, 10:90] = 1
        from_tuple = Polygon(mask=mask, color=(18, 52, 86)).compute(mock_image.copy())
        from_hex = Polygon(mask=mask, color="#123456").compute(mock_image.copy())
        assert from_tuple.tobytes() == from_hex.tobytes()

    def test_instance_segmentation_renders_with_rgb_tuple(
        self,
        mock_image: Image,
        instance_segmentation_result: InstanceSegmentationResult,
    ):
        visualizer = Visualizer(label_colors={"car": (18, 52, 86)})
        assert isinstance(visualizer.render(mock_image, instance_segmentation_result), Image.Image)

    def test_anomaly_renders_with_rgb_tuple(self, mock_image: Image, anomaly_result: AnomalyResult):
        visualizer = Visualizer(label_colors={"Anomaly": (18, 52, 86)})
        assert isinstance(visualizer.render(mock_image, anomaly_result), Image.Image)

    def test_detection_renders_with_rgb_tuple(self, mock_image: Image, detection_result: DetectionResult):
        visualizer = Visualizer(label_colors={"car": (18, 52, 86)})
        assert isinstance(visualizer.render(mock_image, detection_result), Image.Image)

    def test_classification_renders_with_rgb_tuple(
        self,
        mock_image: Image,
        classification_result: ClassificationResult,
    ):
        visualizer = Visualizer(label_colors={"cat": (18, 52, 86)})
        assert isinstance(visualizer.render(mock_image, classification_result), Image.Image)

    def test_tuple_and_hex_render_identically(
        self,
        mock_image: Image,
        instance_segmentation_result: InstanceSegmentationResult,
    ):
        from_tuple = Visualizer(label_colors={"car": (18, 52, 86)}).render(
            mock_image.copy(),
            instance_segmentation_result,
        )
        from_hex = Visualizer(label_colors={"car": "#123456"}).render(
            mock_image.copy(),
            instance_segmentation_result,
        )
        assert from_tuple.tobytes() == from_hex.tobytes()


class TestToRgb:
    """Tests for to_rgb()."""

    @pytest.mark.parametrize(
        ("color", "expected"),
        [
            ("#123456", (18, 52, 86)),
            ("red", (255, 0, 0)),
            ((18, 52, 86), (18, 52, 86)),
        ],
    )
    def test_normalizes_colors(self, color, expected):
        assert to_rgb(color) == expected


class TestRenderedOutput:
    """Regression tests on the rendered images."""

    def test_empty_mapping_renders_like_no_mapping(self, mock_image: Image, detection_result: DetectionResult):
        default = Visualizer().render(mock_image.copy(), detection_result)
        empty = Visualizer(label_colors={}).render(mock_image.copy(), detection_result)
        assert default.tobytes() == empty.tobytes()

    def test_mapping_changes_rendered_pixels(self, mock_image: Image, detection_result: DetectionResult):
        default = Visualizer().render(mock_image.copy(), detection_result)
        custom = Visualizer(label_colors={"car": "#123456"}).render(mock_image.copy(), detection_result)
        assert default.tobytes() != custom.tobytes()
