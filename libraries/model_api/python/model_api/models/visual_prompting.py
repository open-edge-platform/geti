#
# Copyright (C) 2020-2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import annotations  # TODO: remove when Python3.9 support is dropped

from collections import defaultdict
from itertools import product
from typing import Any, NamedTuple

import cv2
import numpy as np

from model_api.models import (
    PredictedMask,
    SAMDecoder,
    SAMImageEncoder,
    VisualPromptingResult,
    ZSLVisualPromptingResult,
)


class VisualPromptingFeatures(NamedTuple):
    feature_vectors: np.ndarray
    used_indices: np.ndarray


class Prompt(NamedTuple):
    data: np.ndarray
    label: int | np.ndarray


class SAMVisualPrompter:
    """A wrapper that implements SAM Visual Prompter.

    Segmentation results can be obtained by calling infer() method
    with corresponding parameters.
    """

    def __init__(
        self,
        encoder_model: SAMImageEncoder,
        decoder_model: SAMDecoder,
    ):
        self.encoder = encoder_model
        self.decoder = decoder_model

    def infer(
        self,
        image: np.ndarray,
        boxes: list[Prompt] | None = None,
        points: list[Prompt] | None = None,
    ) -> VisualPromptingResult:
        """Obtains segmentation masks using given prompts.

        Args:
            image (np.ndarray): HWC-shaped image
            boxes (list[Prompt] | None, optional): Prompts containing bounding boxes (in XYXY torchvision format)
              and their labels (ints, one per box). Defaults to None.
            points (list[Prompt] | None, optional): Prompts containing points (in XY format)
              and their labels (ints, one per point). Defaults to None.

        Returns:
            VisualPromptingResult: result object containing predicted masks and aux information.
        """
        if boxes is None and points is None:
            msg = "boxes or points prompts are required for inference"
            raise RuntimeError(msg)

        outputs: list[dict[str, Any]] = []

        processed_image, meta = self.encoder.preprocess(image)
        image_embeddings = self.encoder.infer_sync(processed_image)
        processed_prompts = self.decoder.preprocess(
            {
                "bboxes": [box.data for box in boxes] if boxes else None,
                "points": [point.data for point in points] if points else None,
                "labels": {
                    "bboxes": [box.label for box in boxes] if boxes else None,
                    "points": [point.label for point in points] if points else None,
                },
                "orig_size": meta["original_shape"][:2],
            },
        )

        for prompt in processed_prompts:
            label = prompt.pop("label")
            prompt.update(**image_embeddings)

            prediction = self.decoder.infer_sync(prompt)
            prediction["scores"] = prediction["iou_predictions"]
            prediction["labels"] = label
            processed_prediction = self.decoder.postprocess(prediction, meta)

            hard_masks, scores, logits = (
                np.expand_dims(processed_prediction["hard_prediction"], 0),
                processed_prediction["iou_predictions"],
                processed_prediction["low_res_masks"],
            )
            _, mask, best_iou = _decide_masks(hard_masks, logits, scores)
            processed_prediction["processed_mask"] = mask
            processed_prediction["best_iou"] = best_iou

            outputs.append(processed_prediction)

        return VisualPromptingResult(
            upscaled_masks=[item["upscaled_masks"] for item in outputs],
            processed_mask=[item["processed_mask"] for item in outputs],
            low_res_masks=[item["low_res_masks"] for item in outputs],
            iou_predictions=[item["iou_predictions"] for item in outputs],
            scores=[item["scores"] for item in outputs],
            labels=[item["labels"] for item in outputs],
            hard_predictions=[item["hard_prediction"] for item in outputs],
            soft_predictions=[item["soft_prediction"] for item in outputs],
            best_iou=[item["best_iou"] for item in outputs],
        )

    def __call__(
        self,
        image: np.ndarray,
        boxes: list[Prompt] | None = None,
        points: list[Prompt] | None = None,
    ) -> VisualPromptingResult:
        """A wrapper of the SAMVisualPrompter.infer() method"""
        return self.infer(image, boxes, points)


