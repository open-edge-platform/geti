# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Object detection wrapper."""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, ClassVar

import torch
from torchvision import tv_tensors
from torchvision.ops import box_convert

from getitune.backend.huggingface._deps import ModelOutput, transformers
from getitune.backend.huggingface.data.geometry import reproject_boxes_to_input_space
from getitune.backend.huggingface.exporter.native import HFModelExporter
from getitune.backend.huggingface.models.base import HFModel
from getitune.data.entity.sample import PredictionBatch
from getitune.metrics.mean_ap import MeanAPCallable
from getitune.types.export import TaskLevelExportParameters
from getitune.types.task import TaskType

if TYPE_CHECKING:
    from torchmetrics import Metric, MetricCollection

    from getitune.backend.lightning.exporter.base import ModelExporter
    from getitune.data.entity.sample import SampleBatch

__all__ = ["HFDetectionModel"]


class HFDetectionModel(HFModel):
    """Detection wrapper covering the DETR family.

    Covers RT-DETRv2, RT-DETR, D-FINE, Deformable/Conditional/DAB-DETR and
    similar models that take ``pixel_values`` and return
    ``{loss, logits, pred_boxes}``.
    """

    task: ClassVar[TaskType] = TaskType.DETECTION
    hf_auto_class: ClassVar[type] = transformers.AutoModelForObjectDetection
    export_model_type: ClassVar[str] = "ssd"
    label_keys: ClassVar[tuple[str, ...]] = ("labels",)

    @property
    def _export_parameters(self) -> TaskLevelExportParameters:
        return super()._export_parameters.wrap(
            model_type=self.export_model_type,
            task_type="detection",
            confidence_threshold=0.25,
            iou_threshold=0.5,
        )

    def build_targets(self, batch: SampleBatch) -> dict[str, Any]:
        """Convert Geti's absolute-xyxy boxes into normalized cxcywh.

        Geti stores boxes as absolute-pixel xyxy; ``transformers`` detection
        models expect cxcywh normalized by the model's input size. That size
        is just ``batch.images.shape[-2:]`` — Geti has already resized and
        padded the image by the time it reaches here.
        """
        images = batch.images
        if not isinstance(images, torch.Tensor) or batch.bboxes is None or batch.labels is None:
            msg = "Detection batches need stacked images, bboxes, and labels."
            raise ValueError(msg)
        _, _, h, w = images.shape
        labels = []
        for boxes, class_labels in zip(batch.bboxes, batch.labels, strict=True):
            xyxy = boxes.as_subclass(torch.Tensor).float()
            if xyxy.numel():
                x1, y1, x2, y2 = xyxy.unbind(-1)
                cxcywh = torch.stack(
                    [(x1 + x2) / 2 / w, (y1 + y2) / 2 / h, (x2 - x1) / w, (y2 - y1) / h],
                    dim=-1,
                )
            else:
                cxcywh = xyxy.new_zeros((0, 4))
            labels.append({"class_labels": class_labels.long(), "boxes": cxcywh})
        return {"pixel_values": batch.images, "labels": labels}

    @cached_property
    def _image_processor(self) -> transformers.RTDetrImageProcessor:
        """The post-processing math is stateless and shared across the DETR family.

        ``RTDetrImageProcessor`` works correctly for every model in this
        wrapper's scope, not just RT-DETR: its ``use_focal_loss`` argument
        selects between the sigmoid/top-k convention RT-DETR and D-FINE use
        and the softmax/background-class convention plain DETR and
        Deformable-DETR use (G3), and it only ever reads ``outputs.logits``
        and ``outputs.pred_boxes``, which every model here provides. So one
        processor instance, built once, is enough for the whole family.
        """
        return transformers.RTDetrImageProcessor()

    def postprocess(self, outputs: ModelOutput, batch: SampleBatch) -> PredictionBatch:
        """Decode raw outputs into boxes, scores, and labels in the model's input space.

        Every image in *batch* was resized to the same input canvas, so
        keeping predictions in that shared space (rather than rescaling each
        one back to its own original size) is what lets ``to_metric_inputs``
        compare them against ground truth with a single reprojection instead
        of two. Returns every query with no confidence filtering — thresholding
        for user-facing predictions happens in ``HFEngine.predict()``, not here,
        so this same method can also feed ``to_metric_inputs`` for mAP, which
        needs the full unfiltered score distribution.
        """
        input_size = batch.images.shape[-2:]
        use_focal_loss = getattr(self.hf_model.config, "use_focal_loss", False)
        decoded = self._image_processor.post_process_object_detection(
            outputs,
            threshold=0.0,
            target_sizes=[input_size] * batch.images.shape[0],
            use_focal_loss=use_focal_loss,
        )

        canvas_size = (int(input_size[0]), int(input_size[1]))
        bboxes = [
            tv_tensors.BoundingBoxes(  # pyrefly: ignore[no-matching-overload]
                image_result["boxes"], format=tv_tensors.BoundingBoxFormat.XYXY, canvas_size=canvas_size
            )
            for image_result in decoded
        ]
        return PredictionBatch(
            images=batch.images,
            imgs_info=batch.imgs_info,
            bboxes=bboxes,
            labels=[image_result["labels"] for image_result in decoded],
            scores=[image_result["scores"] for image_result in decoded],
        )

    def to_metric_inputs(self, outputs: ModelOutput, batch: SampleBatch) -> dict[str, Any]:
        """Build the ``preds``/``target`` lists ``MeanAPCallable`` expects.

        Ground truth stays in original image coordinates (``resize_targets:
        false``), so it is reprojected into the same input-space canvas the
        predictions from ``postprocess`` already live in (G12).
        """
        if batch.bboxes is None or batch.labels is None or batch.imgs_info is None:
            msg = "Detection batches need bboxes, labels, and imgs_info to compute metrics."
            raise ValueError(msg)

        predictions = self.postprocess(outputs, batch)
        if predictions.bboxes is None or predictions.scores is None or predictions.labels is None:
            msg = "Detection postprocess() must always populate bboxes, scores, and labels."
            raise ValueError(msg)

        preds = [
            {"boxes": boxes.as_subclass(torch.Tensor), "scores": scores, "labels": labels}
            for boxes, scores, labels in zip(predictions.bboxes, predictions.scores, predictions.labels, strict=True)
        ]
        target = [
            {
                "boxes": reproject_boxes_to_input_space(boxes.as_subclass(torch.Tensor), img_info),
                "labels": labels,
            }
            for boxes, labels, img_info in zip(batch.bboxes, batch.labels, batch.imgs_info, strict=True)
        ]
        return {"preds": preds, "target": target}

    def build_default_metric(self) -> Metric | MetricCollection:
        """Mean average precision over boxes, the standard detection metric."""
        return MeanAPCallable(self.label_info)

    @property
    def _exporter(self) -> ModelExporter:
        return HFModelExporter(
            task_level_export_parameters=self._export_parameters,
            data_input_params=self.data_input_params,
            resize_mode="standard",
            swap_rgb=False,
            onnx_export_configuration={"input_names": ["images"], "output_names": ["bboxes", "labels", "scores"]},
        )

    def forward_for_tracing(self, images: torch.Tensor) -> dict[str, torch.Tensor]:
        """Return per-query boxes/labels/scores for ONNX/OpenVINO export.

        Every query is kept (no top-k or thresholding) so the traced graph
        has a static shape; ModelAPI's SSD-style parser does the filtering
        at inference time. Boxes are normalized XYXY (Lightning's DETR-family
        contract), not the pixel-space boxes ``postprocess`` produces for
        metrics — see design doc 7.1 for why the normalized layout was
        chosen. Background-class handling follows G3.
        """
        outputs = self.hf_model(pixel_values=images)
        if getattr(self.hf_model.config, "use_focal_loss", False):
            probs = outputs.logits.sigmoid()
        else:
            probs = outputs.logits.softmax(dim=-1)[..., :-1]
        scores, labels = probs.max(dim=-1)
        bboxes = box_convert(outputs.pred_boxes, in_fmt="cxcywh", out_fmt="xyxy").clamp(0.0, 1.0)
        return {"bboxes": bboxes, "labels": labels, "scores": scores}
