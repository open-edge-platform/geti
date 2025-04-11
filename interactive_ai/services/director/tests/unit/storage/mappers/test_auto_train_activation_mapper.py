# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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
