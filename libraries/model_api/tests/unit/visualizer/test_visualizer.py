"""Tests for visualizer."""

# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import numpy as np
import pytest
from model_api.models.result import (
    AnomalyResult,
)
from model_api.visualizer import Visualizer
from PIL import Image


def test_render(mock_image: Image, tmpdir: Path):
    """Test Visualizer.render()."""
    heatmap = np.ones(mock_image.size, dtype=np.uint8)
    heatmap *= 255

    mask = np.zeros(mock_image.size, dtype=np.uint8)
    mask[32:96, 32:96] = 255
    mask[40:80, 0:128] = 255

    anomaly_result = AnomalyResult(
        anomaly_map=heatmap,
        pred_boxes=np.array([[0, 0, 128, 128], [32, 32, 96, 96]]),
        pred_label="Anomaly",
        pred_mask=mask,
        pred_score=0.85,
    )

    visualizer = Visualizer()
    rendered_img = visualizer.render(mock_image, anomaly_result)

    assert isinstance(rendered_img, Image.Image)
    assert np.array(rendered_img).shape == np.array(mock_image).shape

    rendered_img_np = visualizer.render(np.array(mock_image), anomaly_result)

    assert isinstance(rendered_img_np, np.ndarray)
    assert rendered_img_np.shape == np.array(mock_image).shape


def test_show(mock_image: Image, monkeypatch):
    """Test Visualizer.show() with both PIL and numpy input."""
    heatmap = np.ones(mock_image.size, dtype=np.uint8) * 255
    anomaly_result = AnomalyResult(
        anomaly_map=heatmap,
        pred_boxes=None,
        pred_label="Anomaly",
        pred_mask=None,
        pred_score=0.85,
    )

    shown = []
    monkeypatch.setattr(Image.Image, "show", lambda self: shown.append(True))

    visualizer = Visualizer()
    # With PIL Image
    visualizer.show(mock_image, anomaly_result)
    assert len(shown) == 1

    # With numpy array (covers line 70-73)
    visualizer.show(np.array(mock_image), anomaly_result)
    assert len(shown) == 2


def test_save_with_numpy_input(mock_image: Image, tmpdir: Path):
    """Test Visualizer.save() with numpy input (covers line 77)."""
    heatmap = np.ones(mock_image.size, dtype=np.uint8) * 255
    anomaly_result = AnomalyResult(
        anomaly_map=heatmap,
        pred_boxes=None,
        pred_label="Anomaly",
        pred_mask=None,
        pred_score=0.85,
    )

    visualizer = Visualizer()
    visualizer.save(np.array(mock_image), anomaly_result, tmpdir / "numpy_save.jpg")
    assert Path(tmpdir / "numpy_save.jpg").exists()


def test_keypoint_scene_creation(mock_image: Image, tmpdir: Path):
    """Test KeypointScene creation via Visualizer (covers line 112)."""
    from model_api.models.result import DetectedKeypoints

    keypoint_result = DetectedKeypoints(
        keypoints=np.array([[50, 50], [70, 70]]),
        scores=np.array([0.95, 0.80]),
    )

    visualizer = Visualizer()
    rendered = visualizer.render(mock_image, keypoint_result)
    assert isinstance(rendered, Image.Image)

    visualizer.save(mock_image, keypoint_result, tmpdir / "keypoint_scene.jpg")
    assert Path(tmpdir / "keypoint_scene.jpg").exists()


# =============================================================================
# Grayscale Image Support Tests
# =============================================================================
# These tests verify Visualizer correctly handles grayscale inputs by converting
# them to RGB before rendering/showing/saving. This avoids mode mismatches in
# downstream PIL operations (e.g. PIL.Image.blend) that require matching modes.


