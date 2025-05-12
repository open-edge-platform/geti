# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

from iai_core.entities.dataset_entities import PipelineDataset, TaskDataset


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
