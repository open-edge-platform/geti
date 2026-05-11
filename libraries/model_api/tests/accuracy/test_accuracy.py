#
# Copyright (C) 2020-2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
import ast
import contextlib
import json
import os
from pathlib import Path

import cv2
import numpy as np
import onnx
import pytest
from model_api.adapters.onnx_adapter import ONNXRuntimeAdapter
from model_api.adapters.openvino_adapter import OpenvinoAdapter, create_core
from model_api.adapters.utils import load_parameters_from_onnx

# TODO refactor this test so that it does not use eval
# flake8: noqa: F401
from model_api.models import (
    ActionClassificationModel,
    AnomalyDetection,
    AnomalyResult,
    ClassificationModel,
    ClassificationResult,
    DetectedKeypoints,
    DetectionModel,
    DetectionResult,
    ImageModel,
    ImageResultWithSoftPrediction,
    InstanceSegmentationResult,
    KeypointDetectionModel,
    MaskRCNNModel,
    PredictedMask,
    Prompt,
    SAMDecoder,
    SAMImageEncoder,
    SAMLearnableVisualPrompter,
    SAMVisualPrompter,
    SegmentationModel,
    VisualPromptingResult,
    ZSLVisualPromptingResult,
    add_rotated_rects,
    get_contours,
)
from model_api.tilers import (
    DetectionTiler,
    InstanceSegmentationTiler,
    SemanticSegmentationTiler,
)
from model_api.visualizer import Visualizer

# Mapping of model type strings to actual classes for security
MODEL_TYPE_MAPPING = {
    "ActionClassificationModel": ActionClassificationModel,
    "AnomalyDetection": AnomalyDetection,
    "ClassificationModel": ClassificationModel,
    "DetectionModel": DetectionModel,
    "ImageModel": ImageModel,
    "KeypointDetectionModel": KeypointDetectionModel,
    "MaskRCNNModel": MaskRCNNModel,
    "SAMDecoder": SAMDecoder,
    "SAMImageEncoder": SAMImageEncoder,
    "SAMLearnableVisualPrompter": SAMLearnableVisualPrompter,
    "SAMVisualPrompter": SAMVisualPrompter,
    "SegmentationModel": SegmentationModel,
    # Tiler classes
    "DetectionTiler": DetectionTiler,
    "InstanceSegmentationTiler": InstanceSegmentationTiler,
    "SemanticSegmentationTiler": SemanticSegmentationTiler,
}


def read_config(fname):
    with fname.open("r") as f:
        return json.load(f)


def create_models(model_type, model_path, download_dir, force_onnx_adapter=False, device="CPU", configuration=None):
    if model_path.endswith(".onnx") and force_onnx_adapter:
        wrapper_type = model_type.get_model_class(
            load_parameters_from_onnx(onnx.load(model_path))["model_info"]["model_type"],
        )
        model = wrapper_type(
            ONNXRuntimeAdapter(
                model_path,
                ort_options={"providers": ["CPUExecutionProvider"]},
            ),
        )
        model.load()
        return [model]

    configuration = configuration or {}

    models = [
        model_type.create_model(model_path, device=device, download_dir=download_dir, configuration=configuration),
    ]
    if model_path.endswith(".xml"):
        model = create_core().read_model(model_path)
        if model.has_rt_info(["model_info", "model_type"]):
            wrapper_type = model_type.get_model_class(
                model.get_rt_info(["model_info", "model_type"]).astype(str),
            )
            model = wrapper_type(OpenvinoAdapter(create_core(), model_path, device=device), configuration=configuration)
            model.load()
            models.append(model)
    return models


@pytest.fixture(scope="session")
def data(pytestconfig):
    return pytestconfig.getoption("data")


@pytest.fixture(scope="session")
def results_dir(pytestconfig):
    return pytestconfig.getoption("results_dir")


@pytest.fixture(scope="session")
def device(pytestconfig):
    return pytestconfig.getoption("device")