class TestGrayscaleImageSupport:
    """Tests to confirm grayscale image handling issues in Visualizer.

    Root causes identified:
    1. Visualizer.show/save/render: Image.fromarray() preserves 'L' mode for grayscale
    2. Overlay.compute: PIL.Image.blend() requires both images to have same mode
    3. HStack._stitch: Creates RGB image and pastes grayscale onto it (mode mismatch)
    """

    @pytest.fixture
    def grayscale_pil_image(self) -> Image.Image:
        """Create a grayscale PIL Image (mode 'L')."""
        data = np.zeros((100, 100), dtype=np.uint8)
        data[25:75, 25:75] = 128  # Add some variation
        return Image.fromarray(data, mode="L")

    @pytest.fixture
    def grayscale_ndarray(self) -> np.ndarray:
        """Create a grayscale numpy array (2D, no channel dimension)."""
        data = np.zeros((100, 100), dtype=np.uint8)
        data[25:75, 25:75] = 128
        return data

    @pytest.fixture
    def grayscale_ndarray_explicit_channel(self) -> np.ndarray:
        """Create a grayscale numpy array with explicit single channel (H, W, 1)."""
        data = np.zeros((100, 100, 1), dtype=np.uint8)
        data[25:75, 25:75, 0] = 128
        return data

    def test_grayscale_pil_image_mode_preserved(self, grayscale_pil_image: Image.Image):
        """Confirm that grayscale PIL images have mode 'L'."""
        assert grayscale_pil_image.mode == "L", "Grayscale PIL image should have mode 'L'"

    def test_grayscale_ndarray_converts_to_mode_L(self, grayscale_ndarray: np.ndarray):
        """Confirm Image.fromarray() converts 2D array to mode 'L'.

        This is the root cause: when Visualizer receives a grayscale ndarray,
        Image.fromarray() creates an 'L' mode image, not 'RGB'.
        """
        image = Image.fromarray(grayscale_ndarray)
        assert image.mode == "L", "2D ndarray should convert to mode 'L'"

    def test_render_with_grayscale_pil_image(self, grayscale_pil_image: Image.Image):
        """Test Visualizer.render() with grayscale PIL Image.

        Expected behavior: the visualizer should convert grayscale input to RGB before
        any blending/stacking, so rendering should succeed and return an RGB image.
        """
        heatmap = np.ones((100, 100), dtype=np.uint8) * 255

        anomaly_result = AnomalyResult(
            anomaly_map=heatmap,
            pred_boxes=None,
            pred_label="Anomaly",
            pred_mask=None,
            pred_score=0.85,
        )

        visualizer = Visualizer()
        # This should fail or produce incorrect results due to mode mismatch
        rendered = visualizer.render(grayscale_pil_image, anomaly_result)

        # If we get here, check that the output is valid
        assert isinstance(rendered, Image.Image)
        # The rendered image should ideally be RGB for proper visualization
        assert rendered.mode == "RGB", f"Expected RGB output, got {rendered.mode}"

    def test_render_with_grayscale_ndarray(self, grayscale_ndarray: np.ndarray):
        """Test Visualizer.render() with grayscale numpy array (2D).

        Expected behavior: the visualizer converts grayscale input to RGB internally,
        so rendering should succeed and return an RGB (H, W, 3) output.
        """
        heatmap = np.ones((100, 100), dtype=np.uint8) * 255

        anomaly_result = AnomalyResult(
            anomaly_map=heatmap,
            pred_boxes=None,
            pred_label="Anomaly",
            pred_mask=None,
            pred_score=0.85,
        )

        visualizer = Visualizer()
        # This should fail due to grayscale handling
        rendered = visualizer.render(grayscale_ndarray, anomaly_result)

        assert isinstance(rendered, np.ndarray)
        # Output should be RGB (H, W, 3) for proper visualization
        assert len(rendered.shape) == 3, f"Expected 3D array, got shape {rendered.shape}"
        assert rendered.shape[2] == 3, f"Expected 3 channels, got {rendered.shape[2]}"

    def test_render_with_grayscale_ndarray_explicit_channel(
        self,
        grayscale_ndarray_explicit_channel: np.ndarray,
    ):
        """Test Visualizer.render() with grayscale ndarray having explicit channel (H, W, 1).

        This tests another edge case where the array has 3 dimensions but only 1 channel.
        """
        heatmap = np.ones((100, 100), dtype=np.uint8) * 255

        anomaly_result = AnomalyResult(
            anomaly_map=heatmap,
            pred_boxes=None,
            pred_label="Anomaly",
            pred_mask=None,
            pred_score=0.85,
        )

        visualizer = Visualizer()
        rendered = visualizer.render(grayscale_ndarray_explicit_channel, anomaly_result)

        assert isinstance(rendered, np.ndarray)
        assert len(rendered.shape) == 3, f"Expected 3D array, got shape {rendered.shape}"

    def test_show_with_grayscale_pil_image(
        self,
        grayscale_pil_image: Image.Image,
        monkeypatch,
    ):
        """Test Visualizer.show() with grayscale PIL Image."""
        heatmap = np.ones((100, 100), dtype=np.uint8) * 255
        anomaly_result = AnomalyResult(
            anomaly_map=heatmap,
            pred_boxes=None,
            pred_label="Anomaly",
            pred_mask=None,
            pred_score=0.85,
        )

        shown = []
        monkeypatch.setattr(Image.Image, "show", lambda self: shown.append(self.mode))

        visualizer = Visualizer()
        visualizer.show(grayscale_pil_image, anomaly_result)

        assert len(shown) == 1
        # The shown image should be RGB for proper color visualization
        assert shown[0] == "RGB", f"Expected RGB mode for display, got {shown[0]}"

    def test_show_with_grayscale_ndarray(self, grayscale_ndarray: np.ndarray, monkeypatch):
        """Test Visualizer.show() with grayscale numpy array."""
        heatmap = np.ones((100, 100), dtype=np.uint8) * 255
        anomaly_result = AnomalyResult(
            anomaly_map=heatmap,
            pred_boxes=None,
            pred_label="Anomaly",
            pred_mask=None,
            pred_score=0.85,
        )

        shown = []
        monkeypatch.setattr(Image.Image, "show", lambda self: shown.append(self.mode))

        visualizer = Visualizer()
        visualizer.show(grayscale_ndarray, anomaly_result)

        assert len(shown) == 1
        assert shown[0] == "RGB", f"Expected RGB mode for display, got {shown[0]}"

    def test_save_with_grayscale_pil_image(
        self,
        grayscale_pil_image: Image.Image,
        tmpdir: Path,
    ):
        """Test Visualizer.save() with grayscale PIL Image."""
        heatmap = np.ones((100, 100), dtype=np.uint8) * 255
        anomaly_result = AnomalyResult(
            anomaly_map=heatmap,
            pred_boxes=None,
            pred_label="Anomaly",
            pred_mask=None,
            pred_score=0.85,
        )

        visualizer = Visualizer()
        save_path = tmpdir / "grayscale_pil.png"
        visualizer.save(grayscale_pil_image, anomaly_result, save_path)

        assert save_path.exists()
        # Verify the saved image is RGB
        saved_image = Image.open(save_path)
        assert saved_image.mode == "RGB", f"Expected RGB saved image, got {saved_image.mode}"

    def test_save_with_grayscale_ndarray(self, grayscale_ndarray: np.ndarray, tmpdir: Path):
        """Test Visualizer.save() with grayscale numpy array."""
        heatmap = np.ones((100, 100), dtype=np.uint8) * 255
        anomaly_result = AnomalyResult(
            anomaly_map=heatmap,
            pred_boxes=None,
            pred_label="Anomaly",
            pred_mask=None,
            pred_score=0.85,
        )

        visualizer = Visualizer()
        save_path = tmpdir / "grayscale_ndarray.png"
        visualizer.save(grayscale_ndarray, anomaly_result, save_path)

        assert save_path.exists()
        saved_image = Image.open(save_path)
        assert saved_image.mode == "RGB", f"Expected RGB saved image, got {saved_image.mode}"


