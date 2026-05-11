"""Tests for auto_scale visualizer feature."""

# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import numpy as np
import pytest
from model_api.models.result import (
    ClassificationResult,
    DetectionResult,
    InstanceSegmentationResult,
)
from model_api.models.result.classification import Label as ResultLabel
from model_api.visualizer import Visualizer
from model_api.visualizer.defaults import SCALE_BASELINE
from PIL import Image


class TestComputeScaleFactor:
    """Test the compute_scale_factor staticmethod."""

    def test_below_720p_returns_1(self):
        """Images at or below 720p should return scale factor 1.0."""
        image = Image.new("RGB", (640, 480))
        assert Visualizer.compute_scale_factor(image) == 1.0

    def test_exactly_720p_returns_1(self):
        image = Image.new("RGB", (1280, 720))
        assert Visualizer.compute_scale_factor(image) == 1.0

    def test_1080p(self):
        image = Image.new("RGB", (1920, 1080))
        assert Visualizer.compute_scale_factor(image) == pytest.approx(1920 / SCALE_BASELINE, abs=1e-6)

    def test_4032x2268(self):
        """The original motivating use-case: a phone camera photo."""
        image = Image.new("RGB", (4032, 2268))
        assert Visualizer.compute_scale_factor(image) == pytest.approx(4032 / SCALE_BASELINE, abs=1e-6)

    def test_4k(self):
        image = Image.new("RGB", (3840, 2160))
        assert Visualizer.compute_scale_factor(image) == pytest.approx(3840 / SCALE_BASELINE, abs=1e-6)

    def test_8k(self):
        image = Image.new("RGB", (7680, 4320))
        assert Visualizer.compute_scale_factor(image) == pytest.approx(7680 / SCALE_BASELINE, abs=1e-6)

    def test_portrait_uses_longer_edge(self):
        """Portrait orientation: height > width."""
        image = Image.new("RGB", (1080, 1920))
        assert Visualizer.compute_scale_factor(image) == pytest.approx(1920 / SCALE_BASELINE, abs=1e-6)

    def test_small_image(self):
        image = Image.new("RGB", (100, 100))
        assert Visualizer.compute_scale_factor(image) == 1.0


class TestVisualizerAutoScale:
    """Test that auto_scale=False preserves old behaviour and auto_scale=True scales."""

    @pytest.fixture()
    def small_image(self):
        return Image.new("RGB", (640, 480), color=(128, 128, 128))

    @pytest.fixture()
    def large_image(self):
        return Image.new("RGB", (3840, 2160), color=(128, 128, 128))

    @pytest.fixture()
    def detection_result_small(self):
        return DetectionResult(
            bboxes=np.array([[10, 10, 200, 200]]),
            labels=np.array([0]),
            label_names=["person"],
            scores=np.array([0.95]),
            saliency_map=np.array([]),
        )

    @pytest.fixture()
    def detection_result_large(self):
        return DetectionResult(
            bboxes=np.array([[100, 100, 2000, 1500]]),
            labels=np.array([0]),
            label_names=["person"],
            scores=np.array([0.95]),
            saliency_map=np.array([]),
        )

    def test_default_auto_scale_is_true(self):
        vis = Visualizer()
        assert vis.auto_scale is True

    def test_auto_scale_false_no_scaling(self, small_image, detection_result_small):
        """auto_scale=False should work exactly like before."""
        vis = Visualizer(auto_scale=False)
        rendered = vis.render(small_image, detection_result_small)
        assert isinstance(rendered, Image.Image)
        assert rendered.size == small_image.size

    def test_auto_scale_true_small_image_no_scaling(self, small_image, detection_result_small):
        """auto_scale=True on a <=720p image should produce same results as False."""
        vis_off = Visualizer(auto_scale=False)
        vis_on = Visualizer(auto_scale=True)
        rendered_off = vis_off.render(small_image.copy(), detection_result_small)
        rendered_on = vis_on.render(small_image.copy(), detection_result_small)
        np.testing.assert_array_equal(np.array(rendered_off), np.array(rendered_on))

    def test_auto_scale_true_large_image_differs(self, large_image, detection_result_large):
        """auto_scale=True on a large image should produce visually different output."""
        vis_off = Visualizer(auto_scale=False)
        vis_on = Visualizer(auto_scale=True)
        rendered_off = vis_off.render(large_image.copy(), detection_result_large)
        rendered_on = vis_on.render(large_image.copy(), detection_result_large)
        assert not np.array_equal(np.array(rendered_off), np.array(rendered_on))

    def test_auto_scale_render_returns_numpy_when_given_numpy(self, large_image, detection_result_large):
        vis = Visualizer(auto_scale=True)
        rendered = vis.render(np.array(large_image), detection_result_large)
        assert isinstance(rendered, np.ndarray)
        assert rendered.shape == np.array(large_image).shape

    def test_auto_scale_save(self, large_image, detection_result_large, tmp_path):
        vis = Visualizer(auto_scale=True)
        path = tmp_path / "test_auto_scale.jpg"
        vis.save(large_image, detection_result_large, path)
        assert path.exists()

    def test_auto_scale_classification(self, large_image, tmp_path):
        result = ClassificationResult(
            top_labels=[
                ResultLabel(name="cat", confidence=0.95),
                ResultLabel(name="dog", confidence=0.90),
            ],
            saliency_map=np.array([]),
        )
        vis = Visualizer(auto_scale=True)
        path = tmp_path / "test_cls_auto_scale.jpg"
        vis.save(large_image, result, path)
        assert path.exists()

    def test_auto_scale_instance_segmentation(self, large_image, tmp_path):
        result = InstanceSegmentationResult(
            bboxes=np.array([[100, 100, 2000, 1500]]),
            labels=np.array([0]),
            masks=np.array([np.ones((1500, 2000), dtype=np.uint8)]),
            scores=np.array([0.85]),
            label_names=["person"],
            saliency_map=None,
            feature_vector=np.array([1, 2, 3]),
        )
        vis = Visualizer(auto_scale=True)
        path = tmp_path / "test_iseg_auto_scale.jpg"
        vis.save(large_image, result, path)
        assert path.exists()


class TestSceneScalePropagation:
    """Verify that scale factors reach the primitives inside scenes."""

    def test_detection_scene_bounding_box_width_scales(self):
        """BoundingBox outline_width should increase with scale."""
        from model_api.visualizer.scene.detection import DetectionScene

        image = Image.new("RGB", (3840, 2160))
        result = DetectionResult(
            bboxes=np.array([[100, 100, 2000, 1500]]),
            labels=np.array([0]),
            label_names=["person"],
            scores=np.array([0.95]),
            saliency_map=np.array([]),
        )
        scene = DetectionScene(image, result, scale=3.0)
        boxes = scene.bounding_box
        assert boxes is not None
        assert boxes[0].outline_width == 6
        assert boxes[0].font_size == 48

    def test_detection_scene_scale_1_preserves_defaults(self):
        from model_api.visualizer.scene.detection import DetectionScene

        image = Image.new("RGB", (1280, 720))
        result = DetectionResult(
            bboxes=np.array([[10, 10, 200, 200]]),
            labels=np.array([0]),
            label_names=["person"],
            scores=np.array([0.95]),
            saliency_map=np.array([]),
        )
        scene = DetectionScene(image, result, scale=1.0)
        boxes = scene.bounding_box
        assert boxes is not None
        assert boxes[0].outline_width == 2
        assert boxes[0].font_size == 16
