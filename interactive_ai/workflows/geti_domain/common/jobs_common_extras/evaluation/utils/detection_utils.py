# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

import numpy as np
from iai_core.entities.model import Model
from model_api.models.utils import Detection

from jobs_common_extras.evaluation.utils.helpers import is_model_legacy_otx_version

logger = logging.getLogger(__name__)


def detection2array(detections: list[Detection]) -> np.ndarray:
    """
    Convert list of OpenVINO Detection to a numpy array.

    :param detections: list of OpenVINO Detection containing [score, id, xmin, ymin, xmax, ymax]
    :return: numpy array with [label, confidence, x1, y1, x2, y2]
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
    return np.concatenate((labels, scores, boxes), -1)


def get_legacy_detection_inferencer_configuration(model: Model) -> dict:
    """
    Get legacy OTX (version < 2.0) detection configuration from the model.

    :param model: (Geti) Model to get the detection configuration from
    :return: dict representing the detection configuration
    """
    if not is_model_legacy_otx_version(model):
        logger.warning(f"Model {model.id_} is not a legacy OTX model. Skipping legacy detection configuration.")
        return {}

    postprocessing = model.configuration.configurable_parameters.postprocessing  # type: ignore

    output_config: dict = {}
    try:
        output_config["use_ellipse_shapes"] = postprocessing.use_ellipse_shapes
    except AttributeError:
        # Note: rotated detection does not have this parameter
        output_config["use_ellipse_shapes"] = False

    return output_config
