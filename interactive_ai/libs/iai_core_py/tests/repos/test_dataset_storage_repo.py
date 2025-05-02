#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#


from iai_core.entities.dataset_storage import NullDatasetStorage
from iai_core.repos import DatasetStorageRepo
from iai_core.repos.mappers import DatasetStorageToMongo

from geti_types import ProjectIdentifier


class TestDatasetStorageRepo:
    def test_dataset_storage_repo(self, fxt_ote_id) -> None:
        project_identifier = ProjectIdentifier(workspace_id=fxt_ote_id(1), project_id=fxt_ote_id(2))
        repo = DatasetStorageRepo(project_identifier)

        assert repo.forward_map == DatasetStorageToMongo.forward
        assert repo.backward_map == DatasetStorageToMongo.backward
        assert repo.null_object == NullDatasetStorage()
