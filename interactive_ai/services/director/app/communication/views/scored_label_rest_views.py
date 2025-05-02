# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from geti_types import ID
from iai_core.entities.scored_label import ScoredLabel

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