class TestGrayscaleOverlayBlending:
    """Tests to confirm the PIL.Image.blend() mode mismatch issue.

    Root cause: Overlay.compute() uses PIL.Image.blend() which requires
    both images to have the same mode. When base image is 'L' (grayscale)
    and overlay is 'RGB', the blend operation fails.
    """

    def test_blend_mode_mismatch_grayscale_base_rgb_overlay(self):
        """Demonstrate PIL.Image.blend() fails with mode mismatch.

        This is the fundamental issue: blending grayscale with RGB fails.
        """
        grayscale_image = Image.new("L", (100, 100), color=128)
        rgb_overlay = Image.new("RGB", (100, 100), color=(255, 0, 0))

        # PIL.Image.blend requires same mode - this should raise ValueError
        with pytest.raises(ValueError, match="images do not match"):
            Image.blend(grayscale_image, rgb_overlay, alpha=0.5)

    def test_blend_mode_mismatch_rgb_base_grayscale_overlay(self):
        """Demonstrate PIL.Image.blend() fails with reversed mode mismatch."""
        rgb_image = Image.new("RGB", (100, 100), color=(0, 255, 0))
        grayscale_overlay = Image.new("L", (100, 100), color=128)

        with pytest.raises(ValueError, match="images do not match"):
            Image.blend(rgb_image, grayscale_overlay, alpha=0.5)

    def test_overlay_compute_with_grayscale_base(self):
        """Test Overlay.compute() with grayscale base image.

        Overlay.compute() uses PIL.Image.blend() which requires both images to have
        the same mode. When base is grayscale ('L') and overlay is RGB, it fails.

        Note: The fix is in Visualizer._to_rgb() which converts images to RGB before
        they reach the Overlay layer. This test documents the underlying limitation.
        """
        from model_api.visualizer.primitive import Overlay

        grayscale_base = Image.new("L", (100, 100), color=128)
        # Create RGB overlay data (common case: heatmaps are often RGB)
        rgb_overlay_data = np.zeros((100, 100, 3), dtype=np.uint8)
        rgb_overlay_data[:, :, 0] = 255  # Red channel

        overlay = Overlay(rgb_overlay_data, opacity=0.5)

        # Overlay.compute() fails with mode mismatch - this is expected behavior
        # The fix is applied at the Visualizer layer, not here
        with pytest.raises(ValueError, match="images do not match"):
            overlay.compute(grayscale_base)

    def test_overlay_compute_with_grayscale_overlay_on_rgb_base(self):
        """Test Overlay.compute() with grayscale overlay on RGB base.

        When overlay is grayscale and base is RGB, PIL.Image.blend() fails.

        Note: The fix is in Visualizer._to_rgb() which converts images to RGB before
        they reach the Overlay layer. This test documents the underlying limitation.
        """
        from model_api.visualizer.primitive import Overlay

        rgb_base = Image.new("RGB", (100, 100), color=(0, 255, 0))
        # Create grayscale overlay (2D array)
        grayscale_overlay_data = np.ones((100, 100), dtype=np.uint8) * 128

        overlay = Overlay(grayscale_overlay_data, opacity=0.5)

        # Overlay.compute() fails with mode mismatch - this is expected behavior
        with pytest.raises(ValueError, match="images do not match"):
            overlay.compute(rgb_base)