class SAMLearnableVisualPrompter:
    """A wrapper that provides ZSL Visual Prompting workflow.
    To obtain segmentation results, one should run learn() first to obtain the reference features,
    or use previously generated ones.
    """

    def __init__(
        self,
        encoder_model: SAMImageEncoder,
        decoder_model: SAMDecoder,
        reference_features: VisualPromptingFeatures | None = None,
        threshold: float = 0.65,
    ):
        """Initializes ZSL pipeline.

        Args:
            encoder_model (SAMImageEncoder): initialized decoder wrapper
            decoder_model (SAMDecoder): initialized encoder wrapper
            reference_features (VisualPromptingFeatures | None, optional): Previously generated reference features.
                Once the features are passed, one can skip learn() method, and start predicting masks right away.
                Defaults to None.
            threshold (float, optional): Threshold to match vs reference features on infer(). Greater value means a
            stricter matching. Defaults to 0.65.
        """
        self.encoder = encoder_model
        self.decoder = decoder_model
        self._used_indices: np.ndarray | None = None
        self._reference_features: np.ndarray | None = None

        if reference_features is not None:
            self._reference_features = reference_features.feature_vectors
            self._used_indices = reference_features.used_indices

        self._point_labels_box = np.array([[2, 3]], dtype=np.float32)
        self._has_mask_inputs = [np.array([[0.0]]), np.array([[1.0]])]

        self._is_cascade: bool = False
        if 0 <= threshold <= 1:
            self._threshold: float = threshold
        else:
            msg = "Confidence threshold should belong to [0;1] range."
            raise ValueError(msg)
        self._num_bg_points: int = 1
        self._default_threshold_target: float = 0.0
        self._image_size: int = self.encoder.image_size
        self._downsizing: int = 64
        self._default_threshold_reference: float = 0.3

    def has_reference_features(self) -> bool:
        """Checks if reference features are stored in the object state."""
        return self._reference_features is not None and self._used_indices is not None

    @property
    def reference_features(self) -> VisualPromptingFeatures:
        """Property represents reference features. An exception is thrown if called when
        the features are not presented in the internal object state.
        """
        if self.has_reference_features():
            return VisualPromptingFeatures(
                np.copy(self._reference_features),
                np.copy(self._used_indices),
            )

        msg = "Reference features are not generated"
        raise RuntimeError(msg)

    def learn(
        self,
        image: np.ndarray,
        boxes: list[Prompt] | None = None,
        points: list[Prompt] | None = None,
        polygons: list[Prompt] | None = None,
        reset_features: bool = False,
    ) -> tuple[VisualPromptingFeatures, np.ndarray]:
        """Executes `learn` stage of SAM ZSL pipeline.

        Reference features are updated according to newly arrived prompts.
        Features corresponding to the same labels are overridden during
        consequent learn() calls.

        Args:
            image (np.ndarray): HWC-shaped image
            boxes (list[Prompt] | None, optional): Prompts containing bounding boxes (in XYXY torchvision format)
              and their labels (ints, one per box). Defaults to None.
            points (list[Prompt] | None, optional): Prompts containing points (in XY format)
              and their labels (ints, one per point). Defaults to None.
            polygons: (list[Prompt] | None): Prompts containing polygons (a sequence of points in XY format)
              and their labels (ints, one per polygon).
              Polygon prompts are used to mask out the source features without implying decoder usage. Defaults to None.
            reset_features (bool, optional): Forces learning from scratch. Defaults to False.

        Returns:
            tuple[VisualPromptingFeatures, np.ndarray]: return values are the updated VPT reference features and
                reference masks.
            The shape of the reference mask is N_labels x H x W, where H and W are the same as in the input image.
        """
        if boxes is None and points is None and polygons is None:
            msg = "boxes, polygons or points prompts are required for learning"
            raise RuntimeError(msg)

        if reset_features or not self.has_reference_features():
            self.reset_reference_info()

        processed_prompts = self.decoder.preprocess(
            {
                "bboxes": [box.data for box in boxes] if boxes else None,
                "points": [point.data for point in points] if points else None,
                "labels": {
                    "bboxes": [box.label for box in boxes] if boxes else None,
                    "points": [point.label for point in points] if points else None,
                },
                "orig_size": image.shape[:2],
            },
        )

        if polygons is not None:
            for poly in polygons:
                processed_prompts.append({"polygon": poly.data, "label": poly.label})

        processed_prompts_w_labels = self._gather_prompts_with_labels(processed_prompts)
        largest_label: int = max([int(p) for p in processed_prompts_w_labels] + [0])

        self._expand_reference_info(largest_label)

        original_shape = np.array(image.shape[:2])

        # forward image encoder
        image_embeddings = self.encoder(image)
        processed_embedding = image_embeddings.squeeze().transpose(1, 2, 0)

        # get reference masks
        ref_masks: np.ndarray = np.zeros(
            (largest_label + 1, *original_shape),
            dtype=np.uint8,
        )
        for label, input_prompts in processed_prompts_w_labels.items():
            ref_mask: np.ndarray = np.zeros(original_shape, dtype=np.uint8)
            for inputs_decoder in input_prompts:
                inputs_decoder.pop("label")
                if "point_coords" in inputs_decoder:
                    # bboxes and points
                    inputs_decoder["image_embeddings"] = image_embeddings
                    prediction = self._predict_masks(
                        inputs_decoder,
                        original_shape,
                        is_cascade=self._is_cascade,
                    )
                    masks = prediction["upscaled_masks"]
                elif "polygon" in inputs_decoder:
                    masks = _polygon_to_mask(inputs_decoder["polygon"], *original_shape)
                else:
                    msg = "Unsupported type of prompt"
                    raise RuntimeError(msg)
                ref_mask = np.where(masks, 1, ref_mask)

            ref_feat: np.ndarray | None = None
            cur_default_threshold_reference = self._default_threshold_reference
            while ref_feat is None:
                ref_feat = _generate_masked_features(
                    feats=processed_embedding,
                    masks=ref_mask,
                    threshold_mask=cur_default_threshold_reference,
                    image_size=self.encoder.image_size,
                )
                cur_default_threshold_reference -= 0.05

            if self._reference_features is not None:
                self._reference_features[label] = ref_feat
            self._used_indices = np.concatenate((self._used_indices, [label]))
            ref_masks[label] = ref_mask

        self._used_indices = np.unique(self._used_indices)

        return self.reference_features, ref_masks

    def __call__(
        self,
        image: np.ndarray,
        reference_features: VisualPromptingFeatures | None = None,
        apply_masks_refinement: bool = True,
    ) -> ZSLVisualPromptingResult:
        """A wrapper of the SAMLearnableVisualPrompter.infer() method"""
        return self.infer(image, reference_features, apply_masks_refinement)

    def infer(
        self,
        image: np.ndarray,
        reference_features: VisualPromptingFeatures | None = None,
        apply_masks_refinement: bool = True,
    ) -> ZSLVisualPromptingResult:
        """Obtains masks by already prepared reference features.

        Reference features can be obtained with SAMLearnableVisualPrompter.learn() and passed as an argument.
        If the features are not passed, instance internal state will be used as a source of the features.

        Args:
            image (np.ndarray): HWC-shaped image
            reference_features (VisualPromptingFeatures | None, optional): Reference features object obtained during
                previous learn() calls. If not passed, object internal state is used, which reflects the last learn()
                call. Defaults to None.
            apply_masks_refinement (bool, optional): Flag controlling additional refinement stage on inference.
            Once enabled, decoder will be launched 2 extra times to refine the masks obtained with the first decoder
            call. Defaults to True.

        Returns:
            ZSLVisualPromptingResult: Mapping label -> predicted mask. Each mask object contains a list of binary masks,
                and a list of related prompts. Each binary mask corresponds to one prompt point. Class mask can be
                obtained by applying OR operation to all mask corresponding to one label.
        """
        if reference_features is None:
            if self._reference_features is None:
                msg = (
                    "Reference features are not defined. This parameter can be passed via "
                    "SAMLearnableVisualPrompter constructor, or as an argument of infer() method"
                )
                raise RuntimeError(msg)
            reference_feats = self._reference_features

            if self._used_indices is None:
                msg = (
                    "Used indices are not defined. This parameter can be passed via "
                    "SAMLearnableVisualPrompter constructor, or as an argument of infer() method"
                )
                raise RuntimeError(msg)
            used_idx = self._used_indices
        else:
            reference_feats, used_idx = reference_features

        original_shape = np.array(image.shape[:2])
        image_embeddings = self.encoder(image)

        total_points_scores, total_bg_coords = _get_prompt_candidates(
            image_embeddings=image_embeddings,
            reference_feats=reference_feats,
            used_indices=used_idx,
            original_shape=original_shape,
            threshold=self._threshold,
            num_bg_points=self._num_bg_points,
            default_threshold_target=self._default_threshold_target,
            image_size=self._image_size,
            downsizing=self._downsizing,
        )

        predicted_masks: dict[int, list] = defaultdict(list)
        used_points: defaultdict[int, list] = defaultdict(list)
        for label in total_points_scores:
            points_scores = total_points_scores[label]
            bg_coords = total_bg_coords[label]
            for points_score in points_scores:
                if points_score[-1] in [-1.0, 0.0]:
                    continue

                x, y = points_score[:2]
                is_done = False
                for pm in predicted_masks.get(label, []):
                    # check if that point is already assigned
                    if pm[int(y), int(x)] > 0:
                        is_done = True
                        break
                if is_done:
                    continue

                point_coords = np.concatenate(
                    (np.array([[x, y]]), bg_coords),
                    axis=0,
                    dtype=np.float32,
                )
                point_coords = self.decoder.apply_coords(point_coords, original_shape)
                point_labels = np.array([1] + [0] * len(bg_coords), dtype=np.float32)
                inputs_decoder = {
                    "point_coords": point_coords[None],
                    "point_labels": point_labels[None],
                    "orig_size": original_shape[None],
                }
                inputs_decoder["image_embeddings"] = image_embeddings

                _prediction: dict[str, np.ndarray] = self._predict_masks(
                    inputs_decoder,
                    original_shape,
                    apply_masks_refinement,
                )
                _prediction.update({"scores": points_score[-1]})

                predicted_masks[label].append(_prediction[self.decoder.output_blob_name])
                used_points[label].append(points_score)

        # check overlapping area between different label masks
        _inspect_overlapping_areas(predicted_masks, used_points)

        prediction: dict[int, PredictedMask] = {}
        for k in used_points:
            processed_points = []
            scores = []
            for pt in used_points[k]:
                processed_points.append(pt[:2])
                scores.append(float(pt[2]))
            prediction[k] = PredictedMask(predicted_masks[k], processed_points, scores)

        return ZSLVisualPromptingResult(prediction)

    def reset_reference_info(self) -> None:
        """Initialize reference information."""
        self._reference_features = np.zeros(
            (0, 1, self.decoder.embed_dim),
            dtype=np.float32,
        )
        self._used_indices = np.array([], dtype=np.int64)

    def _gather_prompts_with_labels(
        self,
        image_prompts: list[dict[str, np.ndarray]],
    ) -> dict[int, list[dict[str, np.ndarray]]]:
        """Gather prompts according to labels."""
        processed_prompts: defaultdict[int, list[dict[str, np.ndarray]]] = defaultdict(
            list,
        )
        for prompt in image_prompts:
            processed_prompts[int(prompt["label"])].append(prompt)

        return dict(sorted(processed_prompts.items(), key=lambda x: x))

    def _expand_reference_info(self, new_largest_label: int) -> None:
        """Expand reference info dimensions if newly given processed prompts have more labels."""
        if self._reference_features is None:
            msg = "Can not expand non existing reference info"
            raise RuntimeError(msg)

        if new_largest_label > (cur_largest_label := len(self._reference_features) - 1):
            diff = new_largest_label - cur_largest_label
            self._reference_features = np.pad(
                self._reference_features,
                ((0, diff), (0, 0), (0, 0)),
                constant_values=0.0,
            )

    def _predict_masks(
        self,
        inputs: dict[str, np.ndarray],
        original_size: np.ndarray,
        is_cascade: bool = False,
    ) -> dict[str, np.ndarray]:
        """Process function of OpenVINO Visual Prompting Inferencer."""
        masks: np.ndarray
        logits: np.ndarray
        scores: np.ndarray
        num_iter = 3 if is_cascade else 1
        for i in range(num_iter):
            if i == 0:
                # First-step prediction
                mask_input = np.zeros(
                    (1, 1, *(x * 4 for x in inputs["image_embeddings"].shape[2:])),
                    dtype=np.float32,
                )
                has_mask_input = self._has_mask_inputs[0]

            elif i == 1:
                # Cascaded Post-refinement-1
                mask_input, masks, _ = _decide_masks(
                    masks,  # noqa: F821 masks are set in the first iteration
                    logits,  # noqa: F821 masks are set in the first iteration
                    scores,  # noqa: F821 masks are set in the first iteration
                    is_single=True,
                )
                if masks.sum() == 0:
                    return {"upscaled_masks": masks}

                has_mask_input = self._has_mask_inputs[1]

            elif i == 2:
                # Cascaded Post-refinement-2
                mask_input, masks, _ = _decide_masks(
                    masks,
                    logits,  # noqa: F821 masks are set in the first iteration
                    scores,  # noqa: F821 masks are set in the first iteration
                )
                if masks.sum() == 0:
                    return {"upscaled_masks": masks}

                has_mask_input = self._has_mask_inputs[1]
                y, x = np.nonzero(masks)
                box_coords = self.decoder.apply_coords(
                    np.array(
                        [[x.min(), y.min()], [x.max(), y.max()]],
                        dtype=np.float32,
                    ),
                    original_size,
                )
                box_coords = np.expand_dims(box_coords, axis=0)
                inputs.update(
                    {
                        "point_coords": np.concatenate(
                            (inputs["point_coords"], box_coords),
                            axis=1,
                        ),
                        "point_labels": np.concatenate(
                            (inputs["point_labels"], self._point_labels_box),
                            axis=1,
                        ),
                    },
                )

            inputs.update({"mask_input": mask_input, "has_mask_input": has_mask_input})
            prediction = self.decoder.infer_sync(inputs)
            upscaled_masks, scores, logits = (
                prediction["upscaled_masks"],
                prediction["iou_predictions"],
                prediction["low_res_masks"],
            )
            masks = upscaled_masks > self.decoder.mask_threshold

        _, masks, _ = _decide_masks(masks, logits, scores)
        return {"upscaled_masks": masks}


