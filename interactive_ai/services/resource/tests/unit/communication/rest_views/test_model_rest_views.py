# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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

from testfixtures import compare

from communication.rest_views.model_rest_views import ModelRestInfo, ModelRESTViews


class TestModelRESTViews:
    def test_model_storage_to_rest(
        self,
        fxt_model,
        fxt_model_group_rest,
        fxt_detection_node,
        fxt_mongo_id,
        fxt_model_storage_detection,
    ) -> None:
        task_node = fxt_detection_node
        model_storage = fxt_model_storage_detection
        task_node.id_ = fxt_mongo_id(1)
        model_storage._id_ = fxt_mongo_id(0)
        model_storage._task_node_id = task_node.id_
        per_model_info = [ModelRestInfo(fxt_model, fxt_model.performance, True)]

        result = ModelRESTViews.model_storage_to_rest(
            task_node_id=task_node.id_,
            model_storage=model_storage,
            per_model_info=per_model_info,
            active_model=fxt_model,
            include_lifecycle_stage=True,
        )

        compare(result, fxt_model_group_rest)

    def test_model_info_to_rest(self, fxt_model, fxt_model_info_rest, fxt_dataset_storage, fxt_dataset_counts) -> None:
        result = ModelRESTViews.model_info_to_rest(
            model=fxt_model,
            model_performance=fxt_model.performance,
            is_label_schema_in_sync=True,
            dataset_storage_id=fxt_dataset_storage.id_,
            dataset_counts=fxt_dataset_counts,
            optimized_per_model_performance=[],
            total_disk_size=1,
        )

        compare(result, fxt_model_info_rest)

    def test_optimized_model_to_rest_pot(self, fxt_optimized_model_2, fxt_optimized_model_rest_2) -> None:
        result = ModelRESTViews.optimized_model_to_rest(
            optimized_model=fxt_optimized_model_2,
            performance=fxt_optimized_model_2.performance,
        )

        compare(result, fxt_optimized_model_rest_2)