class TestGrayscaleHStackLayout:
    """Tests HStack._stitch() behavior with grayscale inputs.

    HStack._stitch() always creates an RGB canvas and pastes source images onto it.
    This test verifies that pasting grayscale ('L') images results in an RGB image
    with grayscale values replicated across channels.
    """

    def test_hstack_stitch_grayscale_images(self):
        """Test HStack._stitch() with grayscale images.

        The _stitch method creates an RGB canvas and pastes images.
        Grayscale images pasted onto RGB may produce incorrect results.
        """
        from model_api.visualizer.layout import HStack

        gray1 = Image.new("L", (50, 100), color=64)
        gray2 = Image.new("L", (50, 100), color=192)

        result = HStack._stitch(gray1, gray2)  # noqa: SLF001

        assert isinstance(result, Image.Image)
        assert result.mode == "RGB", f"Expected RGB result, got {result.mode}"
        assert result.size == (100, 100)

        # Verify the grayscale values are preserved correctly in RGB
        result_array = np.array(result)
        # Left half should be (64, 64, 64) in RGB
        assert np.allclose(
            result_array[50, 10, :],
            [64, 64, 64],
        ), f"Expected [64,64,64], got {result_array[50, 10, :]}"
        # Right half should be (192, 192, 192) in RGB
        assert np.allclose(
            result_array[50, 60, :],
            [192, 192, 192],
        ), f"Expected [192,192,192], got {result_array[50, 60, :]}"

    def test_hstack_stitch_mixed_modes(self):
        """Test HStack._stitch() with mixed grayscale and RGB images."""
        from model_api.visualizer.layout import HStack

        gray_image = Image.new("L", (50, 100), color=128)
        rgb_image = Image.new("RGB", (50, 100), color=(255, 0, 0))

        result = HStack._stitch(gray_image, rgb_image)  # noqa: SLF001

        assert isinstance(result, Image.Image)
        assert result.mode == "RGB"
        assert result.size == (100, 100)