def _polygon_to_mask(
    polygon: np.ndarray | list[np.ndarray],
    height: int,
    width: int,
) -> np.ndarray:
    """Converts a polygon represented as an array of 2D points into a mask"""
    if isinstance(polygon, np.ndarray) and np.issubdtype(polygon.dtype, np.integer):
        contour = polygon.reshape(-1, 2)
    else:
        contour = [[int(point[0]), int(point[1])] for point in polygon]
    gt_mask = np.zeros((height, width), dtype=np.uint8)
    return cv2.drawContours(gt_mask, np.asarray([contour]), 0, 1, cv2.FILLED)


def _generate_masked_features(
    feats: np.ndarray,
    masks: np.ndarray,
    threshold_mask: float,
    image_size: int = 1024,
) -> np.ndarray | None:
    """Generate masked features.

    Args:
        feats (np.ndarray): Raw reference features. It will be filtered with masks.
        masks (np.ndarray): Reference masks used to filter features.
        threshold_mask (float): Threshold to control masked region.
        image_size (int): Input image size.

    Returns:
        (np.ndarray): Masked features.
    """
    target_shape = image_size / max(masks.shape) * np.array(masks.shape)
    target_shape = target_shape[::-1].astype(np.int32)

    # Post-process masks
    masks = cv2.resize(masks, target_shape, interpolation=cv2.INTER_LINEAR)
    masks = _pad_to_square(masks, image_size)
    masks = cv2.resize(masks, feats.shape[:2][::-1], interpolation=cv2.INTER_LINEAR)

    # Target feature extraction
    if (masks > threshold_mask).sum() == 0:
        # (for stability) there is no area to be extracted
        return None

    masked_feat = feats[masks > threshold_mask]
    masked_feat = masked_feat.mean(0)[None]
    return masked_feat / np.linalg.norm(masked_feat, axis=-1, keepdims=True)


