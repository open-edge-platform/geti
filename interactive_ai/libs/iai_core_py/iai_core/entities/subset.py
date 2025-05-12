# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This file defines the Subset enum for use in datasets."""

from enum import Enum


class Subset(Enum):
    """Describes the Subset a DatasetItem is assigned to."""

    NONE = 0
    TRAINING = 1
    VALIDATION = 2
    TESTING = 3
    UNLABELED = 4
    PSEUDOLABELED = 5
    UNASSIGNED = 6

    def __str__(self):
        """Returns name of subset."""
        return str(self.name)

    def __repr__(self):
        """Returns name of subset."""
        return f"Subset.{self.name}"
