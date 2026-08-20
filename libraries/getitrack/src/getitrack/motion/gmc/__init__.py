# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Global motion compensation estimators.

Importing the package registers every estimator with `BaseMotionEstimator`, so
`BaseMotionEstimator.from_config` can build any of them by `GMCMethod`.
"""

from getitrack.motion.gmc.base import BaseMotionEstimator
from getitrack.motion.gmc.ecc import ECCEstimator
from getitrack.motion.gmc.features import FeatureMatchingEstimator
from getitrack.motion.gmc.orb import ORBEstimator
from getitrack.motion.gmc.sift import SIFTEstimator
from getitrack.motion.gmc.sparse_optflow import SparseOptFlowEstimator

__all__ = [
    "BaseMotionEstimator",
    "ECCEstimator",
    "FeatureMatchingEstimator",
    "ORBEstimator",
    "SIFTEstimator",
    "SparseOptFlowEstimator",
]
