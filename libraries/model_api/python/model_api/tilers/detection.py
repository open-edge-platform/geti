#
# Copyright (C) 2020-2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

import cv2 as cv
import numpy as np

from model_api.models import DetectionResult
from model_api.models.types import NumericalValue
from model_api.models.utils import multiclass_nms

from .tiler import Tiler


class DetectionTiler(Tiler):
    """Tiler for object detection models.
    This tiler expects model to output a lsit of `Detection` objects
    or one `DetectionResult` object.
    """

    def __init__(self, model, configuration: dict = {}, execution_mode="async"):
        super().__init__(model, configuration, execution_mode)

    @classmethod
    def parameters(cls):
        """Defines the description and type of configurable data parameters for the tiler.

        Returns:
            - the dictionary with defined wrapper tiler parameters
        """
        parameters = super().parameters()
        parameters.update(
            {
                "max_pred_number": NumericalValue(
                    value_type=int,
                    default_value=100,
                    min=1,
                    description="Maximum numbers of prediction per image",
                ),
                "iou_threshold": NumericalValue(
                    value_type=float,
                    default_value=0.45,
                    min=0,
                    max=1.0,
                    description="IoU threshold which is used to apply NMS to bounding boxes",
                ),
            },
        )
        return parameters

    def _postprocess_tile(
        self,
        predictions: DetectionResult,
        coord: list[int],
    ) -> dict:
        """Converts predictions to a format convenient for further merging.

        Args:
            predictions: predictions wrapped in DetectionResult from a detection model
            coord: a list containing coordinates for the processed tile

        Returns:
            a dict with postprocessed predictions in 6-items format: (label id, score, bbox)
        """
        output_dict = {}
        output_dict["saliency_map"] = predictions.saliency_map
        output_dict["features"] = predictions.feature_vector

        if self.execution_mode == "sync":
            output_dict["saliency_map"] = np.copy(output_dict["saliency_map"])
            output_dict["features"] = np.copy(output_dict["features"])

        offset_x, offset_y = coord[:2]
        predictions.bboxes += np.tile((offset_x, offset_y), 2)
        output_dict["bboxes"] = np.concatenate(
            (predictions.labels[:, np.newaxis], predictions.scores[:, np.newaxis], predictions.bboxes),
            -1,
        )
        output_dict["coords"] = coord

        return output_dict

    def _merge_results(self, results: list[dict], shape: tuple[int, int, int]) -> DetectionResult:
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
        for result in results:
            if len(result["bboxes"]):
                detections_array = np.concatenate((detections_array, result["bboxes"]))
            feature_vectors.append(result["features"])
            saliency_maps.append(result["saliency_map"])
            tiles_coords.append(result["coords"])

        if np.prod(detections_array.shape):
            detections_array, _ = multiclass_nms(
                detections_array,
                max_num=self.max_pred_number,  # type: ignore[attr-defined]
                iou_threshold=self.iou_threshold,  # type: ignore[attr-defined]
            )

        merged_vector = np.mean(feature_vectors, axis=0) if feature_vectors else np.ndarray(0)
        saliency_map = self._merge_saliency_maps(saliency_maps, shape, tiles_coords) if saliency_maps else np.ndarray(0)
        label_names = [self.model.labels[int(label_idx)] for label_idx in detections_array[:, 0]]

        return DetectionResult(
            bboxes=detections_array[:, 2:].astype(np.int32),
            labels=detections_array[:, 0].astype(np.int32),
            scores=detections_array[:, 1],
            label_names=label_names,
            saliency_map=saliency_map,
            feature_vector=merged_vector,
        )

    def _merge_saliency_maps(
        self,
        saliency_maps: list[np.ndarray],
        shape: tuple[int, int, int],
        tiles_coords: list[tuple[int, int, int, int]],
    ) -> np.ndarray:
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

        if len(image_saliency_map.shape) == 1 or len(saliency_maps) == 1:
            return image_saliency_map

        recover_shape = False
        if len(image_saliency_map.shape) == 4:
            recover_shape = True
            image_saliency_map = image_saliency_map.squeeze(0)

        num_classes = image_saliency_map.shape[0]
        map_h, map_w = image_saliency_map.shape[1:]

        image_h, image_w, _ = shape
        ratio = (
            map_h / min(image_h, self.tile_size),  # type: ignore[attr-defined]
            map_w
            / min(
                image_w,
                self.tile_size,  # type: ignore[attr-defined]
            ),
        )

        image_map_h = int(image_h * ratio[0])
        image_map_w = int(image_w * ratio[1])
        merged_map = np.zeros((num_classes, image_map_h, image_map_w))

        start_idx = 1 if self.tile_with_full_img else 0  # type: ignore[attr-defined]
        for i, saliency_map in enumerate(saliency_maps[start_idx:], start_idx):
            for class_idx in range(num_classes):
                if len(saliency_map.shape) == 4:
                    saliency_map = saliency_map.squeeze(0)

                cls_map = saliency_map[class_idx]

                x_1, y_1, x_2, y_2 = tiles_coords[i]
                y_1, x_1 = int(y_1 * ratio[0]), int(x_1 * ratio[1])
                y_2, x_2 = int(y_2 * ratio[0]), int(x_2 * ratio[1])

                map_h, map_w = cls_map.shape

                if (map_h > y_2 - y_1 > 0) and (map_w > x_2 - x_1 > 0):
                    cls_map = cv.resize(cls_map, (x_2 - x_1, y_2 - y_1))

                map_h, map_w = y_2 - y_1, x_2 - x_1

                for hi, wi in [(h_, w_) for h_ in range(map_h) for w_ in range(map_w)]:
                    map_pixel = cls_map[hi, wi]
                    merged_pixel = merged_map[class_idx][y_1 + hi, x_1 + wi]
                    if merged_pixel != 0:
                        merged_map[class_idx][y_1 + hi, x_1 + wi] = 0.5 * (map_pixel + merged_pixel)
                    else:
                        merged_map[class_idx][y_1 + hi, x_1 + wi] = map_pixel

        for class_idx in range(num_classes):
            if self.tile_with_full_img:  # type: ignore[attr-defined]
                image_map_cls = image_saliency_map[class_idx]
                image_map_cls = cv.resize(image_map_cls, (image_map_w, image_map_h))
                merged_map[class_idx] += 0.5 * image_map_cls

            merged_map[class_idx] = _non_linear_normalization(merged_map[class_idx])

        if recover_shape:
            merged_map = np.expand_dims(merged_map, 0)

        return merged_map.astype(np.uint8)


def _non_linear_normalization(saliency_map) -> np.ndarray:
    """Use non-linear normalization y=x**1.5 for 2D saliency maps."""
    min_soft_score = np.min(saliency_map)
    # make merged_map distribution positive to perform non-linear normalization y=x**1.5
    saliency_map = (saliency_map - min_soft_score) ** 1.5

    max_soft_score = np.max(saliency_map)
    saliency_map = 255.0 / (max_soft_score + 1e-12) * saliency_map

    return np.floor(saliency_map)
