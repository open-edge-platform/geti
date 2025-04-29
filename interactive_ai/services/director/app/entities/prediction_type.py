# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
