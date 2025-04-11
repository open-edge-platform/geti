# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
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

from geti_types import ID
from sc_sdk.entities.scored_label import ScoredLabel

COLOR = "color"
ID_ = "id"
NAME = "name"
PROBABILITY = "probability"
SOURCE = "source"
USER_ID = "user_id"
MODEL_ID = "model_id"
MODEL_STORAGE_ID = "model_storage_id"


class ScoredLabelRESTViews:
    """
    This class maps ScoredLabel entities as REST and can interpret REST views to entities
    """

    @staticmethod
    def scored_label_to_rest(scored_label: ScoredLabel) -> dict:
        """
        Maps a scored label to rest representation

        :param scored_label: ScoredLabel to map
        :return:
        """
        source = scored_label.label_source
        return {
            ID_: str(scored_label.label_id),
            PROBABILITY: scored_label.probability,
            SOURCE: {
                USER_ID: source.user_id if source.user_id else None,
                MODEL_ID: str(source.model_id) if source.model_id != ID() else None,
                MODEL_STORAGE_ID: str(source.model_storage_id) if source.model_storage_id != ID() else None,
            },
        }
