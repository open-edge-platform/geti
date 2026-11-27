#
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

"""Unit tests for visual_prompting helpers and wrappers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from model_api.models import ZSLVisualPromptingResult
from model_api.models.visual_prompting import (
    Prompt,
    SAMLearnableVisualPrompter,
    SAMVisualPrompter,
    VisualPromptingFeatures,
    _decide_masks,
    _generate_masked_features,
    _get_prepadded_size,
    _get_prompt_candidates,
    _inspect_overlapping_areas,
    _pad_to_square,
    _point_selection,
    _polygon_to_mask,
    _resize_to_original_shape,
    _topk_numpy,
)

rng = np.random.default_rng(0)

# ---------------------------------------------------------------------------
# _polygon_to_mask
# ---------------------------------------------------------------------------


class TestPolygonToMask:
    def test_integer_array(self):
        polygon = np.array([[10, 10], [10, 50], [50, 50], [50, 10]], dtype=np.int32)
        mask = _polygon_to_mask(polygon, 100, 100)
        assert mask.shape == (100, 100)
        assert mask.dtype == np.uint8
        assert mask.sum() > 0

    def test_list_of_points(self):
        polygon = [[5.0, 5.0], [5.0, 20.0], [20.0, 20.0], [20.0, 5.0]]
        mask = _polygon_to_mask(polygon, 50, 50)
        assert mask.shape == (50, 50)
        assert mask.sum() > 0


# ---------------------------------------------------------------------------
# _generate_masked_features
# ---------------------------------------------------------------------------


class TestGenerateMaskedFeatures:
    def test_valid_mask_returns_features(self):
        feats = rng.random((64, 64, 256)).astype(np.float32)
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[20:80, 20:80] = 1
        result = _generate_masked_features(feats, mask, threshold_mask=0.3, image_size=1024)
        assert result is not None
        assert result.shape == (1, 256)
        # Should be normalized
        norm = np.linalg.norm(result, axis=-1)
        np.testing.assert_allclose(norm, 1.0, atol=1e-5)

    def test_empty_mask_returns_none(self):
        feats = rng.random((64, 64, 256)).astype(np.float32)
        mask = np.zeros((100, 100), dtype=np.uint8)
        result = _generate_masked_features(feats, mask, threshold_mask=0.5, image_size=1024)
        assert result is None


# ---------------------------------------------------------------------------
# _pad_to_square
# ---------------------------------------------------------------------------


class TestPadToSquare:
    def test_padding(self):
        x = np.ones((500, 700), dtype=np.float32)
        result = _pad_to_square(x, image_size=1024)
        assert result.shape == (1024, 1024)
        # original area preserved
        assert result[:500, :700].sum() == 500 * 700
        # padded area is zero
        assert result[500:, :].sum() == 0
        assert result[:, 700:].sum() == 0


# ---------------------------------------------------------------------------
# _decide_masks
# ---------------------------------------------------------------------------


class TestDecideMasks:
    def test_is_single_uses_idx_0(self):
        masks = np.ones((1, 4, 32, 32), dtype=np.float32)
        logits = rng.random((1, 4, 16, 16)).astype(np.float32)
        scores = np.array([[0.2, 0.9, 0.5, 0.3]])
        log_out, _, _ = _decide_masks(masks, logits, scores, is_single=True)
        assert log_out is not None
        assert log_out.shape[1] == 1
        # is_single always uses best_idx=0
        np.testing.assert_array_equal(log_out, logits[:, [0]])

    def test_not_single_skips_first(self):
        masks = np.ones((1, 4, 32, 32), dtype=np.float32)
        logits = rng.random((1, 4, 16, 16)).astype(np.float32)
        scores = np.array([[0.1, 0.9, 0.8, 0.5]])
        # After skipping index 0, remaining scores are [0.9, 0.8, 0.5], best is index 0 of remaining
        _, _, score = _decide_masks(masks, logits, scores, is_single=False)
        assert score == pytest.approx(0.9, abs=1e-5)

    def test_all_zero_masks(self):
        masks = np.zeros((1, 4, 32, 32), dtype=np.float32)
        logits = rng.random((1, 4, 16, 16)).astype(np.float32)
        scores = np.array([[0.1, 0.9, 0.8, 0.5]])
        log_out, mask_out, score = _decide_masks(masks, logits, scores, is_single=False)
        assert log_out is None
        assert score == 0.0
        assert mask_out.sum() == 0


# ---------------------------------------------------------------------------
# _topk_numpy
# ---------------------------------------------------------------------------


class TestTopkNumpy:
    def test_largest_true(self):
        x = np.array([1, 5, 3, 4, 2])
        vals, _ = _topk_numpy(x, k=3, largest=True)
        assert list(vals) == [5, 4, 3]

    def test_largest_false(self):
        x = np.array([1, 5, 3, 4, 2])
        vals, _ = _topk_numpy(x, k=2, largest=False)
        assert list(vals) == [1, 2]


# ---------------------------------------------------------------------------
# _get_prepadded_size
# ---------------------------------------------------------------------------


class TestGetPrepaddedSize:
    def test_landscape(self):
        original = np.array([500, 1000])
        result = _get_prepadded_size(original, 1024)
        # longer side scaled to 1024
        assert result[1] == 1024
        assert result[0] < 1024

    def test_square(self):
        original = np.array([800, 800])
        result = _get_prepadded_size(original, 1024)
        assert result[0] == result[1] == 1024


# ---------------------------------------------------------------------------
# _resize_to_original_shape
# ---------------------------------------------------------------------------


class TestResizeToOriginalShape:
    def test_output_shape(self):
        masks = rng.random((64, 64)).astype(np.float32)
        original_shape = np.array([480, 640])
        result = _resize_to_original_shape(masks, 1024, original_shape)
        assert result.shape == (480, 640)


# ---------------------------------------------------------------------------
# _point_selection
# ---------------------------------------------------------------------------


class TestPointSelection:
    def test_with_points_above_threshold(self):
        sim = np.zeros((100, 100), dtype=np.float32)
        sim[40:60, 40:60] = 0.9
        original_shape = np.array([100, 100])
        pts, bg = _point_selection(sim, original_shape, threshold=0.5, num_bg_points=1, image_size=1024, downsizing=64)
        assert pts is not None
        assert bg is not None
        assert pts.shape[1] == 3  # x, y, score

    def test_empty_case(self):
        sim = np.zeros((100, 100), dtype=np.float32)
        original_shape = np.array([100, 100])
        pts, bg = _point_selection(sim, original_shape, threshold=0.5, num_bg_points=1, image_size=1024, downsizing=64)
        assert pts is None
        assert bg is None


# ---------------------------------------------------------------------------
# _inspect_overlapping_areas
# ---------------------------------------------------------------------------


class TestInspectOverlappingAreas:
    def test_no_overlap(self):
        mask_a = np.zeros((50, 50), dtype=np.float32)
        mask_a[:25, :] = 1
        mask_b = np.zeros((50, 50), dtype=np.float32)
        mask_b[25:, :] = 1
        predicted = {0: [mask_a], 1: [mask_b]}
        used_pts = {0: [np.array([10, 10, 0.9])], 1: [np.array([10, 30, 0.8])]}
        _inspect_overlapping_areas(predicted, used_pts)
        assert len(predicted[0]) == 1
        assert len(predicted[1]) == 1

    def test_high_overlap_removes_lower_score(self):
        mask = np.ones((50, 50), dtype=np.float32)
        predicted = {0: [mask.copy()], 1: [mask.copy()]}
        used_pts = {0: [np.array([10, 10, 0.9])], 1: [np.array([10, 10, 0.5])]}
        _inspect_overlapping_areas(predicted, used_pts, threshold_iou=0.8)
        # Lower-scored mask (label 1) should be removed
        assert len(predicted[1]) == 0
        assert len(predicted[0]) == 1

    def test_partial_overlap_zeros_intersection(self):
        mask_a = np.zeros((50, 50), dtype=np.float32)
        mask_a[:30, :] = 1
        mask_b = np.zeros((50, 50), dtype=np.float32)
        mask_b[20:, :] = 1
        predicted = {0: [mask_a.copy()], 1: [mask_b.copy()]}
        used_pts = {0: [np.array([10, 10, 0.9])], 1: [np.array([10, 30, 0.5])]}
        _inspect_overlapping_areas(predicted, used_pts, threshold_iou=0.95)
        # Partial overlap: intersection region zeroed in lower-scored mask
        assert predicted[1][0][20:30, :].sum() == 0


# ---------------------------------------------------------------------------
# _get_prompt_candidates
# ---------------------------------------------------------------------------


class TestGetPromptCandidates:
    def test_basic_flow(self):
        ref_feats = rng.random((2, 1, 256)).astype(np.float32)
        ref_feats = ref_feats / np.linalg.norm(ref_feats, axis=-1, keepdims=True)
        image_emb = rng.random((1, 256, 64, 64)).astype(np.float32)
        used_indices = np.array([0, 1])
        original_shape = np.array([480, 640])
        pts_scores, bg_coords = _get_prompt_candidates(
            image_embeddings=image_emb,
            reference_feats=ref_feats,
            used_indices=used_indices,
            original_shape=original_shape,
            threshold=0.0,
            num_bg_points=1,
            default_threshold_target=0.0,
            image_size=1024,
            downsizing=64,
        )
        assert isinstance(pts_scores, dict)
        assert isinstance(bg_coords, dict)


# ---------------------------------------------------------------------------
# SAMVisualPrompter
# ---------------------------------------------------------------------------


def _make_mock_encoder_decoder():
    encoder = MagicMock()
    encoder.params = MagicMock()
    encoder.params.image_size = 1024
    encoder.params.resize_type = "standard"

    decoder = MagicMock()
    decoder.params = MagicMock()
    decoder.params.embed_dim = 256
    decoder.params.mask_threshold = 0.0
    return encoder, decoder


class TestSAMVisualPrompter:
    def test_init(self):
        enc, dec = _make_mock_encoder_decoder()
        prompter = SAMVisualPrompter(enc, dec)
        assert prompter.encoder is enc
        assert prompter.decoder is dec

    def test_infer_no_prompts_raises(self):
        enc, dec = _make_mock_encoder_decoder()
        prompter = SAMVisualPrompter(enc, dec)
        with pytest.raises(RuntimeError, match="boxes or points prompts are required"):
            prompter.infer(np.zeros((100, 100, 3), dtype=np.uint8))

    def test_call_delegates_to_infer(self):
        enc, dec = _make_mock_encoder_decoder()
        prompter = SAMVisualPrompter(enc, dec)
        with pytest.raises(RuntimeError, match="boxes or points prompts are required"):
            prompter(np.zeros((100, 100, 3), dtype=np.uint8))


# ---------------------------------------------------------------------------
# SAMLearnableVisualPrompter
# ---------------------------------------------------------------------------


class TestSAMLearnableVisualPrompter:
    def test_init_default(self):
        enc, dec = _make_mock_encoder_decoder()
        prompter = SAMLearnableVisualPrompter(enc, dec)
        assert prompter._threshold == 0.65  # noqa: SLF001
        assert not prompter.has_reference_features()

    def test_init_with_reference_features(self):
        enc, dec = _make_mock_encoder_decoder()
        feats = VisualPromptingFeatures(
            feature_vectors=rng.random((3, 1, 256)).astype(np.float32),
            used_indices=np.array([0, 1, 2]),
        )
        prompter = SAMLearnableVisualPrompter(enc, dec, reference_features=feats)
        assert prompter.has_reference_features()

    def test_init_invalid_threshold(self):
        enc, dec = _make_mock_encoder_decoder()
        with pytest.raises(ValueError, match="Confidence threshold"):
            SAMLearnableVisualPrompter(enc, dec, threshold=1.5)

    def test_reference_features_property_success(self):
        enc, dec = _make_mock_encoder_decoder()
        feats = VisualPromptingFeatures(
            feature_vectors=rng.random((2, 1, 256)).astype(np.float32),
            used_indices=np.array([0, 1]),
        )
        prompter = SAMLearnableVisualPrompter(enc, dec, reference_features=feats)
        result = prompter.reference_features
        assert isinstance(result, VisualPromptingFeatures)

    def test_reference_features_property_error(self):
        enc, dec = _make_mock_encoder_decoder()
        prompter = SAMLearnableVisualPrompter(enc, dec)
        with pytest.raises(RuntimeError, match="Reference features are not generated"):
            _ = prompter.reference_features

    def test_reset_reference_info(self):
        enc, dec = _make_mock_encoder_decoder()
        prompter = SAMLearnableVisualPrompter(enc, dec)
        prompter.reset_reference_info()
        assert prompter._reference_features is not None  # noqa: SLF001
        assert prompter._reference_features.shape == (0, 1, 256)  # noqa: SLF001
        assert len(prompter._used_indices) == 0  # noqa: SLF001

    def test_gather_prompts_with_labels(self):
        enc, dec = _make_mock_encoder_decoder()
        prompter = SAMLearnableVisualPrompter(enc, dec)
        prompts = [
            {"label": np.int64(0), "data": np.array([1, 2])},
            {"label": np.int64(1), "data": np.array([3, 4])},
            {"label": np.int64(0), "data": np.array([5, 6])},
        ]
        result = prompter._gather_prompts_with_labels(prompts)  # noqa: SLF001
        assert 0 in result
        assert 1 in result
        assert len(result[0]) == 2
        assert len(result[1]) == 1

    def test_expand_reference_info(self):
        enc, dec = _make_mock_encoder_decoder()
        prompter = SAMLearnableVisualPrompter(enc, dec)
        prompter.reset_reference_info()
        prompter._expand_reference_info(5)  # noqa: SLF001
        assert prompter._reference_features.shape[0] == 6  # noqa: SLF001  # 0..5

    def test_learn_no_prompts_raises(self):
        enc, dec = _make_mock_encoder_decoder()
        prompter = SAMLearnableVisualPrompter(enc, dec)
        with pytest.raises(RuntimeError, match="boxes, polygons or points prompts are required"):
            prompter.learn(np.zeros((100, 100, 3), dtype=np.uint8))

    def test_infer_without_reference_features_raises(self):
        enc, dec = _make_mock_encoder_decoder()
        prompter = SAMLearnableVisualPrompter(enc, dec)
        with pytest.raises(RuntimeError, match="Reference features are not defined"):
            prompter.infer(np.zeros((100, 100, 3), dtype=np.uint8))


# ---------------------------------------------------------------------------
# SAMVisualPrompter.infer() - full path
# ---------------------------------------------------------------------------


class TestSAMVisualPrompterInfer:
    """Cover lines 71-117: the happy-path through SAMVisualPrompter.infer()."""

    @staticmethod
    def _make_prompt():
        return {
            "point_coords": np.array([[[10.0, 10.0]]]),
            "point_labels": np.array([[1.0]]),
            "mask_input": np.zeros((1, 1, 256, 256)),
            "has_mask_input": np.array([[0.0]]),
            "orig_size": np.array([[100, 100]]),
            "label": 1,
        }

    @staticmethod
    def _make_postprocess_result():
        return {
            "upscaled_masks": np.ones((1, 4, 100, 100)),
            "iou_predictions": np.array([[0.9, 0.8, 0.7, 0.6]]),
            "low_res_masks": np.ones((1, 4, 64, 64)),
            "scores": np.array([[0.9, 0.8, 0.7, 0.6]]),
            "labels": 1,
            "hard_prediction": np.ones((4, 100, 100)),
            "soft_prediction": np.ones((4, 100, 100)),
        }

    @staticmethod
    def _setup_encoder_decoder():
        enc, dec = _make_mock_encoder_decoder()
        processed_image = np.zeros((1, 3, 1024, 1024), dtype=np.float32)
        meta = {"original_shape": (100, 100, 3)}
        enc.base_preprocess.return_value = (processed_image, meta)
        enc.infer_sync.return_value = {"image_embeddings": np.ones((1, 256, 64, 64))}

        dec.base_preprocess.side_effect = lambda _: [
            TestSAMVisualPrompterInfer._make_prompt(),
        ]
        dec.infer_sync.return_value = {
            "upscaled_masks": np.ones((1, 4, 100, 100)),
            "iou_predictions": np.array([[0.9, 0.8, 0.7, 0.6]]),
            "low_res_masks": np.ones((1, 4, 64, 64)),
        }
        dec.postprocess.side_effect = lambda p, m: TestSAMVisualPrompterInfer._make_postprocess_result()
        dec.output_blob_name = "upscaled_masks"
        return enc, dec

    def test_infer_with_boxes(self):
        enc, dec = self._setup_encoder_decoder()
        prompter = SAMVisualPrompter(enc, dec)
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        boxes = [Prompt(data=np.array([10, 10, 50, 50]), label=1)]
        result = prompter.infer(image, boxes=boxes)
        assert result is not None
        assert len(result.labels) == 1
        assert len(result.best_iou) == 1

    def test_infer_with_points(self):
        enc, dec = self._setup_encoder_decoder()
        prompter = SAMVisualPrompter(enc, dec)
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        points = [Prompt(data=np.array([25, 25]), label=0)]
        result = prompter.infer(image, points=points)
        assert len(result.processed_mask) == 1

    def test_infer_with_boxes_and_points(self):
        enc, dec = self._setup_encoder_decoder()

        # Two prompts returned by decoder

        def _two_prompts(_):
            p1 = self._make_prompt()
            p1["label"] = 1
            p2 = self._make_prompt()
            p2["label"] = 2
            return [p1, p2]

        dec.base_preprocess.side_effect = _two_prompts
        prompter = SAMVisualPrompter(enc, dec)
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        result = prompter.infer(
            image,
            boxes=[Prompt(data=np.array([10, 10, 50, 50]), label=1)],
            points=[Prompt(data=np.array([30, 30]), label=2)],
        )
        assert len(result.labels) == 2

    def test_call_delegates(self):
        enc, dec = self._setup_encoder_decoder()
        prompter = SAMVisualPrompter(enc, dec)
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        boxes = [Prompt(data=np.array([10, 10, 50, 50]), label=1)]
        result = prompter(image, boxes=boxes)
        assert result is not None


# ---------------------------------------------------------------------------
# SAMLearnableVisualPrompter.learn() - lines 229-302
# ---------------------------------------------------------------------------


class TestSAMLearnableVisualPrompterLearn:
    @staticmethod
    def _make_prompt_dict(label=0):
        return {
            "point_coords": np.array([[[10.0, 10.0]]]),
            "point_labels": np.array([[1.0]]),
            "mask_input": np.zeros((1, 1, 256, 256)),
            "has_mask_input": np.array([[0.0]]),
            "orig_size": np.array([[100, 100]]),
            "label": np.int64(label),
        }

    @staticmethod
    def _setup():
        enc, dec = _make_mock_encoder_decoder()
        enc.return_value = np.ones((1, 256, 64, 64), dtype=np.float32)
        dec.base_preprocess.side_effect = lambda _: [
            TestSAMLearnableVisualPrompterLearn._make_prompt_dict(0),
        ]
        dec.infer_sync.return_value = {
            "upscaled_masks": np.ones((1, 4, 100, 100), dtype=np.float32),
            "iou_predictions": np.array([[0.9, 0.8, 0.7, 0.6]]),
            "low_res_masks": np.ones((1, 4, 64, 64), dtype=np.float32),
        }
        dec.output_blob_name = "upscaled_masks"
        dec.apply_coords.side_effect = lambda c, s: c
        return enc, dec

    def test_learn_with_boxes(self):
        enc, dec = self._setup()
        prompter = SAMLearnableVisualPrompter(enc, dec)
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        boxes = [Prompt(data=np.array([10, 10, 50, 50]), label=0)]
        feats, ref_masks = prompter.learn(image, boxes=boxes)
        assert isinstance(feats, VisualPromptingFeatures)
        assert ref_masks.shape[0] >= 1
        assert prompter.has_reference_features()

    def test_learn_with_points(self):
        enc, dec = self._setup()
        prompter = SAMLearnableVisualPrompter(enc, dec)
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        points = [Prompt(data=np.array([25, 25]), label=0)]
        feats, _ = prompter.learn(image, points=points)
        assert isinstance(feats, VisualPromptingFeatures)

    def test_learn_with_polygons_only(self):
        enc, dec = self._setup()
        dec.base_preprocess.return_value = []  # no box/point prompts
        prompter = SAMLearnableVisualPrompter(enc, dec)
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        polygon_pts = np.array([[10, 10], [10, 50], [50, 50], [50, 10]], dtype=np.int32)
        polygons = [Prompt(data=polygon_pts, label=0)]
        feats, ref_masks = prompter.learn(image, polygons=polygons)
        assert isinstance(feats, VisualPromptingFeatures)
        assert ref_masks[0].sum() > 0

    def test_learn_with_reset_features(self):
        enc, dec = self._setup()
        prompter = SAMLearnableVisualPrompter(enc, dec)
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        boxes = [Prompt(data=np.array([10, 10, 50, 50]), label=0)]
        # First learn
        prompter.learn(image, boxes=boxes)
        # Second learn with reset
        feats, _ = prompter.learn(image, boxes=boxes, reset_features=True)
        assert isinstance(feats, VisualPromptingFeatures)

    def test_learn_unsupported_prompt_type_raises(self):
        """Lines 280-281: unsupported prompt type raises RuntimeError."""
        enc, dec = self._setup()
        # Clear side_effect so return_value takes effect
        dec.base_preprocess.side_effect = None
        # Return a prompt that has neither point_coords nor polygon
        dec.base_preprocess.return_value = [{"label": np.int64(0), "unsupported_key": np.array([1, 2])}]
        prompter = SAMLearnableVisualPrompter(enc, dec)
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        with pytest.raises(RuntimeError, match="Unsupported type of prompt"):
            prompter.learn(image, boxes=[Prompt(data=np.array([10, 10, 50, 50]), label=0)])

    def test_learn_multiple_labels(self):
        enc, dec = self._setup()
        dec.base_preprocess.side_effect = lambda _: [
            self._make_prompt_dict(0),
            self._make_prompt_dict(3),
        ]
        prompter = SAMLearnableVisualPrompter(enc, dec)
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        boxes = [
            Prompt(data=np.array([10, 10, 50, 50]), label=0),
            Prompt(data=np.array([30, 30, 60, 60]), label=3),
        ]
        feats, ref_masks = prompter.learn(image, boxes=boxes)
        assert ref_masks.shape[0] == 4  # labels 0..3
        assert 0 in feats.used_indices
        assert 3 in feats.used_indices


# ---------------------------------------------------------------------------
# SAMLearnableVisualPrompter.__call__ - line 311
# ---------------------------------------------------------------------------


class TestSAMLearnableVisualPrompterCall:
    def test_call_delegates_to_infer(self):
        enc, dec = _make_mock_encoder_decoder()
        enc.return_value = np.ones((1, 256, 64, 64), dtype=np.float32)
        dec.apply_coords.side_effect = lambda c, s: c
        dec.infer_sync.return_value = {
            "upscaled_masks": np.ones((1, 4, 100, 100), dtype=np.float32),
            "iou_predictions": np.array([[0.9, 0.8, 0.7, 0.6]]),
            "low_res_masks": np.ones((1, 4, 64, 64), dtype=np.float32),
        }
        dec.output_blob_name = "upscaled_masks"

        feats = VisualPromptingFeatures(
            feature_vectors=rng.random((2, 1, 256)).astype(np.float32),
            used_indices=np.array([0, 1]),
        )
        prompter = SAMLearnableVisualPrompter(enc, dec, reference_features=feats)
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        result = prompter(image)
        assert result is not None


# ---------------------------------------------------------------------------
# SAMLearnableVisualPrompter.infer() - lines 345-427
# ---------------------------------------------------------------------------


class TestSAMLearnableVisualPrompterInfer:
    @staticmethod
    def _setup_for_infer():
        enc, dec = _make_mock_encoder_decoder()
        enc.return_value = np.ones((1, 256, 64, 64), dtype=np.float32)
        dec.apply_coords.side_effect = lambda c, s: c
        dec.infer_sync.return_value = {
            "upscaled_masks": np.ones((1, 4, 100, 100), dtype=np.float32),
            "iou_predictions": np.array([[0.9, 0.8, 0.7, 0.6]]),
            "low_res_masks": np.ones((1, 4, 64, 64), dtype=np.float32),
        }
        dec.output_blob_name = "upscaled_masks"
        return enc, dec

    def test_infer_with_internal_features(self):
        enc, dec = self._setup_for_infer()
        feats = VisualPromptingFeatures(
            feature_vectors=rng.random((2, 1, 256)).astype(np.float32),
            used_indices=np.array([0, 1]),
        )
        prompter = SAMLearnableVisualPrompter(enc, dec, reference_features=feats)
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        result = prompter.infer(image)
        assert isinstance(result, ZSLVisualPromptingResult)

    def test_infer_with_external_features(self):
        enc, dec = self._setup_for_infer()
        prompter = SAMLearnableVisualPrompter(enc, dec)
        feats = VisualPromptingFeatures(
            feature_vectors=rng.random((2, 1, 256)).astype(np.float32),
            used_indices=np.array([0, 1]),
        )
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        result = prompter.infer(image, reference_features=feats)
        assert isinstance(result, ZSLVisualPromptingResult)

    def test_infer_skips_zero_score_points(self):
        """Line 379: points with score 0 or -1 are skipped."""
        enc, dec = self._setup_for_infer()
        feats = VisualPromptingFeatures(
            feature_vectors=rng.random((2, 1, 256)).astype(np.float32),
            used_indices=np.array([0, 1]),
        )
        prompter = SAMLearnableVisualPrompter(enc, dec, reference_features=feats)
        image = np.zeros((100, 100, 3), dtype=np.uint8)

        mock_pts = {
            0: np.array([[10, 10, 0.0], [20, 20, -1.0], [30, 30, 0.9]]),
        }
        mock_bg = {0: np.array([[5, 5]])}
        with patch("model_api.models.visual_prompting._get_prompt_candidates", return_value=(mock_pts, mock_bg)):
            result = prompter.infer(image)
        assert isinstance(result, ZSLVisualPromptingResult)

    def test_infer_skips_duplicate_points(self):
        """Lines 383-389: skip point already covered by existing mask."""
        enc, dec = self._setup_for_infer()
        # The decoder returns a mask that covers point (30, 30)
        mask_result = np.ones((1, 4, 100, 100), dtype=np.float32)
        dec.infer_sync.return_value = {
            "upscaled_masks": mask_result,
            "iou_predictions": np.array([[0.9, 0.8, 0.7, 0.6]]),
            "low_res_masks": np.ones((1, 4, 64, 64), dtype=np.float32),
        }
        feats = VisualPromptingFeatures(
            feature_vectors=rng.random((2, 1, 256)).astype(np.float32),
            used_indices=np.array([0, 1]),
        )
        prompter = SAMLearnableVisualPrompter(enc, dec, reference_features=feats)
        image = np.zeros((100, 100, 3), dtype=np.uint8)

        # Two points for same label; second point (30,30) is covered by mask from first
        mock_pts = {
            0: np.array([[10, 10, 0.9], [30, 30, 0.8]]),
        }
        mock_bg = {0: np.array([[5, 5]])}
        with patch("model_api.models.visual_prompting._get_prompt_candidates", return_value=(mock_pts, mock_bg)):
            result = prompter.infer(image)
        assert isinstance(result, ZSLVisualPromptingResult)

    def test_infer_used_indices_none_raises(self):
        enc, dec = self._setup_for_infer()
        prompter = SAMLearnableVisualPrompter(enc, dec)
        prompter._reference_features = np.zeros((2, 1, 256), dtype=np.float32)  # noqa: SLF001
        prompter._used_indices = None  # noqa: SLF001
        with pytest.raises(RuntimeError, match="Used indices are not defined"):
            prompter.infer(np.zeros((100, 100, 3), dtype=np.uint8))


# ---------------------------------------------------------------------------
# _expand_reference_info - lines 453-454
# ---------------------------------------------------------------------------


class TestExpandReferenceInfoError:
    def test_expand_none_raises(self):
        enc, dec = _make_mock_encoder_decoder()
        prompter = SAMLearnableVisualPrompter(enc, dec)
        # _reference_features is None by default
        with pytest.raises(RuntimeError, match="Can not expand non existing reference info"):
            prompter._expand_reference_info(5)  # noqa: SLF001


# ---------------------------------------------------------------------------
# _predict_masks - lines 474-540
# ---------------------------------------------------------------------------


class TestPredictMasks:
    @staticmethod
    def _setup():
        enc, dec = _make_mock_encoder_decoder()
        dec.apply_coords.side_effect = lambda c, s: c
        dec.infer_sync.return_value = {
            "upscaled_masks": np.ones((1, 4, 100, 100), dtype=np.float32),
            "iou_predictions": np.array([[0.9, 0.8, 0.7, 0.6]]),
            "low_res_masks": np.ones((1, 4, 64, 64), dtype=np.float32),
        }
        dec.output_blob_name = "upscaled_masks"
        return enc, dec

    def test_single_iteration(self):
        """is_cascade=False => 1 iteration (i=0 only)."""
        enc, dec = self._setup()
        prompter = SAMLearnableVisualPrompter(enc, dec)
        inputs = {
            "point_coords": np.array([[[10.0, 10.0]]], dtype=np.float32),
            "point_labels": np.array([[1.0]], dtype=np.float32),
            "orig_size": np.array([[100, 100]]),
            "image_embeddings": np.ones((1, 256, 64, 64), dtype=np.float32),
        }
        result = prompter._predict_masks(inputs, np.array([100, 100]), is_cascade=False)  # noqa: SLF001
        assert "upscaled_masks" in result
        dec.infer_sync.assert_called_once()

    def test_cascade_three_iterations(self):
        """is_cascade=True => 3 iterations."""
        enc, dec = self._setup()
        prompter = SAMLearnableVisualPrompter(enc, dec)
        inputs = {
            "point_coords": np.array([[[10.0, 10.0]]], dtype=np.float32),
            "point_labels": np.array([[1.0]], dtype=np.float32),
            "orig_size": np.array([[100, 100]]),
            "image_embeddings": np.ones((1, 256, 64, 64), dtype=np.float32),
        }
        result = prompter._predict_masks(inputs, np.array([100, 100]), is_cascade=True)  # noqa: SLF001
        assert "upscaled_masks" in result
        assert dec.infer_sync.call_count == 3

    def test_cascade_early_exit_at_iter1(self):
        """Masks sum to 0 at iteration 1 => early return (line 493)."""
        enc, dec = self._setup()
        # First call: upscaled_masks all slightly negative so masks > 0 threshold => all False
        first_response = {
            "upscaled_masks": np.full((1, 4, 100, 100), -0.1, dtype=np.float32),
            "iou_predictions": np.array([[0.9, 0.8, 0.7, 0.6]]),
            "low_res_masks": np.ones((1, 4, 64, 64), dtype=np.float32),
        }
        dec.infer_sync.side_effect = [first_response]
        prompter = SAMLearnableVisualPrompter(enc, dec)
        inputs = {
            "point_coords": np.array([[[10.0, 10.0]]], dtype=np.float32),
            "point_labels": np.array([[1.0]], dtype=np.float32),
            "orig_size": np.array([[100, 100]]),
            "image_embeddings": np.ones((1, 256, 64, 64), dtype=np.float32),
        }
        result = prompter._predict_masks(inputs, np.array([100, 100]), is_cascade=True)  # noqa: SLF001
        assert result["upscaled_masks"].sum() == 0
        assert dec.infer_sync.call_count == 1  # stopped at iter 1

    def test_cascade_early_exit_at_iter2(self):
        """Masks sum to 0 at iteration 2 => early return (line 505)."""
        enc, dec = self._setup()
        # iter 0: normal non-zero masks
        iter0_masks = np.ones((1, 4, 100, 100), dtype=np.float32)
        # iter 1: only index 0 is non-zero, rest are zero
        # After _decide_masks(is_single=False) skips idx 0, remaining are all-zero
        iter1_masks = np.zeros((1, 4, 100, 100), dtype=np.float32)
        iter1_masks[:, 0, :, :] = 1.0  # only index 0 non-zero
        dec.infer_sync.side_effect = [
            # iter 0
            {
                "upscaled_masks": iter0_masks,
                "iou_predictions": np.array([[0.9, 0.8, 0.7, 0.6]]),
                "low_res_masks": np.ones((1, 4, 64, 64), dtype=np.float32),
            },
            # iter 1
            {
                "upscaled_masks": iter1_masks,
                "iou_predictions": np.array([[0.9, 0.0, 0.0, 0.0]]),
                "low_res_masks": np.ones((1, 4, 64, 64), dtype=np.float32),
            },
        ]
        prompter = SAMLearnableVisualPrompter(enc, dec)
        inputs = {
            "point_coords": np.array([[[10.0, 10.0]]], dtype=np.float32),
            "point_labels": np.array([[1.0]], dtype=np.float32),
            "orig_size": np.array([[100, 100]]),
            "image_embeddings": np.ones((1, 256, 64, 64), dtype=np.float32),
        }
        result = prompter._predict_masks(inputs, np.array([100, 100]), is_cascade=True)  # noqa: SLF001
        assert result["upscaled_masks"].sum() == 0
        assert dec.infer_sync.call_count == 2


# ---------------------------------------------------------------------------
# _inspect_overlapping_areas - missing branches
# ---------------------------------------------------------------------------


class TestInspectOverlappingAreasExtra:
    def test_union_zero_returns_zero_iou(self):
        """Line 803: union==0 => iou=0.0, no removal."""
        mask_a = np.zeros((50, 50), dtype=np.float32)
        mask_b = np.zeros((50, 50), dtype=np.float32)
        predicted = {0: [mask_a], 1: [mask_b]}
        used_pts = {0: [np.array([10, 10, 0.9])], 1: [np.array([10, 30, 0.8])]}
        _inspect_overlapping_areas(predicted, used_pts)
        assert len(predicted[0]) == 1
        assert len(predicted[1]) == 1

    def test_high_overlap_other_score_higher_removes_label(self):
        """Line 825: other score is higher => label mask is removed."""
        mask = np.ones((50, 50), dtype=np.float32)
        predicted = {0: [mask.copy()], 1: [mask.copy()]}
        # label 0 has *lower* score than label 1
        used_pts = {0: [np.array([10, 10, 0.3])], 1: [np.array([10, 10, 0.9])]}
        _inspect_overlapping_areas(predicted, used_pts, threshold_iou=0.8)
        # label 0 should be removed (lower score)
        assert len(predicted[0]) == 0
        assert len(predicted[1]) == 1

    def test_partial_overlap_label_mask_zeroed(self):
        """Line 832: partial overlap, label mask zeroed when other score higher."""
        mask_a = np.zeros((50, 50), dtype=np.float32)
        mask_a[:30, :] = 1
        mask_b = np.zeros((50, 50), dtype=np.float32)
        mask_b[20:, :] = 1
        predicted = {0: [mask_a.copy()], 1: [mask_b.copy()]}
        # label 0 has lower score
        used_pts = {0: [np.array([10, 10, 0.3])], 1: [np.array([10, 30, 0.9])]}
        _inspect_overlapping_areas(predicted, used_pts, threshold_iou=0.95)
        # overlap region in label 0 mask should be zeroed
        assert predicted[0][0][20:30, :].sum() == 0

    def test_multiple_masks_per_label_removal(self):
        """Lines 835-836: masks.pop(im) and used_points[label].pop(im)."""
        mask1 = np.ones((50, 50), dtype=np.float32)
        mask2 = np.ones((50, 50), dtype=np.float32)
        other_mask = np.ones((50, 50), dtype=np.float32)
        predicted = {0: [mask1.copy(), mask2.copy()], 1: [other_mask.copy()]}
        # Both label-0 masks have lower score than label-1
        used_pts = {
            0: [np.array([10, 10, 0.2]), np.array([20, 20, 0.1])],
            1: [np.array([10, 10, 0.9])],
        }
        _inspect_overlapping_areas(predicted, used_pts, threshold_iou=0.8)
        assert len(predicted[0]) == 0
        assert len(used_pts[0]) == 0
        assert len(predicted[1]) == 1
