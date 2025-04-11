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

import pytest

from sc_sdk.entities.dataset_entities import PipelineDataset, TaskDataset


@pytest.fixture
def fxt_task_dataset_entity(fxt_mongo_id):
    yield TaskDataset(
        dataset_id=fxt_mongo_id(1),
        dataset_storage_id=fxt_mongo_id(0),
        task_node_id=fxt_mongo_id(2),
    )


@pytest.fixture
def fxt_pipeline_dataset_entity(fxt_mongo_id, fxt_task_dataset_entity):
    yield PipelineDataset(
        dataset_storage_id=fxt_task_dataset_entity.dataset_storage_id,
        project_id=fxt_mongo_id(1),
        task_datasets={fxt_mongo_id(2): fxt_task_dataset_entity},
    )