@pytest.fixture(scope="session")
def dump(pytestconfig):
    return pytestconfig.getoption("dump")


@pytest.fixture(scope="session")
def result(pytestconfig):
    return pytestconfig.test_results


@pytest.fixture(scope="session")
def model_data_file(pytestconfig):
    return pytestconfig.getoption("model_data")


def pytest_generate_tests(metafunc):
    if "model_data" in metafunc.fixturenames:
        model_data_file = metafunc.config.getoption("model_data")
        model_data_path = Path(__file__).resolve().parent / model_data_file
        config_data = read_config(model_data_path)
        metafunc.parametrize("model_data", config_data)


def compare_classification_result(outputs: ClassificationResult, reference: dict) -> None:
    """Compare ClassificationResult with reference data.

    Args:
        outputs: The ClassificationResult to validate
        reference: Dictionary containing expected values for top_labels and/or raw_scores

    Note:
        When raw_scores are empty and confidence is 1.0, only confidence is checked.
        This handles models with embedded TopK that may produce different argmax results
        on different devices due to numerical precision differences.
    """
    assert "top_labels" in reference
    assert outputs.top_labels is not None
    assert len(outputs.top_labels) == len(reference["top_labels"])

    # Check if we have raw scores to validate predictions
    has_raw_scores = (
        outputs.raw_scores is not None
        and outputs.raw_scores.size > 0
        and "raw_scores" in reference
        and len(reference["raw_scores"]) > 0
    )

    for i, (actual_label, expected_label) in enumerate(zip(outputs.top_labels, reference["top_labels"])):
        if not has_raw_scores and expected_label.get("confidence", 0.0) == 1.0:
            assert abs(actual_label.confidence - expected_label["confidence"]) < 1e-1, f"Label {i} confidence mismatch"
        else:
            assert actual_label.id == expected_label["id"], f"Label {i} id mismatch"
            assert actual_label.name == expected_label["name"], f"Label {i} name mismatch"
            assert abs(actual_label.confidence - expected_label["confidence"]) < 1e-1, f"Label {i} confidence mismatch"

    # Validate raw_scores if available
    if has_raw_scores:
        expected_scores = np.array(reference["raw_scores"])
        assert np.allclose(outputs.raw_scores, expected_scores, rtol=1e-2, atol=1e-1), "raw_scores mismatch"


def create_classification_result_dump(outputs: ClassificationResult) -> dict:
    """Create a JSON-serializable dump of ClassificationResult.

    Args:
        outputs: The ClassificationResult to serialize

    Returns:
        Dictionary containing top_labels and raw_scores in JSON-serializable format
    """
    return {
        "top_labels": [
            {
                "id": int(label.id) if label.id is not None else None,
                "name": label.name,
                "confidence": float(label.confidence) if label.confidence is not None else None,
            }
            for label in outputs.top_labels
        ]
        if outputs.top_labels
        else None,
        "raw_scores": [float(x) for x in outputs.raw_scores.tolist()] if outputs.raw_scores is not None else None,
    }