def _pad_to_square(x: np.ndarray, image_size: int = 1024) -> np.ndarray:
    """Pad to a square input.

    Args:
        x (np.ndarray): Mask to be padded.

    Returns:
        (np.ndarray): Padded mask.
    """
    h, w = x.shape[-2:]
    padh = image_size - h
    padw = image_size - w
    return np.pad(x, ((0, padh), (0, padw)), constant_values=0.0)


def _decide_masks(
    masks: np.ndarray,
    logits: np.ndarray,
    scores: np.ndarray,
    is_single: bool = False,
) -> tuple[np.ndarray, np.ndarray, float] | tuple[None, np.ndarray, float]:
    """Post-process logits for resized masks according to best index based on scores."""
    if is_single:
        best_idx = 0
    else:
        # skip the first index components
        scores, masks, logits = (x[:, 1:] for x in (scores, masks, logits))

        # filter zero masks
        while len(scores[0]) > 0 and masks[0, (best_idx := np.argmax(scores[0]))].sum() == 0:
            scores, masks, logits = (
                np.concatenate((x[:, :best_idx], x[:, best_idx + 1 :]), axis=1) for x in (scores, masks, logits)
            )

        if len(scores[0]) == 0:
            # all predicted masks were zero masks, ignore them.
            return (
                None,
                np.zeros(masks.shape[-2:]),
                0.0,
            )

        best_idx = np.argmax(scores[0])
    return (
        logits[:, [best_idx]],
        masks[0, best_idx],
        float(np.clip(scores[0][best_idx], 0, 1)),
    )


