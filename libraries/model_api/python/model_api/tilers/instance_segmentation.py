#
# Copyright (C) 2020-2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

from contextlib import contextmanager

import cv2 as cv
import numpy as np

from model_api.models import InstanceSegmentationResult
from model_api.models.instance_segmentation import MaskRCNNModel, _segm_postprocess
from model_api.models.utils import multiclass_nms

from .detection import DetectionTiler


class InstanceSegmentationTiler(DetectionTiler):
    """Tiler for object instance segmentation models.
    This tiler expects model to output a list of `SegmentedObject` objects.

    In addition, this tiler allows to use a tile classifier model,
    which predicts objectness score for each tile. Later, tiles can
    be filtered by this score.
    """

    def __init__(
        self,
        model,
        configuration: dict = {},
        execution_mode="async",
        tile_classifier_model=None,
    ):
        """Constructor for creating a semantic segmentation tiling pipeline

        Args:
            model: underlying model
            configuration: it contains values for parameters accepted by specific
            tiler (`tile_size`, `tiles_overlap` etc.) which are set as data attributes.
            execution_mode: Controls inference mode of the tiler (`async` or `sync`).
            tile_classifier_model: an `ImageModel`, which has "tile_prob" output.
        """
        super().__init__(model, configuration, execution_mode)
        self.tile_classifier_model = tile_classifier_model

    def _filter_tiles(self, image, tile_coords, confidence_threshold=0.35):
        """Filter tiles by objectness score provided by tile classifier

        Args:
             image: full size image
             tile_coords: tile coordinates

        Returns:
             tile coordinates to keep
        """
        if self.tile_classifier_model is not None:
            keep_coords = []
            for i, coord in enumerate(tile_coords):
                tile_img = self._crop_tile(image, coord)
                tile_dict, _ = self.model.preprocess(tile_img)
                cls_outputs = self.tile_classifier_model.infer_sync(tile_dict)
                if i == 0 or cls_outputs["tile_prob"] > confidence_threshold:
                    keep_coords.append(coord)
            return keep_coords

        return tile_coords

    def _postprocess_tile(self, predictions: InstanceSegmentationResult, coord) -> dict:  # type: ignore[override]
        """Converts predictions to a format convenient for further merging.

        Args:
             predictions: predictions from an instance segmentation model: a list of `SegmentedObject` objects
             coord: a list containing coordinates for the processed tile

        Returns:
             a dict with postprocessed detections in 6-items format: (label id, score, bbox) and masks
        """
        output_dict = super()._postprocess_tile(predictions, coord)
        output_dict["masks"] = []
        for mask in predictions.masks:
            output_dict["masks"].append(mask)

        return output_dict

    def _merge_results(self, results, shape) -> InstanceSegmentationResult:
        """Merge results from all tiles.

        To merge detections, per-class NMS is applied.

        Args:
            results: list of per-tile results
            shape: original full-res image shape
        Returns:
            merged prediction
        """
        detections_array = np.empty((0, 6), dtype=np.float32)
        feature_vectors = []
        saliency_maps = []
        tiles_coords = []
        masks = []
        for result in results:
            if len(result["bboxes"]):
                detections_array = np.concatenate((detections_array, result["bboxes"]))
            feature_vectors.append(result["features"])
            saliency_maps.append(result["saliency_map"])
            tiles_coords.append(result["coords"])
            if len(result["masks"]):
                masks.extend(result["masks"])

        keep_idxs = []
        if np.prod(detections_array.shape):
            detections_array, keep_idxs = multiclass_nms(
                detections_array,
                max_num=self.max_pred_number,  # type: ignore[attr-defined]
                iou_threshold=self.iou_threshold,  # type: ignore[attr-defined]
            )
        masks = [masks[keep_idx] for keep_idx in keep_idxs]

        merged_vector = np.mean(feature_vectors, axis=0) if feature_vectors else np.ndarray(0)
        saliency_map = self._merge_saliency_maps(saliency_maps, shape, tiles_coords) if saliency_maps else []

        labels, scores, bboxes = np.hsplit(detections_array, [1, 2])
        labels = labels.astype(np.int32)
        resized_masks, label_names = [], []
        for mask, box, label_idx in zip(masks, bboxes, labels):
            label_names.append(self.model.labels[int(label_idx)])
            resized_masks.append(_segm_postprocess(box, mask, *shape[:-1]))

        resized_masks = np.stack(resized_masks) if resized_masks else masks
        return InstanceSegmentationResult(
            bboxes=np.round(bboxes).astype(np.int32),
            labels=labels.squeeze(),
            scores=scores.squeeze(),
            masks=resized_masks,
            label_names=label_names or None,
            saliency_map=saliency_map,
            feature_vector=merged_vector,
        )

    def _merge_saliency_maps(self, saliency_maps, shape, tiles_coords):
        """Merged saliency maps from each tile

        Args:
            saliency_maps: list of saliency maps, shape of each map is (Nc, H, W)
            shape: shape of the original image
            tiles_coords: coordinates of tiles

        Returns:
            Merged saliency map with shape (Nc, H, W)
        """
        if not saliency_maps:
            return None

        image_saliency_map = saliency_maps[0]

        if not image_saliency_map:
            return image_saliency_map

        num_classes = len(image_saliency_map)
        image_h, image_w, _ = shape

        merged_map = [np.zeros((image_h, image_w)) for _ in range(num_classes)]

        start_idx = 1 if self.tile_with_full_img else 0
        for i, saliency_map in enumerate(saliency_maps[start_idx:], start_idx):
            for class_idx in range(num_classes):
                cls_map = saliency_map[class_idx]
                if len(cls_map.shape) < 2:
                    continue

                x_1, y_1, x_2, y_2 = tiles_coords[i]
                cls_map = cv.resize(cls_map, (x_2 - x_1, y_2 - y_1))

                tile_map = merged_map[class_idx][y_1:y_2, x_1:x_2]
                merged_map[class_idx][y_1:y_2, x_1:x_2] = np.maximum(tile_map, cls_map)

        for class_idx in range(num_classes):
            image_map_cls = image_saliency_map[class_idx] if self.tile_with_full_img else np.ndarray(0)
            if len(image_map_cls.shape) < 2:
                merged_map[class_idx] = np.round(merged_map[class_idx]).astype(np.uint8)
                if np.sum(merged_map[class_idx]) == 0:
                    merged_map[class_idx] = np.ndarray(0)
            else:
                image_map_cls = cv.resize(image_map_cls, (image_w, image_h))
                merged_map[class_idx] = np.maximum(merged_map[class_idx], image_map_cls)
                merged_map[class_idx] = np.round(merged_map[class_idx]).astype(np.uint8)

        return merged_map

    def __call__(self, inputs):
        @contextmanager
        def setup_maskrcnn(*args, **kwds):
            postprocess_state = None
            if isinstance(self.model, MaskRCNNModel):
                postprocess_state = self.model.postprocess_semantic_masks
                self.model.postprocess_semantic_masks = False
            try:
                yield
            finally:
                if isinstance(self.model, MaskRCNNModel):
                    self.model.postprocess_semantic_masks = postprocess_state

        with setup_maskrcnn():
            return super().__call__(inputs)
