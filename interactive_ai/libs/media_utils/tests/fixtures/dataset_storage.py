# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import pytest
from geti_types import DatasetStorageIdentifier


@pytest.fixture
def fxt_dataset_storage_identifier(fxt_ote_id):
    yield DatasetStorageIdentifier(
        workspace_id=fxt_ote_id(1),
        project_id=fxt_ote_id(2),
        dataset_storage_id=fxt_ote_id(3),
    )
