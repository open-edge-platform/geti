#
# Copyright (C) 2020-2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
import functools
import os
import types
from pathlib import Path

import cv2
import numpy as np
import openvino as ov
import pytest
import torch
import ultralytics
from model_api.models import YOLOv5
from ultralytics.data import utils
from ultralytics.models import yolo


def _init_predictor(yolo):
    yolo.predict(np.empty([1, 1, 3], np.uint8))


@functools.lru_cache(maxsize=1)
def _cached_alignment(pt):
    export_dir = Path(
        ultralytics.YOLO(
            Path(os.environ["DATA"]) / "ultralytics" / pt,
            "detect",
        ).export(format="openvino", half=True),
    )
    impl_wrapper = YOLOv5.create_model(export_dir / (pt.stem + ".xml"), device="CPU")
    ref_wrapper = ultralytics.YOLO(export_dir, "detect")
    ref_wrapper.overrides["imgsz"] = (impl_wrapper.w, impl_wrapper.h)
    _init_predictor(ref_wrapper)
    ref_wrapper.predictor.model.ov_compiled_model = ov.Core().compile_model(
        ref_wrapper.predictor.model.ov_model,
        "CPU",
    )
    ref_dir = export_dir / "ref"
    ref_dir.mkdir(exist_ok=True)
    return impl_wrapper, ref_wrapper, ref_dir


def _impaths():
    """
    It's impossible to pass fixture as argument for
    @pytest.mark.parametrize, so it can't take a cmd arg. Use env var
    instead. Another solution was to define
    pytest_generate_tests(metafunc) in conftest.py
    """
    impaths = sorted(
        file
        for file in (Path(os.environ["DATA"]) / "coco128/images/train2017/").iterdir()
        if file.name
        not in {  # This images fail because image preprocessing is imbedded into the model
            "000000000143.jpg",
            "000000000491.jpg",
            "000000000536.jpg",
            "000000000581.jpg",
        }
    )
    if not impaths:
        error_message = f"{Path(os.environ['DATA']) / 'coco128/images/train2017/'} is empty"
        raise RuntimeError(error_message)
    return impaths


@pytest.mark.parametrize("impath", _impaths())
@pytest.mark.parametrize("pt", [Path("yolov5mu.pt"), Path("yolov8l.pt")])
def test_alignment(impath, pt):
    impl_wrapper, ref_wrapper, ref_dir = _cached_alignment(pt)
    im = cv2.imread(str(impath))
    assert im is not None
    impl_preds = impl_wrapper(im)
    pred_boxes = impl_preds.bboxes.astype(np.float32)
    pred_scores = impl_preds.scores.astype(np.float32)
    pred_labels = impl_preds.labels
    ref_predictions = ref_wrapper.predict(im)
    assert len(ref_predictions) == 1
    ref_boxes = ref_predictions[0].boxes.data.numpy()
    if 0 == len(pred_boxes) == len(ref_boxes):
        return  # np.isclose() doesn't work for empty arrays
    ref_boxes[:, :4] = np.round(ref_boxes[:, :4], out=ref_boxes[:, :4])
    # Allow one pixel deviation because image preprocessing is imbedded into the model
    assert np.isclose(pred_boxes, ref_boxes[:, :4], 0, 1).all()
    assert np.isclose(pred_scores, ref_boxes[:, 4], 0.0, 0.02).all()
    assert (pred_labels == ref_boxes[:, 5]).all()
    with Path.open(ref_dir / impath.with_suffix(".txt").name, "w") as file:
        print(impl_preds, end="", file=file)


class Metrics(yolo.detect.DetectionValidator):
    @torch.inference_mode()
    def evaluate(self, wrapper):
        self.data = utils.check_det_dataset("coco128.yaml")
        dataloader = self.get_dataloader(self.data[self.args.split], batch_size=1)
        dataloader.dataset.transforms.transforms = (
            lambda di: {
                "batch_idx": torch.zeros(len(di["instances"])),
                "bboxes": torch.from_numpy(di["instances"].bboxes),
                "cls": torch.from_numpy(di["cls"]),
                "img": torch.empty(1, 1, 1),
                "im_file": di["im_file"],
                "ori_shape": di["ori_shape"],
                "ratio_pad": [(1.0, 1.0), (0, 0)],
            },
        )
        self.init_metrics(
            types.SimpleNamespace(
                names=dict(enumerate(wrapper.labels)),
            ),
        )
        for batch in dataloader:
            im = cv2.imread(batch["im_file"][0])
            result = wrapper(im)
            bboxes = torch.from_numpy(result.bboxes) / torch.tile(
                torch.tensor([im.shape[1], im.shape[0]], dtype=torch.float32),
                (1, 2),
            )
            scores = torch.from_numpy(result.scores)
            labels = torch.from_numpy(result.labels)

            pred = torch.cat(
                [bboxes, scores[:, None], labels[:, None].float()],
                dim=1,
            ).unsqueeze(0)
            if not pred.numel():
                pred = pred.view(1, 0, 6)
            self.update_metrics(pred, batch)
        return self.get_stats()


@pytest.mark.parametrize(
    ("pt", "ref_mAP50_95"),
    [
        (
            Path("yolov8n.pt"),
            0.439413760605130543357432770790182985365390777587890625,
        ),
        (
            Path("yolov5n6u.pt"),
            0.48720141594764942993833756190724670886993408203125,
        ),
    ],
)
def test_metric(pt, ref_mAP50_95):
    mAP50_95 = Metrics().evaluate(
        YOLOv5.create_model(
            ultralytics.YOLO(
                Path(os.environ["DATA"]) / "ultralytics" / pt,
                "detect",
            ).export(format="openvino", half=True)
            / pt.with_suffix(".xml"),
            device="CPU",
            configuration={"confidence_threshold": 0.001},
        ),
    )["metrics/mAP50-95(B)"]
    assert abs(mAP50_95 - ref_mAP50_95) <= 0.01 * ref_mAP50_95 or mAP50_95 >= ref_mAP50_95