def compare_detection_result(outputs: DetectionResult, reference: dict) -> None:
    """Compare DetectionResult with reference data.

    Args:
        outputs: The DetectionResult to validate
        reference: Dictionary containing expected values for bboxes, labels, scores, and label_names
    """
    assert "bboxes" in reference
    assert outputs.bboxes is not None
    expected_bboxes = np.array(reference["bboxes"])

    if expected_bboxes.size == 0 and outputs.bboxes.size == 0:
        expected_bboxes = expected_bboxes.reshape(0, 4)

    assert (
        outputs.bboxes.shape == expected_bboxes.shape
    ), f"bboxes shape mismatch: {outputs.bboxes.shape} vs {expected_bboxes.shape}"

    # Sort both outputs and expected by bbox coordinates (x1, y1, x2, y2) for deterministic comparison
    output_sort_indices = np.lexsort((
        outputs.bboxes[:, 3],
        outputs.bboxes[:, 2],
        outputs.bboxes[:, 1],
        outputs.bboxes[:, 0],
    ))
    expected_sort_indices = np.lexsort((
        expected_bboxes[:, 3],
        expected_bboxes[:, 2],
        expected_bboxes[:, 1],
        expected_bboxes[:, 0],
    ))

    sorted_output_bboxes = outputs.bboxes[output_sort_indices]
    sorted_expected_bboxes = expected_bboxes[expected_sort_indices]

    assert np.allclose(sorted_output_bboxes, sorted_expected_bboxes, rtol=1e-2, atol=1), "bboxes mismatch"

    assert "labels" in reference
    assert outputs.labels is not None
    expected_labels = np.array(reference["labels"])
    assert np.array_equal(outputs.labels, expected_labels), "labels mismatch"

    assert "scores" in reference
    assert outputs.scores is not None
    expected_scores = np.array(reference["scores"])
    assert np.allclose(outputs.scores, expected_scores, rtol=1e-2, atol=1e-1), "scores mismatch"

    assert "label_names" in reference
    assert outputs.label_names is not None
    assert outputs.label_names == reference["label_names"], "label_names mismatch"


def create_detection_result_dump(outputs: DetectionResult) -> dict:
    """Create a JSON-serializable dump of DetectionResult.

    Args:
        outputs: The DetectionResult to serialize

    Returns:
        Dictionary containing bboxes, labels, scores, and label_names in JSON-serializable format
    """
    return {
        "bboxes": outputs.bboxes.tolist() if outputs.bboxes is not None else None,
        "labels": outputs.labels.tolist() if outputs.labels is not None else None,
        "scores": [float(x) for x in outputs.scores.tolist()] if outputs.scores is not None else None,
        "label_names": outputs.label_names if outputs.label_names is not None else None,
    }


