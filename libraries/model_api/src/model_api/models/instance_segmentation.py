#
# Copyright (C) 2020-2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

import cv2
import numpy as np

from model_api.adapters.inference_adapter import InferenceAdapter

from .image_model import ImageModel
from .parameters import ParameterRegistry
from .result import InstanceSegmentationResult
from .utils import ResizeMetadata, calculate_nms, load_labels


class MaskRCNNModel(ImageModel):
    __model__ = "MaskRCNN"

    def __init__(self, inference_adapter: InferenceAdapter, configuration: dict = {}, preload: bool = False) -> None:
        super().__init__(inference_adapter, configuration, preload)
        self._check_io_number((1, 2), (3, 4, 5, 6, 8))

        if self.params.path_to_labels:
            self._labels = load_labels(self.params.path_to_labels)
        self.is_segmentoly = len(self.inputs) == 2
        self.output_blob_name = self._get_outputs()

    @classmethod
    def parameters(cls) -> dict:
        parameters = super().parameters()
        parameters.update(
            ParameterRegistry.merge(
                ParameterRegistry.CONFIDENCE_THRESHOLD,
                ParameterRegistry.LABELS,
                ParameterRegistry.INSTANCE_SEGMENTATION,
                ParameterRegistry.NMS,
            ),
        )
        return parameters

    def _get_outputs(self) -> dict:  # noqa: C901 TODO: Fix this method to reduce complexity
        if self.is_segmentoly:
            return self._get_segmentoly_outputs()
        filtered_names = []
        for name, output in self.outputs.items():
            if _saliency_map_name not in output.names and _feature_vector_name not in output.names:
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
        return self.raise_error(f"Unexpected outputs: {self.outputs}")

    def _get_segmentoly_outputs(self) -> dict:
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
                    f"Unexpected output layer shape {layer_shape} with name {layer_name}",
                )
        return outputs

    def preprocess(self, dict_inputs: dict, meta: dict) -> tuple[dict, dict]:
        input_image_size = meta["resized_shape"][:2]
        if self.is_segmentoly:
            assert len(self.image_info_blob_names) == 1
            input_image_info = np.asarray(
                [[input_image_size[0], input_image_size[1], 1]],
                dtype=np.float32,
            )
            dict_inputs[self.image_info_blob_names[0]] = input_image_info
        return dict_inputs, meta

    def postprocess(self, outputs: dict, meta: dict) -> InstanceSegmentationResult:
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

        inputImgWidth, inputImgHeight = (
            meta["original_shape"][1],
            meta["original_shape"][0],
        )
        resize_meta = ResizeMetadata.compute(
            original_width=inputImgWidth,
            original_height=inputImgHeight,
            model_width=self.orig_width,
            model_height=self.orig_height,
            resize_type=self.params.resize_type,
        )

        boxes -= (resize_meta.pad_left, resize_meta.pad_top, resize_meta.pad_left, resize_meta.pad_top)
        boxes *= (
            resize_meta.inverted_scale_x,
            resize_meta.inverted_scale_y,
            resize_meta.inverted_scale_x,
            resize_meta.inverted_scale_y,
        )
        np.around(boxes, out=boxes)
        np.clip(
            boxes,
            0.0,
            [inputImgWidth, inputImgHeight, inputImgWidth, inputImgHeight],
            out=boxes,
        )

        has_feature_vector_name = _feature_vector_name in self.outputs
        labels_list = self.params.labels
        if has_feature_vector_name:
            if not labels_list:
                self.raise_error("Can't get number of classes because labels are empty")
            saliency_maps: list = [[] for _ in range(len(labels_list))]
        else:
            saliency_maps = []

        # Apply confidence threshold, bounding box area filter and label index filter.
        # Calculate box areas safely to avoid overflow
        box_widths = np.clip(boxes[:, 2] - boxes[:, 0], 0, None)
        box_heights = np.clip(boxes[:, 3] - boxes[:, 1], 0, None)

        # Use float64 for area calculation to prevent overflow, then check if area > 1
        box_areas = box_widths.astype(np.float64) * box_heights.astype(np.float64)

        keep = (scores > self.params.confidence_threshold) & (box_areas > 1)

        if labels_list:
            keep &= labels < len(labels_list)

        boxes = boxes[keep].astype(np.int32)
        scores = scores[keep]
        labels = labels[keep]
        masks = masks[keep]

        keep_nms = calculate_nms(
            boxes=boxes,
            scores=scores,
            labels=labels,
            execute_nms=self.params.nms_execute,
            agnostic_nms=self.params.agnostic_nms,
            iou_threshold=self.params.iou_threshold,
            max_predictions=self.params.nms_max_predictions,
        )

        boxes = boxes[keep_nms]
        scores = scores[keep_nms]
        labels = labels[keep_nms]
        masks = masks[keep_nms]

        resized_masks, label_names = [], []
        for box, label_idx, raw_mask in zip(boxes, labels, masks):
            if labels_list:
                label_names.append(labels_list[label_idx])

            raw_cls_mask = raw_mask[label_idx, ...] if self.is_segmentoly else raw_mask
            if self.params.postprocess_semantic_masks or has_feature_vector_name:
                resized_mask = _segm_postprocess(
                    box,
                    raw_cls_mask,
                    *meta["original_shape"][:-1],
                )
            else:
                resized_mask = raw_cls_mask

            output_mask = resized_mask if self.params.postprocess_semantic_masks else raw_cls_mask
            resized_masks.append(output_mask)
            if has_feature_vector_name:
                saliency_maps[label_idx - 1].append(resized_mask)

        _masks = np.stack(resized_masks) if len(resized_masks) > 0 else np.empty((0, 16, 16), dtype=np.uint8)
        return InstanceSegmentationResult(
            bboxes=boxes,
            labels=labels,
            scores=scores,
            masks=_masks,
            label_names=label_names or None,
            saliency_map=_average_and_normalize(saliency_maps),
            feature_vector=outputs.get(_feature_vector_name, np.ndarray(0)),
        )


def _average_and_normalize(saliency_maps: list) -> list:
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


def _expand_box(box: np.ndarray, scale: float) -> np.ndarray:
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


def _segm_postprocess(box: np.ndarray, raw_cls_mask: np.ndarray, im_h: int, im_w: int) -> np.ndarray:
    # Add zero border to prevent upsampling artifacts on segment borders.
    raw_cls_mask = np.pad(raw_cls_mask, ((1, 1), (1, 1)), "constant", constant_values=0)
    extended_box = _expand_box(
        box,
        raw_cls_mask.shape[0] / (raw_cls_mask.shape[0] - 2.0),
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


_saliency_map_name = "saliency_map"
_feature_vector_name = "feature_vector"


def _append_xai_names(outputs: dict, output_names: dict) -> None:
    if _saliency_map_name in outputs:
        output_names["saliency_map"] = _saliency_map_name
    if _feature_vector_name in outputs:
        output_names["feature_vector"] = _feature_vector_name
