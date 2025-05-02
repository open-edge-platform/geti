# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module define enums and constants"""

from collections import defaultdict
from enum import Enum, auto

import datumaro as dm
from iai_core_py.entities.label import Domain

FORMAT_NAME_MAP: dict[str, str] = {
    "coco_instances": "coco_instances",
    "coco": "coco_instances",
    "yolo": "yolo",
    "voc": "voc",
    "datumaro": "datumaro",
    "roboflow_coco": "roboflow_coco",
    "roboflow_voc": "roboflow_voc",
    "roboflow_yolo": "roboflow_yolo",
}

ANNOTATION_TYPE_TO_SUPPORTED_DOMAINS: dict[dm.AnnotationType, list[Domain]] = {
    dm.AnnotationType.label: [
        Domain.CLASSIFICATION,
        Domain.ANOMALY_CLASSIFICATION,
        Domain.ANOMALY_DETECTION,
        Domain.ANOMALY_SEGMENTATION,
    ],
    dm.AnnotationType.bbox: [
        Domain.DETECTION,
        Domain.SEGMENTATION,  # Geti tool supports rectangle(which is same to bbox) tool for seg., ins-seg.
        Domain.INSTANCE_SEGMENTATION,
        Domain.ANOMALY_DETECTION,
        Domain.ANOMALY_SEGMENTATION,
    ],
    dm.AnnotationType.polygon: [
        Domain.SEGMENTATION,
        Domain.INSTANCE_SEGMENTATION,
        Domain.ANOMALY_SEGMENTATION,
        Domain.ROTATED_DETECTION,
    ],
    dm.AnnotationType.ellipse: [
        Domain.SEGMENTATION,
        Domain.INSTANCE_SEGMENTATION,
        Domain.ANOMALY_SEGMENTATION,
    ],
    dm.AnnotationType.mask: [
        Domain.SEGMENTATION,
        Domain.INSTANCE_SEGMENTATION,
        Domain.ANOMALY_SEGMENTATION,
    ],
    dm.AnnotationType.points: [
        Domain.KEYPOINT_DETECTION,
    ],
}

SUPPORTED_DOMAIN_TO_ANNOTATION_TYPES: dict[Domain, set[dm.AnnotationType]] = defaultdict(set)
# Invert ANNOTATION_TYPE_TO_SUPPORTED_DOMAINS
# to create SUPPORTED_DOMAIN_TO_ANNOTATION_TYPES
for ann_type, domains in ANNOTATION_TYPE_TO_SUPPORTED_DOMAINS.items():
    for domain in domains:
        SUPPORTED_DOMAIN_TO_ANNOTATION_TYPES[domain].add(ann_type)


class GetiProjectType(Enum):
    """Enum for Geti project type"""

    CLASSIFICATION = auto()
    HIERARCHICAL_CLASSIFICATION = auto()
    DETECTION = auto()
    SEGMENTATION = auto()
    INSTANCE_SEGMENTATION = auto()
    ANOMALY_CLASSIFICATION = auto()
    ANOMALY_DETECTION = auto()
    ANOMALY_SEGMENTATION = auto()
    ROTATED_DETECTION = auto()  # ui project name is Detection Oriented
    CHAINED_DETECTION_CLASSIFICATION = auto()
    CHAINED_DETECTION_SEGMENTATION = auto()
    KEYPOINT_DETECTION = auto()
    UNKNOWN = auto()


SUPPORTED_IMPORT_PROJECT_TYPE = [
    GetiProjectType.CLASSIFICATION,
    GetiProjectType.DETECTION,
    GetiProjectType.SEGMENTATION,
    GetiProjectType.INSTANCE_SEGMENTATION,
]

ANOMALY_PROJECT_TYPES = [
    GetiProjectType.ANOMALY_CLASSIFICATION,
    GetiProjectType.ANOMALY_DETECTION,
    GetiProjectType.ANOMALY_SEGMENTATION,
]

CHAINED_PROJECT_TYPES = [
    GetiProjectType.CHAINED_DETECTION_CLASSIFICATION,
    GetiProjectType.CHAINED_DETECTION_SEGMENTATION,
]
