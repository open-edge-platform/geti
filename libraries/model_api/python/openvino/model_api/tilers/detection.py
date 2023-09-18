"""
 Copyright (c) 2023 Intel Corporation

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

import cv2 as cv
import numpy as np
from openvino.model_api.models.types import NumericalValue
from openvino.model_api.models.utils import Detection, DetectionResult, multiclass_nms

from .tiler import Tiler


class DetectionTiler(Tiler):
    """
    Tiler for object detection models.
    This tiler expects model to output a lsit of `Detection` objects
    or one `DetectionResult` object.
    """

    def __init__(self, model, configuration=dict(), execution_mode="async"):
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
            }
        )
        return parameters

    def _postprocess_tile(self, predictions, coord):
        """Converts predictions to a format convinient for further merging.

        Args:
             predictions: predictions from a detection model: a list of `Detection` objects
             or one `DetectionResult`
             coord: a list containing coordinates for the processed tile

        Returns:
             a dict with postprocessed predictions in 6-items format: (label id, score, bbox)
        """

        output_dict = {}
        if hasattr(predictions, "objects"):
            detections = _detection2array(predictions.objects)
        elif hasattr(predictions, "segmentedObjects"):
            detections = _detection2array(predictions.segmentedObjects)
        else:
            raise RuntimeError("Unsupported model predictions fromat")

        output_dict["saliency_map"] = predictions.saliency_map
        output_dict["features"] = predictions.feature_vector

        if self.execution_mode == "sync":
            output_dict["saliency_map"] = np.copy(output_dict["saliency_map"])
            output_dict["features"] = np.copy(output_dict["features"])

        offset_x, offset_y = coord[:2]
        detections[:, 2:] += np.tile((offset_x, offset_y), 2)
        output_dict["bboxes"] = detections
        output_dict["coords"] = coord

        return output_dict

    def _merge_results(self, results, shape):
        """Merge results from all tiles.

        To merge detections, per-class NMS is applied.

        Args:
             results: list of per-tile results
             shape: original full-res image shape
        Returns:
             merged prediciton
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
                detections_array, max_num=self.max_pred_number
            )

        merged_vector = (
            np.mean(feature_vectors, axis=0) if feature_vectors else np.ndarray(0)
        )
        saliency_map = (
            self._merge_saliency_maps(saliency_maps, shape, tiles_coords)
            if saliency_maps
            else np.ndarray(0)
        )

        detected_objects = []
        for i in range(detections_array.shape[0]):
            label = int(detections_array[i][0])
            score = float(detections_array[i][1])
            bbox = list(detections_array[i][2:].astype(np.int32))
            detected_objects.append(
                Detection(*bbox, score, label, self.model.labels[label])
            )

        return DetectionResult(
            detected_objects,
            saliency_map,
            merged_vector,
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

        if len(image_saliency_map.shape) == 1:
            return image_saliency_map

        recover_shape = False
        if len(image_saliency_map.shape) == 4:
            recover_shape = True
            image_saliency_map = image_saliency_map.squeeze(0)

        num_classes = image_saliency_map.shape[0]
        map_h, map_w = image_saliency_map.shape[1:]

        image_h, image_w, _ = shape
        ratio = map_h / min(image_h, self.tile_size), map_w / min(
            image_w, self.tile_size
        )

        image_map_h = int(image_h * ratio[0])
        image_map_w = int(image_w * ratio[1])
        merged_map = np.zeros((num_classes, image_map_h, image_map_w))

        for i, saliency_map in enumerate(saliency_maps[1:], 1):
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
                        merged_map[class_idx][y_1 + hi, x_1 + wi] = 0.5 * (
                            map_pixel + merged_pixel
                        )
                    else:
                        merged_map[class_idx][y_1 + hi, x_1 + wi] = map_pixel

        for class_idx in range(num_classes):
            image_map_cls = image_saliency_map[class_idx]
            image_map_cls = cv.resize(image_map_cls, (image_map_w, image_map_h))

            merged_map[class_idx] += 0.5 * image_map_cls
            merged_map[class_idx] = _non_linear_normalization(merged_map[class_idx])

        if recover_shape:
            merged_map = np.expand_dims(merged_map, 0)

        return merged_map.astype(np.uint8)


def _non_linear_normalization(saliency_map):
    """Use non-linear normalization y=x**1.5 for 2D saliency maps."""

    min_soft_score = np.min(saliency_map)
    # make merged_map distribution positive to perform non-linear normalization y=x**1.5
    saliency_map = (saliency_map - min_soft_score) ** 1.5

    max_soft_score = np.max(saliency_map)
    saliency_map = 255.0 / (max_soft_score + 1e-12) * saliency_map

    return np.floor(saliency_map)


def _detection2array(detections):
    """Convert list of OpenVINO Detection to a numpy array.

    Args:
        detections (List): List of OpenVINO Detection containing score, id, xmin, ymin, xmax, ymax

    Returns:
        np.ndarray: numpy array with [label, confidence, x1, y1, x2, y2]
    """
    scores = np.empty((0, 1), dtype=np.float32)
    labels = np.empty((0, 1), dtype=np.uint32)
    boxes = np.empty((0, 4), dtype=np.float32)
    for det in detections:
        if (det.xmax - det.xmin) * (det.ymax - det.ymin) < 1.0:
            continue
        scores = np.append(scores, [[det.score]], axis=0)
        labels = np.append(labels, [[det.id]], axis=0)
        boxes = np.append(
            boxes,
            [[float(det.xmin), float(det.ymin), float(det.xmax), float(det.ymax)]],
            axis=0,
        )
    detections = np.concatenate((labels, scores, boxes), -1)
    return detections
