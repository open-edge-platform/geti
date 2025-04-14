# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from geti_types import ID
from sc_sdk.entities.label import Label
from sc_sdk.entities.scored_label import LabelSource, ScoredLabel

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

    @staticmethod
    def scored_label_from_rest(scored_label_data: dict, label: Label) -> ScoredLabel:
        probability = scored_label_data.get(PROBABILITY, 1.0)
        label_source = None
        if SOURCE in scored_label_data:
            source_dict = scored_label_data[SOURCE]
            label_source = LabelSource(
                user_id=source_dict.get(USER_ID, ""),
                model_id=ID(source_dict.get(MODEL_ID)),
                model_storage_id=ID(source_dict.get(MODEL_STORAGE_ID)),
            )
        return ScoredLabel(
            label_id=label.id_,
            is_empty=label.is_empty,
            probability=probability,
            label_source=label_source,
        )
