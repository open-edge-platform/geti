# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

from enum import Enum


class PredictionType(Enum):
    """
    Prediction type stores the requested way to obtain a prediction:
        - LATEST: pull latest prediction for a media entity from the database
        - ONLINE: infer a new prediction using the latest active model
        - AUTO: first pull latest prediction for a media entity from the database, if
            none exist, then infer a new prediction using the latest active model
    """

    LATEST = 0
    ONLINE = 1
    AUTO = 2
