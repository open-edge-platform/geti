#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#


import pytest

from sc_sdk.entities.model_storage import ModelStorage
from sc_sdk.entities.model_template import NullModelTemplate
from sc_sdk.repos import ModelStorageRepo


@pytest.mark.ScSdkComponent
class TestModelStorageRepo:
    def test_indexes(self, fxt_project_identifier) -> None:
        model_storage_repo = ModelStorageRepo(fxt_project_identifier)

        indexes_names = set(model_storage_repo._collection.index_information().keys())

        assert indexes_names == {
            "_id_",
            "organization_id_-1_workspace_id_-1_project_id_-1__id_1",
            "task_node_id_-1",
            "model_template_id_-1",
        }

    def test_get_by_task_node_id(self, request, fxt_model_storage_repo, fxt_ote_id) -> None:
        # Arrange
        model_storage_repo = fxt_model_storage_repo
        task_node_id_1 = fxt_ote_id(11)
        task_node_id_2 = fxt_ote_id(12)
        # create 3 model storages: 2 for one task, 1 for the other one
        ms1, ms2, ms3 = (
            ModelStorage(
                id_=ModelStorageRepo.generate_id(),
                project_id=model_storage_repo.identifier.project_id,
                task_node_id=task_node_id,
                model_template=NullModelTemplate(),
            )
            for task_node_id in [task_node_id_1, task_node_id_1, task_node_id_2]
        )
        model_storage_repo.save_many([ms1, ms2, ms3])
        request.addfinalizer(lambda: model_storage_repo.delete_all())

        # Act
        task_1_out = model_storage_repo.get_by_task_node_id(task_node_id=task_node_id_1)
        task_2_out = model_storage_repo.get_by_task_node_id(task_node_id=task_node_id_2)

        # Assert
        assert set(task_1_out) == {ms1, ms2}
        assert set(task_2_out) == {ms3}

    @pytest.fixture
    def fxt_model_storage_repo(self, fxt_empty_project_persisted):
        model_storage_repo = ModelStorageRepo(fxt_empty_project_persisted.identifier)
        yield model_storage_repo
