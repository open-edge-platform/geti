# Copyright (C) 2022-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
Constants for YOLO dataset format.
"""

from getidata.fields import Subset

# Mapping from subset enum to YOLO Ultralytics directory names
SUBSET_TO_DIR_NAME = {
    Subset.TRAINING: "train",
    Subset.VALIDATION: "val",
    Subset.TESTING: "test",
    Subset.UNASSIGNED: "unassigned",
}

# Mapping from YOLO directory names (and the ``data.yaml`` keys sharing those names) to the
# subset enum. Exporters are not consistent in how they spell the splits (e.g. Roboflow names
# the validation split "valid" instead of "val"), so common variations are accepted on import.
# Export always uses the canonical names from ``SUBSET_TO_DIR_NAME``.
DIR_NAME_TO_SUBSET = {
    "train": Subset.TRAINING,
    "training": Subset.TRAINING,
    "val": Subset.VALIDATION,
    "valid": Subset.VALIDATION,
    "validation": Subset.VALIDATION,
    "test": Subset.TESTING,
    "testing": Subset.TESTING,
    "unassigned": Subset.UNASSIGNED,
    "unknown": Subset.UNASSIGNED,
}

# Mapping from subset enum to traditional YOLO directory names
TRADITIONAL_SUBSET_DIR_NAMES = {
    Subset.TRAINING: "obj_train_data",
    Subset.VALIDATION: "obj_valid_data",
    Subset.TESTING: "obj_test_data",
    Subset.UNASSIGNED: "obj_data",
}

# Mapping from subset enum to traditional YOLO config keys
TRADITIONAL_SUBSET_CONFIG_KEYS = {
    Subset.TRAINING: "train",
    Subset.VALIDATION: "valid",
    Subset.TESTING: "test",
}

# Mapping from traditional YOLO directory names to subset enum
TRADITIONAL_DIR_NAME_TO_SUBSET = {
    "obj_train_data": Subset.TRAINING,
    "train": Subset.TRAINING,
    "obj_valid_data": Subset.VALIDATION,
    "valid": Subset.VALIDATION,
    "val": Subset.VALIDATION,
    "obj_test_data": Subset.TESTING,
    "test": Subset.TESTING,
    "obj_data": Subset.UNASSIGNED,
}
