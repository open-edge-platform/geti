# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements constants
"""

import os

MAX_N_MEDIA_RETURNED = 1000
DEFAULT_N_MEDIA_RETURNED = 100

MAX_N_PREDICTIONS_RETURNED = 20
MAX_N_ANNOTATIONS_RETURNED = 500

MAX_UNANNOTATED_DATASET_SIZE: int = 10000

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
