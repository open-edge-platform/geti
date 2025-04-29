# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from freezegun import freeze_time
from tests.test_helpers import verify_mongo_mapper

from entities.auto_train_activation import AutoTrainActivation
from storage.mappers.auto_train_activation_mapper import AutoTrainActivationToMongo


class TestAutoTrainActivationMapper:
    @freeze_time("2011-11-11 11:11:11")
    def test_auto_train_activation_mapper(self, fxt_ote_id, fxt_session_ctx) -> None:
        auto_train_activation = AutoTrainActivation(
            task_node_id=fxt_ote_id(1),
            model_storage_id=fxt_ote_id(2),
            session=fxt_session_ctx,
            ready=False,
            ephemeral=False,
        )

        verify_mongo_mapper(entity_to_map=auto_train_activation, mapper_class=AutoTrainActivationToMongo)