def test_image_models(data, device, dump, result, model_data, results_dir):  # noqa: C901
    name = model_data["name"]
    if name.endswith((".xml", ".onnx")):
        name = f"{data}/{name}"

    for model in create_models(
        MODEL_TYPE_MAPPING[model_data["type"]],
        name,
        data,
        model_data.get("force_ort", False),
        device=device,
        configuration=model_data.get("configuration", None),
    ):
        if "tiler" in model_data:
            if "extra_model" in model_data:
                extra_adapter = OpenvinoAdapter(
                    create_core(),
                    f"{data}/{model_data['extra_model']}",
                    device=device,
                )

                extra_model = MODEL_TYPE_MAPPING[model_data["extra_type"]](
                    extra_adapter,
                    configuration={},
                    preload=True,
                )
                model = MODEL_TYPE_MAPPING[model_data["tiler"]](
                    model,
                    configuration={},
                    tile_classifier_model=extra_model,
                )
            else:
                model = MODEL_TYPE_MAPPING[model_data["tiler"]](model, configuration={})
        elif "prompter" in model_data:
            encoder_adapter = OpenvinoAdapter(
                create_core(),
                f"{data}/{model_data['encoder']}",
                device=device,
            )

            encoder_model = MODEL_TYPE_MAPPING[model_data["encoder_type"]](
                encoder_adapter,
                configuration={},
                preload=True,
            )
            model = MODEL_TYPE_MAPPING[model_data["prompter"]](encoder_model, model)

        if dump:
            result.append(model_data)
            inference_results = []

        for test_data in model_data["test_data"]:
            image_path = Path(data) / test_data["image"]
            image = cv2.imread(str(image_path))
            if image is None:
                error_message = f"Failed to read the image at {image_path}"
                raise RuntimeError(error_message)
            if "input_res" in model_data:
                image = cv2.resize(image, ast.literal_eval(model_data["input_res"]))
            if isinstance(model, ActionClassificationModel):
                image = np.stack([image for _ in range(8)])
            if "prompter" in model_data:
                if model_data["prompter"] == "SAMLearnableVisualPrompter":
                    model.learn(
                        image,
                        points=[
                            Prompt(
                                np.array([image.shape[0] / 2, image.shape[1] / 2]),
                                0,
                            ),
                        ],
                        polygons=[
                            Prompt(
                                np.array(
                                    [
                                        [image.shape[0] / 4, image.shape[1] / 4],
                                        [image.shape[0] / 4, image.shape[1] / 2],
                                        [image.shape[0] / 2, image.shape[1] / 2],
                                    ],
                                ),
                                1,
                            ),
                        ],
                    )
                    outputs = model(image)
                else:
                    outputs = model(
                        image,
                        points=[
                            Prompt(
                                np.array([image.shape[0] / 2, image.shape[1] / 2]),
                                0,
                            ),
                        ],
                    )
            else:
                outputs = model(image)

            store_outputs(name, image, device, outputs, results_dir)

            if isinstance(outputs, ClassificationResult):
                compare_classification_result(outputs, test_data["reference"])
                image_result = create_classification_result_dump(outputs)
            elif type(outputs) is DetectionResult:
                compare_detection_result(outputs, test_data["reference"])
                image_result = create_detection_result_dump(outputs)
            elif isinstance(outputs, ImageResultWithSoftPrediction):
                assert len(test_data["reference"]) == 1
                if hasattr(model, "get_contours"):
                    contours = model.get_contours(outputs)
                else:
                    contours = model.model.get_contours(outputs)
                contour_str = "; "
                for contour in contours:
                    contour_str += str(contour) + ", "
                output_str = str(outputs) + contour_str
                assert test_data["reference"][0] == output_str
                image_result = [output_str]
            elif type(outputs) is InstanceSegmentationResult:
                assert len(test_data["reference"]) == 1
                output_str = str(add_rotated_rects(outputs)) + "; "
                with contextlib.suppress(RuntimeError):
                    # getContours() assumes each instance generates only one contour.
                    # That doesn't hold for some models
                    output_str += "; ".join(str(contour) for contour in get_contours(outputs)) + "; "
                assert test_data["reference"][0] == output_str
                image_result = [output_str]
            elif isinstance(outputs, AnomalyResult):
                assert len(test_data["reference"]) == 1
                output_str = str(outputs)
                assert test_data["reference"][0] == output_str
                image_result = [output_str]
            elif isinstance(outputs, (ZSLVisualPromptingResult, VisualPromptingResult, DetectedKeypoints)):
                output_str = str(outputs)
                assert test_data["reference"][0] == output_str
                image_result = [output_str]
            else:
                pytest.fail(f"Unexpected output type: {type(outputs)}")
            if dump:
                inference_results.append(
                    {"image": test_data["image"], "reference": image_result},
                )
    save_name = Path(name).name if name.endswith(".xml") else name + ".xml"

    if not model_data.get("force_ort", False):
        if "tiler" in model_data:
            model.get_model().save(data + "/serialized/" + save_name)
        elif "prompter" in model_data:
            pass
        else:
            model.save(data + "/serialized/" + save_name)
            if model_data.get("check_extra_rt_info", False):
                assert (
                    create_core()
                    .read_model(data + "/serialized/" + save_name)
                    .get_rt_info(["model_info", "label_ids"])
                    .astype(str)
                )

    if dump:
        result[-1]["test_data"] = inference_results


def store_outputs(name, image, device, result, results_dir: str) -> None:
    if not results_dir:
        return

    Path(results_dir).mkdir(exist_ok=True, parents=True)

    iteration = 1
    while True:
        path = Path(results_dir) / f"{Path(name).stem}_{iteration}_{device}.png"
        if not path.exists():
            break
        iteration += 1

    visualizer = Visualizer()
    try:
        visualizer.save(image, result, path)
    except (TypeError, ValueError) as e:
        print(f"Cannot save the output visualization for {name}. Error: {e}")