def _get_prompt_candidates(
    image_embeddings: np.ndarray,
    reference_feats: np.ndarray,
    used_indices: np.ndarray,
    original_shape: np.ndarray,
    threshold: float = 0.0,
    num_bg_points: int = 1,
    default_threshold_target: float = 0.65,
    image_size: int = 1024,
    downsizing: int = 64,
) -> tuple[dict[int, np.ndarray], dict[int, np.ndarray]]:
    """Get prompt candidates."""
    target_feat = image_embeddings.squeeze()
    c_feat, h_feat, w_feat = target_feat.shape
    target_feat = target_feat / np.linalg.norm(target_feat, axis=0, keepdims=True)
    target_feat = target_feat.reshape(c_feat, h_feat * w_feat)

    total_points_scores: dict[int, np.ndarray] = {}
    total_bg_coords: dict[int, np.ndarray] = {}
    for label in used_indices:
        sim = reference_feats[label] @ target_feat
        sim = sim.reshape(h_feat, w_feat)
        sim = _resize_to_original_shape(sim, image_size, original_shape)

        threshold = (threshold == 0) * default_threshold_target + threshold
        points_scores, bg_coords = _point_selection(
            mask_sim=sim,
            original_shape=original_shape,
            threshold=threshold,
            num_bg_points=num_bg_points,
            image_size=image_size,
            downsizing=downsizing,
        )

        if points_scores is not None:
            total_points_scores[label] = points_scores
            total_bg_coords[label] = bg_coords
    return total_points_scores, total_bg_coords