class Test16BitImageSupport:
    """Tests for 16-bit image handling in Visualizer.

    16-bit images require special handling:
    1. 16-bit grayscale arrays (uint16) need scaling to 8-bit before conversion
    2. 16-bit RGB arrays fail with Image.fromarray() - need manual scaling
    3. PIL 'I;16' mode images need proper scaling during RGB conversion
    """

    @pytest.fixture
    def grayscale_16bit_ndarray(self) -> np.ndarray:
        """Create a 16-bit grayscale numpy array."""
        data = np.zeros((100, 100), dtype=np.uint16)
        data[25:75, 25:75] = 32768  # Mid-value for 16-bit (should be ~128 in 8-bit)
        return data

    @pytest.fixture
    def rgb_16bit_ndarray(self) -> np.ndarray:
        """Create a 16-bit RGB numpy array."""
        data = np.zeros((100, 100, 3), dtype=np.uint16)
        data[25:75, 25:75, 0] = 32768  # Red channel at mid-value
        return data

    @pytest.fixture
    def grayscale_16bit_pil(self) -> Image.Image:
        """Create a 16-bit grayscale PIL Image (mode 'I;16')."""
        data = np.zeros((100, 100), dtype=np.uint16)
        data[25:75, 25:75] = 32768
        return Image.fromarray(data)

    @pytest.fixture
    def float32_ndarray(self) -> np.ndarray:
        """Create a float32 numpy array in [0, 1] range."""
        data = np.zeros((100, 100, 3), dtype=np.float32)
        data[25:75, 25:75, 0] = 0.5  # Red channel at mid-value
        return data

    def test_16bit_grayscale_pil_mode(self, grayscale_16bit_pil: Image.Image):
        """Confirm 16-bit grayscale PIL image has mode 'I;16'."""
        assert grayscale_16bit_pil.mode == "I;16"

    def test_render_with_16bit_grayscale_ndarray(self, grayscale_16bit_ndarray: np.ndarray):
        """Test Visualizer.render() with 16-bit grayscale numpy array.

        The 16-bit values should be scaled to 8-bit (32768 -> ~128).
        """
        heatmap = np.ones((100, 100), dtype=np.uint8) * 255

        anomaly_result = AnomalyResult(
            anomaly_map=heatmap,
            pred_boxes=None,
            pred_label="Anomaly",
            pred_mask=None,
            pred_score=0.85,
        )

        visualizer = Visualizer()
        rendered = visualizer.render(grayscale_16bit_ndarray, anomaly_result)

        assert isinstance(rendered, np.ndarray)
        assert rendered.dtype == np.uint8
        assert len(rendered.shape) == 3
        assert rendered.shape[2] == 3

    def test_render_with_16bit_rgb_ndarray(self, rgb_16bit_ndarray: np.ndarray):
        """Test Visualizer.render() with 16-bit RGB numpy array.

        The 16-bit values should be scaled to 8-bit.
        """
        heatmap = np.ones((100, 100), dtype=np.uint8) * 255

        anomaly_result = AnomalyResult(
            anomaly_map=heatmap,
            pred_boxes=None,
            pred_label="Anomaly",
            pred_mask=None,
            pred_score=0.85,
        )

        visualizer = Visualizer()
        rendered = visualizer.render(rgb_16bit_ndarray, anomaly_result)

        assert isinstance(rendered, np.ndarray)
        assert rendered.dtype == np.uint8
        assert rendered.shape == (100, 100, 3)

    def test_render_with_16bit_grayscale_pil(self, grayscale_16bit_pil: Image.Image):
        """Test Visualizer.render() with 16-bit PIL Image (mode 'I;16').

        The 16-bit values should be scaled properly during RGB conversion.
        """
        heatmap = np.ones((100, 100), dtype=np.uint8) * 255

        anomaly_result = AnomalyResult(
            anomaly_map=heatmap,
            pred_boxes=None,
            pred_label="Anomaly",
            pred_mask=None,
            pred_score=0.85,
        )

        visualizer = Visualizer()
        rendered = visualizer.render(grayscale_16bit_pil, anomaly_result)

        assert isinstance(rendered, Image.Image)
        assert rendered.mode == "RGB"

    def test_render_with_float32_ndarray(self, float32_ndarray: np.ndarray):
        """Test Visualizer.render() with float32 numpy array in [0, 1] range.

        Float values should be scaled to 8-bit (0.5 -> 127/128).
        """
        heatmap = np.ones((100, 100), dtype=np.uint8) * 255

        anomaly_result = AnomalyResult(
            anomaly_map=heatmap,
            pred_boxes=None,
            pred_label="Anomaly",
            pred_mask=None,
            pred_score=0.85,
        )

        visualizer = Visualizer()
        rendered = visualizer.render(float32_ndarray, anomaly_result)

        assert isinstance(rendered, np.ndarray)
        assert rendered.dtype == np.uint8
        assert rendered.shape == (100, 100, 3)

    def test_16bit_scaling_preserves_relative_values(self):
        """Verify 16-bit to 8-bit scaling preserves relative intensity values."""
        # Create image with known values
        data = np.array([[0, 32768, 65535]], dtype=np.uint16)  # min, mid, max

        visualizer = Visualizer()
        rgb = visualizer._to_rgb(data)  # noqa: SLF001
        rgb_array = np.array(rgb)

        # After scaling: 0->0, 32768->128, 65535->255
        assert rgb_array[0, 0, 0] == 0, f"Expected 0, got {rgb_array[0, 0, 0]}"
        assert rgb_array[0, 1, 0] == 128, f"Expected 128, got {rgb_array[0, 1, 0]}"
        assert rgb_array[0, 2, 0] == 255, f"Expected 255, got {rgb_array[0, 2, 0]}"

    def test_16bit_pil_scaling_preserves_relative_values(self):
        """Verify 16-bit PIL image scaling preserves relative intensity values."""
        data = np.array([[0, 32768, 65535]], dtype=np.uint16)
        pil_16bit = Image.fromarray(data)
        assert pil_16bit.mode == "I;16"

        visualizer = Visualizer()
        rgb = visualizer._to_rgb(pil_16bit)  # noqa: SLF001
        rgb_array = np.array(rgb)

        # After scaling: 0->0, 32768->128, 65535->255
        assert rgb_array[0, 0, 0] == 0, f"Expected 0, got {rgb_array[0, 0, 0]}"
        assert rgb_array[0, 1, 0] == 128, f"Expected 128, got {rgb_array[0, 1, 0]}"
        assert rgb_array[0, 2, 0] == 255, f"Expected 255, got {rgb_array[0, 2, 0]}"
