# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements constants
"""

import os

MAX_SETTINGS_LENGTH_IN_CHARACTERS = 3000

MAX_N_MEDIA_RETURNED = 1000
DEFAULT_N_MEDIA_RETURNED = 100

MAX_N_PROJECTS_RETURNED = 100
DEFAULT_N_PROJECTS_RETURNED = 10

MAX_N_ANNOTATIONS_RETURNED = 500

MAX_UNANNOTATED_DATASET_SIZE: int = 10000

# Limit object sizes to return, see: CVS-91701
MAX_OBJECT_SIZES_PER_LABEL = 1000

MINIMUM_PIXELS_FOR_ANNOTATION = 1

# Maximum number of projects that an organization can have
try:
    MAX_NUMBER_OF_PROJECTS_PER_ORGANIZATION: int | None = int(os.environ.get("MAX_NUMBER_OF_PROJECTS_PER_ORGANIZATION"))  # type: ignore[arg-type]
except (ValueError, TypeError):
    MAX_NUMBER_OF_PROJECTS_PER_ORGANIZATION = None

try:
    MAX_NUMBER_OF_MEDIA_PER_PROJECT: int | None = int(os.environ.get("MAX_NUMBER_OF_MEDIA_PER_PROJECT"))  # type: ignore[arg-type]
except (ValueError, TypeError):
    MAX_NUMBER_OF_MEDIA_PER_PROJECT = None

try:
    MAX_NUMBER_OF_ANNOTATION_VERSIONS_PER_MEDIA: int | None = int(
        os.environ.get("MAX_NUMBER_OF_ANNOTATION_VERSIONS_PER_MEDIA")  # type: ignore[arg-type]
    )
except (ValueError, TypeError):
    MAX_NUMBER_OF_ANNOTATION_VERSIONS_PER_MEDIA = None

try:
    MAX_NUMBER_OF_DATASET_STORAGES: int | None = int(os.environ.get("MAX_NUMBER_OF_DATASET_STORAGES"))  # type: ignore[arg-type]
except (ValueError, TypeError):
    MAX_NUMBER_OF_DATASET_STORAGES = None

# Max number of tasks supported in a project
MAX_NUMBER_OF_TRAINABLE_TASKS = int(os.environ.get("MAX_NUMBER_OF_TRAINABLE_TASKS", "2"))
# Max number of connections for a project
# This value is calculated by counting the connections that would be made:
# - Normal project (dataset -> task_1) = 1 connection
# - Task chain project (dataset -> task_1 -> crop -> task_2) = 3 connections
# this gives the formula x = 2n - 1, where n is the number of tasks.
# Supporting 2 tasks gives x = 2*2 - 1 , x = 3
MAX_NUMBER_OF_CONNECTIONS_IN_CHAIN = 2 * MAX_NUMBER_OF_TRAINABLE_TASKS - 1

MAX_NUMBER_OF_LABELS = int(os.environ.get("MAX_NUMBER_OF_LABELS", "1000"))

# Maximum number of pixels allowed in an image: (width x height) > MAX_NUMBER_OF_PIXELS
try:
    MAX_NUMBER_OF_PIXELS: int | None = int(os.environ.get("MAX_NUMBER_OF_PIXELS"))  # type: ignore[arg-type]
except (ValueError, TypeError):
    MAX_NUMBER_OF_PIXELS = None

MIN_IMAGE_SIZE = int(os.environ.get("MIN_IMAGE_SIZE", "32"))  # pixels
MAX_IMAGE_SIZE = int(os.environ.get("MAX_IMAGE_SIZE", "20000"))  # pixels
MIN_VIDEO_SIZE = int(os.environ.get("MIN_VIDEO_SIZE", "32"))  # pixels
MAX_VIDEO_WIDTH = int(os.environ.get("MAX_VIDEO_WIDTH", "7680"))  # pixels
MAX_VIDEO_HEIGHT = int(os.environ.get("MAX_VIDEO_HEIGHT", "4320"))  # pixels
MAX_VIDEO_LENGTH = int(os.environ.get("MAX_VIDEO_LENGTH", "10800"))  # seconds (=3hours)
