#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#


import pytest

from sc_sdk.entities.dataset_storage import NullDatasetStorage
from sc_sdk.repos import DatasetStorageRepo
from sc_sdk.repos.mappers import DatasetStorageToMongo

from geti_types import ProjectIdentifier


@pytest.mark.ScSdkComponent
class TestDatasetStorageRepo:
    def test_dataset_storage_repo(self, fxt_ote_id) -> None:
        project_identifier = ProjectIdentifier(workspace_id=fxt_ote_id(1), project_id=fxt_ote_id(2))
        repo = DatasetStorageRepo(project_identifier)

        assert repo.forward_map == DatasetStorageToMongo.forward
        assert repo.backward_map == DatasetStorageToMongo.backward
        assert repo.null_object == NullDatasetStorage()