def _point_selection(
    mask_sim: np.ndarray,
    original_shape: np.ndarray,
    threshold: float = 0.0,
    num_bg_points: int = 1,
    image_size: int = 1024,
    downsizing: int = 64,
) -> tuple[np.ndarray, np.ndarray] | tuple[None, None]:
    """Select point used as point prompts."""
    _, w_sim = mask_sim.shape

    # Top-first point selection
    point_coords = np.where(mask_sim > threshold)
    fg_coords_scores = np.stack(
        point_coords[::-1] + (mask_sim[point_coords],),
        axis=0,
    ).T

    ## skip if there is no point coords
    if len(fg_coords_scores) == 0:
        return None, None

    ratio = image_size / original_shape.max()
    width = (original_shape[1] * ratio).astype(np.int64)
    n_w = width // downsizing

    ## get grid numbers
    idx_grid = fg_coords_scores[:, 1] * ratio // downsizing * n_w + fg_coords_scores[:, 0] * ratio // downsizing
    idx_grid_unique = np.unique(idx_grid.astype(np.int64))

    ## get matched indices
    matched_matrix = np.expand_dims(idx_grid, axis=-1) == idx_grid_unique  # (totalN, uniqueN)

    ## sample fg_coords_scores matched by matched_matrix
    matched_grid = np.expand_dims(fg_coords_scores, axis=1) * np.expand_dims(
        matched_matrix,
        axis=-1,
    )

    ## sample the highest score one of the samples that are in the same grid
    matched_indices = _topk_numpy(matched_grid[..., -1], k=1, axis=0, largest=True)[1][0].astype(np.int64)
    points_scores = matched_grid[matched_indices].diagonal().T

    ## sort by the highest score
    sorted_points_scores_indices = np.flip(
        np.argsort(points_scores[:, -1]),
        axis=-1,
    ).astype(np.int64)
    points_scores = points_scores[sorted_points_scores_indices]

    # Top-last point selection
    bg_indices = _topk_numpy(mask_sim.flatten(), num_bg_points, largest=False)[1]
    bg_x = np.expand_dims(bg_indices // w_sim, axis=0)
    bg_y = bg_indices - bg_x * w_sim
    bg_coords = np.concatenate((bg_y, bg_x), axis=0).transpose(1, 0)
    bg_coords = bg_coords.astype(np.float32)

    return points_scores, bg_coords


def _resize_to_original_shape(
    masks: np.ndarray,
    image_size: int,
    original_shape: np.ndarray,
) -> np.ndarray:
    """Resize feature size to original shape."""
    # resize feature size to input size
    masks = cv2.resize(masks, (image_size, image_size), interpolation=cv2.INTER_LINEAR)

    # remove pad
    prepadded_size = _get_prepadded_size(original_shape, image_size)
    masks = masks[..., : prepadded_size[0], : prepadded_size[1]]

    # resize unpadded one to original shape
    original_shape = original_shape.astype(np.int64)
    h, w = original_shape[0], original_shape[1]
    return cv2.resize(masks, (w, h), interpolation=cv2.INTER_LINEAR)


def _get_prepadded_size(original_shape: np.ndarray, image_size: int) -> np.ndarray:
    """Get pre-padded size."""
    scale = image_size / np.max(original_shape)
    transformed_size = scale * original_shape
    return np.floor(transformed_size + 0.5).astype(np.int64)


def _topk_numpy(
    x: np.ndarray,
    k: int,
    axis: int = -1,
    largest: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    """Top-k function for numpy same with torch.topk."""
    if largest:
        k = -k
        indices = range(k, 0)
    else:
        indices = range(k)
    partitioned_ind = np.argpartition(x, k, axis=axis).take(indices=indices, axis=axis)
    partitioned_scores = np.take_along_axis(x, partitioned_ind, axis=axis)
    sorted_trunc_ind = np.argsort(partitioned_scores, axis=axis)
    if largest:
        sorted_trunc_ind = np.flip(sorted_trunc_ind, axis=axis)
    ind = np.take_along_axis(partitioned_ind, sorted_trunc_ind, axis=axis)
    scores = np.take_along_axis(partitioned_scores, sorted_trunc_ind, axis=axis)
    return scores, ind


def _inspect_overlapping_areas(
    predicted_masks: dict[int, list[np.ndarray]],
    used_points: dict[int, list[np.ndarray]],
    threshold_iou: float = 0.8,
) -> None:
    def _calculate_mask_iou(
        mask1: np.ndarray,
        mask2: np.ndarray,
    ) -> tuple[float, np.ndarray | None]:
        assert mask1.ndim == 2
        assert mask2.ndim == 2
        # Avoid division by zero
        if (union := np.logical_or(mask1, mask2).sum().item()) == 0:
            return 0.0, None
        intersection = np.logical_and(mask1, mask2)
        return intersection.sum().item() / union, intersection

    for (label, masks), (other_label, other_masks) in product(
        predicted_masks.items(),
        predicted_masks.items(),
    ):
        if other_label <= label:
            continue

        overlapped_label = []
        overlapped_other_label = []
        for (im, mask), (jm, other_mask) in product(
            enumerate(masks),
            enumerate(other_masks),
        ):
            _mask_iou, _intersection = _calculate_mask_iou(mask, other_mask)
            if _mask_iou > threshold_iou:
                if used_points[label][im][2] > used_points[other_label][jm][2]:
                    overlapped_other_label.append(jm)
                else:
                    overlapped_label.append(im)
            elif _mask_iou > 0:
                # refine the slightly overlapping region
                overlapped_coords = np.where(_intersection)
                if used_points[label][im][2] > used_points[other_label][jm][2]:
                    other_mask[overlapped_coords] = 0.0
                else:
                    mask[overlapped_coords] = 0.0

        for im in sorted(set(overlapped_label), reverse=True):
            masks.pop(im)
            used_points[label].pop(im)

        for jm in sorted(set(overlapped_other_label), reverse=True):
            other_masks.pop(jm)
            used_points[other_label].pop(jm)
