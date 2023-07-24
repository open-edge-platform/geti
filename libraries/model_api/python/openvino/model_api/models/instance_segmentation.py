"""
 Copyright (c) 2020-2023 Intel Corporation

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

import cv2
import numpy as np

from .image_model import ImageModel
from .types import BooleanValue, ListValue, NumericalValue, StringValue
from .utils import InstanceSegmentationResult, SegmentedObject, load_labels, nms


class MaskRCNNModel(ImageModel):
    __model__ = "MaskRCNN"

    def __init__(self, inference_adapter, configuration=dict(), preload=False):
        super().__init__(inference_adapter, configuration, preload)
        self._check_io_number((1, 2), (3, 4, 5, 6, 8))
        if self.path_to_labels:
            self.labels = load_labels(self.path_to_labels)
        self.is_segmentoly = len(self.inputs) == 2
        self.output_blob_name = self._get_outputs()

    @classmethod
    def parameters(cls):
        parameters = super().parameters()
        parameters.update(
            {
                "confidence_threshold": NumericalValue(
                    default_value=0.5,
                    description="Probability threshold value for bounding box filtering",
                ),
                "labels": ListValue(description="List of class labels"),
                "path_to_labels": StringValue(
                    description="Path to file with labels. Overrides the labels, if they sets via `labels` parameter"
                ),
                "postprocess_semantic_masks": BooleanValue(
                    description="Resize and apply 0.5 threshold to instance segmentation masks",
                    default_value=True,
                ),
            }
        )
        return parameters

    def _get_outputs(self):
        if self.is_segmentoly:
            return self._get_segmentoly_outputs()
        filtered_names = []
        for name, output in self.outputs.items():
            if (
                _saliency_map_name not in output.names
                and _feature_vector_name not in output.names
            ):
                filtered_names.append(name)
        outputs = {}
        for layer_name in filtered_names:
            if layer_name.startswith("TopK"):
                continue
            layer_shape = self.outputs[layer_name].shape

            if len(layer_shape) == 1:
                outputs["labels"] = layer_name
            elif len(layer_shape) == 2:
                outputs["boxes"] = layer_name
            elif len(layer_shape) == 3:
                outputs["masks"] = layer_name
        if len(outputs) == 3:
            _append_xai_names(self.outputs, outputs)
            return outputs
        outputs = {}
        for layer_name in filtered_names:
            if layer_name.startswith("TopK"):
                continue
            layer_shape = self.outputs[layer_name].shape

            if len(layer_shape) == 2:
                outputs["labels"] = layer_name
            elif len(layer_shape) == 3:
                outputs["boxes"] = layer_name
            elif len(layer_shape) == 4:
                outputs["masks"] = layer_name
        if len(outputs) == 3:
            _append_xai_names(self.outputs, outputs)
            return outputs
        self.raise_error(f"Unexpected outputs: {self.outputs}")

    def _get_segmentoly_outputs(self):
        outputs = {}
        for layer_name in self.outputs:
            layer_shape = self.outputs[layer_name].shape
            if layer_name == "boxes" and len(layer_shape) == 2:
                outputs["boxes"] = layer_name
            elif layer_name == "classes" and len(layer_shape) == 1:
                outputs["labels"] = layer_name
            elif layer_name == "scores" and len(layer_shape) == 1:
                outputs["scores"] = layer_name
            elif layer_name == "raw_masks" and len(layer_shape) == 4:
                outputs["masks"] = layer_name
            else:
                self.raise_error(
                    "Unexpected output layer shape {} with name {}".format(
                        layer_shape, layer_name
                    )
                )
        return outputs

    def preprocess(self, inputs):
        dict_inputs, meta = super().preprocess(inputs)
        input_image_size = meta["resized_shape"][:2]
        if self.is_segmentoly:
            assert len(self.image_info_blob_names) == 1
            input_image_info = np.asarray(
                [[input_image_size[0], input_image_size[1], 1]], dtype=np.float32
            )
            dict_inputs[self.image_info_blob_names[0]] = input_image_info
        return dict_inputs, meta

    def postprocess(self, outputs, meta):
        if (
            outputs[self.output_blob_name["labels"]].ndim == 2
            and outputs[self.output_blob_name["boxes"]].ndim == 3
            and outputs[self.output_blob_name["masks"]].ndim == 4
        ):
            (
                outputs[self.output_blob_name["labels"]],
                outputs[self.output_blob_name["boxes"]],
                outputs[self.output_blob_name["masks"]],
            ) = (
                outputs[self.output_blob_name["labels"]][0],
                outputs[self.output_blob_name["boxes"]][0],
                outputs[self.output_blob_name["masks"]][0],
            )
        boxes = (
            outputs[self.output_blob_name["boxes"]]
            if self.is_segmentoly
            else outputs[self.output_blob_name["boxes"]][:, :4]
        )
        scores = (
            outputs[self.output_blob_name["scores"]]
            if self.is_segmentoly
            else outputs[self.output_blob_name["boxes"]][:, 4]
        )
        labels = outputs[self.output_blob_name["labels"]]
        masks = outputs[self.output_blob_name["masks"]]
        if not self.is_segmentoly:
            labels += 1
        if self.labels is None:
            str_labels = (f"#{label}" for label in labels)
        else:
            str_labels = (self.labels[label] for label in labels)

        inputImgWidth, inputImgHeight = (
            meta["original_shape"][1],
            meta["original_shape"][0],
        )
        invertedScaleX, invertedScaleY = (
            inputImgWidth / self.orig_width,
            inputImgHeight / self.orig_height,
        )
        padLeft, padTop = 0, 0
        if (
            "fit_to_window" == self.resize_type
            or "fit_to_window_letterbox" == self.resize_type
        ):
            invertedScaleX = invertedScaleY = max(invertedScaleX, invertedScaleY)
            if "fit_to_window_letterbox" == self.resize_type:
                padLeft = (self.orig_width - round(inputImgWidth / invertedScaleX)) // 2
                padTop = (
                    self.orig_height - round(inputImgHeight / invertedScaleY)
                ) // 2

        boxes -= (padLeft, padTop, padLeft, padTop)
        boxes *= (invertedScaleX, invertedScaleY, invertedScaleX, invertedScaleY)
        np.around(boxes, out=boxes)
        np.clip(
            boxes,
            0.0,
            [inputImgWidth, inputImgHeight, inputImgWidth, inputImgHeight],
            out=boxes,
        )

        objects = []
        has_feature_vector_name = _feature_vector_name in self.outputs
        if has_feature_vector_name:
            if not self.labels:
                self.raise_error("Can't get number of classes because labels are empty")
            saliency_maps = [[] for _ in range(len(self.labels))]
        else:
            saliency_maps = []
        for box, confidence, cls, str_label, raw_mask in zip(
            boxes, scores, labels, str_labels, masks
        ):
            if confidence <= self.confidence_threshold and not has_feature_vector_name:
                continue
            raw_cls_mask = raw_mask[cls, ...] if self.is_segmentoly else raw_mask
            if self.postprocess_semantic_masks or has_feature_vector_name:
                resized_mask = _segm_postprocess(
                    box, raw_cls_mask, *meta["original_shape"][:-1]
                )
            else:
                resized_mask = raw_cls_mask
            if confidence > self.confidence_threshold:
                output_mask = (
                    resized_mask if self.postprocess_semantic_masks else raw_cls_mask
                )
                objects.append(
                    SegmentedObject(
                        *box.astype(int), confidence, cls, str_label, output_mask
                    )
                )
            if has_feature_vector_name:
                if confidence > self.confidence_threshold:
                    saliency_maps[cls - 1].append(resized_mask)
        return InstanceSegmentationResult(
            objects,
            _average_and_normalize(saliency_maps),
            outputs.get(_feature_vector_name, np.ndarray(0)),
        )


def _average_and_normalize(saliency_maps):
    aggregated = []
    for per_object_maps in saliency_maps:
        if per_object_maps:
            saliency_map = np.max(np.array(per_object_maps), axis=0)
            max_values = np.max(saliency_map)
            saliency_map = 255 * (saliency_map) / (max_values + 1e-12)
            aggregated.append(np.round(saliency_map).astype(np.uint8))
        else:
            aggregated.append(np.ndarray(0))
    return aggregated


def _expand_box(box, scale):
    w_half = (box[2] - box[0]) * 0.5 * scale
    h_half = (box[3] - box[1]) * 0.5 * scale
    x_c = (box[2] + box[0]) * 0.5
    y_c = (box[3] + box[1]) * 0.5
    box_exp = np.zeros(box.shape)
    box_exp[0] = x_c - w_half
    box_exp[2] = x_c + w_half
    box_exp[1] = y_c - h_half
    box_exp[3] = y_c + h_half
    return box_exp


def _segm_postprocess(box, raw_cls_mask, im_h, im_w):
    # Add zero border to prevent upsampling artifacts on segment borders.
    raw_cls_mask = np.pad(raw_cls_mask, ((1, 1), (1, 1)), "constant", constant_values=0)
    extended_box = _expand_box(
        box, raw_cls_mask.shape[0] / (raw_cls_mask.shape[0] - 2.0)
    ).astype(int)
    w, h = np.maximum(extended_box[2:] - extended_box[:2] + 1, 1)
    x0, y0 = np.clip(extended_box[:2], a_min=0, a_max=[im_w, im_h])
    x1, y1 = np.clip(extended_box[2:] + 1, a_min=0, a_max=[im_w, im_h])

    raw_cls_mask = cv2.resize(raw_cls_mask.astype(np.float32), (w, h)) > 0.5
    mask = raw_cls_mask.astype(np.uint8)
    # Put an object mask in an image mask.
    im_mask = np.zeros((im_h, im_w), dtype=np.uint8)
    im_mask[y0:y1, x0:x1] = mask[
        (y0 - extended_box[1]) : (y1 - extended_box[1]),
        (x0 - extended_box[0]) : (x1 - extended_box[0]),
    ]
    return im_mask


class YolactModel(ImageModel):
    __model__ = "Yolact"

    def __init__(self, inference_adapter, configuration, preload=False):
        super().__init__(inference_adapter, configuration, preload)
        if self.path_to_labels:
            self.labels = load_labels(self.path_to_labels)
        self._check_io_number(1, 4)
        self.output_blob_name = self._get_outputs()

    @classmethod
    def parameters(cls):
        parameters = super().parameters()
        parameters.update(
            {
                "confidence_threshold": NumericalValue(
                    default_value=0.5,
                    description="Probability threshold for detections filtering",
                ),
                "labels": ListValue(description="List of class labels"),
                "path_to_labels": StringValue(
                    description="Path to file with labels. Overrides the labels"
                ),
            }
        )
        return parameters

    def _get_outputs(self):
        outputs = {}
        for layer_name in self.outputs:
            layer_shape = self.outputs[layer_name].shape
            if layer_name == "boxes" and len(layer_shape) == 3:
                outputs["boxes"] = layer_name
            elif layer_name == "conf" and len(layer_shape) == 3:
                outputs["conf"] = layer_name
            elif layer_name == "proto" and len(layer_shape) == 4:
                outputs["proto"] = layer_name
            elif layer_name == "mask" and len(layer_shape) == 3:
                outputs["masks"] = layer_name
            else:
                self.raise_error(
                    "Unexpected output layer shape {} with name {}".format(
                        layer_shape, layer_name
                    )
                )
        return outputs

    def postprocess(self, outputs, meta):
        frame_height, frame_width = meta["original_shape"][:-1]
        input_height, input_width = meta["resized_shape"][:-1]
        scale_x = meta["resized_shape"][1] / meta["original_shape"][1]
        scale_y = meta["resized_shape"][0] / meta["original_shape"][0]

        boxes = outputs["boxes"][0]
        conf = np.transpose(outputs["conf"][0])
        masks = outputs["mask"][0]
        proto = outputs["proto"][0]
        num_classes = conf.shape[0]
        idx_lst, cls_lst, scr_lst = [], [], []
        shift_x = (input_width - (frame_width * scale_x)) / frame_width
        shift_y = (input_height - (frame_height * scale_y)) / frame_height

        for cls in range(1, num_classes):
            cls_scores = conf[cls, :]
            idx = np.arange(cls_scores.shape[0])
            conf_mask = cls_scores > self.confidence_threshold

            cls_scores = cls_scores[conf_mask]
            idx = idx[conf_mask]

            if cls_scores.shape[0] == 0:
                continue
            x1, x2 = self._sanitize_coordinates(
                boxes[idx, 0], boxes[idx, 2], frame_width
            )
            y1, y2 = self._sanitize_coordinates(
                boxes[idx, 1], boxes[idx, 3], frame_height
            )
            keep = nms(x1, y1, x2, y2, cls_scores, 0.5)

            idx_lst.append(idx[keep])
            cls_lst.append(np.full(len(keep), cls))
            scr_lst.append(cls_scores[keep])

        if not idx_lst:
            return np.array([]), np.array([]), np.array([]), np.array([])
        idx = np.concatenate(idx_lst, axis=0)
        classes = np.concatenate(cls_lst, axis=0)
        scores = np.concatenate(scr_lst, axis=0)

        idx2 = np.argsort(scores, axis=0)[::-1]
        scores = scores[idx2]

        idx = idx[idx2]
        classes = classes[idx2]

        boxes = boxes[idx]
        masks = masks[idx]
        if np.size(boxes) > 0:
            boxes, scores, classes, masks = self._segm_postprocess(
                boxes,
                masks,
                scores,
                classes,
                proto,
                frame_width,
                frame_height,
                shift_x=shift_x,
                shift_y=shift_y,
            )
        return scores, classes, boxes, masks

    def _segm_postprocess(
        self, boxes, masks, score, classes, proto_data, w, h, shift_x=0, shift_y=0
    ):
        if self.confidence_threshold > 0:
            keep = score > self.confidence_threshold
            score = score[keep]
            boxes = boxes[keep]
            masks = masks[keep]
            classes = classes[keep]
            if np.size(score) == 0:
                return [] * 4

        masks = proto_data @ masks.T
        masks = 1 / (1 + np.exp(-masks))
        masks = self._crop_mask(masks, boxes)

        masks = np.transpose(masks, (2, 0, 1))
        boxes[:, 0], boxes[:, 2] = self._sanitize_coordinates(
            boxes[:, 0], boxes[:, 2], w, shift_x
        )
        boxes[:, 1], boxes[:, 3] = self._sanitize_coordinates(
            boxes[:, 1], boxes[:, 3], h, shift_y
        )
        ready_masks = []

        for mask in masks:
            mask = cv2.resize(mask, (w, h), cv2.INTER_LINEAR)
            mask = mask > 0.5
            ready_masks.append(mask.astype(np.uint8))

        return boxes, score, classes, ready_masks

    def _crop_mask(self, masks, boxes, padding: int = 1):
        h, w, n = np.shape(masks)
        x1, x2 = self._sanitize_coordinates(
            boxes[:, 0], boxes[:, 2], w, padding=padding
        )
        y1, y2 = self._sanitize_coordinates(
            boxes[:, 1], boxes[:, 3], h, padding=padding
        )

        rows = np.reshape(
            np.repeat(
                np.reshape(np.repeat(np.arange(w, dtype=x1.dtype), h), (w, h)),
                n,
                axis=-1,
            ),
            (h, w, n),
        )
        cols = np.reshape(
            np.repeat(
                np.reshape(np.repeat(np.arange(h, dtype=x1.dtype), h), (w, h)),
                n,
                axis=-1,
            ),
            (h, w, n),
        )
        rows = np.transpose(rows, (1, 0, 2))

        masks_left = rows >= x1
        masks_right = rows < x2
        masks_up = cols >= y1
        masks_down = cols < y2
        crop_mask = masks_left * masks_right * masks_up * masks_down
        return masks * crop_mask

    @staticmethod
    def _sanitize_coordinates(_x1, _x2, img_size, shift=0, padding=0):
        _x1 = (_x1 + shift / 2) * img_size
        _x2 = (_x2 + shift / 2) * img_size
        x1 = np.clip(_x1 - padding, 0, img_size)
        x2 = np.clip(_x2 + padding, 0, img_size)
        return x1, x2


_saliency_map_name = "saliency_map"
_feature_vector_name = "feature_vector"


def _append_xai_names(outputs, output_names):
    if _saliency_map_name in outputs:
        output_names["saliency_map"] = _saliency_map_name
    if _feature_vector_name in outputs:
        output_names["feature_vector"] = _feature_vector_name
