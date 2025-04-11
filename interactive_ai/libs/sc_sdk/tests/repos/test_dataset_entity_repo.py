# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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
from unittest.mock import ANY, MagicMock, call, patch

import pytest

from sc_sdk.entities.dataset_entities import NullPipelineDataset, PipelineDataset
from sc_sdk.entities.datasets import Dataset, DatasetPurpose
from sc_sdk.repos import DatasetRepo, TaskNodeRepo
from sc_sdk.repos.dataset_entity_repo import DuplicatePipelineDatasetException, PipelineDatasetRepo


@pytest.mark.ScSdkComponent
class TestPipelineDatasetRepo:
    def test_get_or_create(self, request, fxt_dataset_storage_identifier, fxt_ote_id) -> None:
        request.addfinalizer(lambda: PipelineDatasetRepo.get_or_create.cache_clear())
        task_ids = [fxt_ote_id(201), fxt_ote_id(202)]
        with (
            patch.object(TaskNodeRepo, "get_trainable_task_ids", return_value=task_ids) as mock_get_task_ids,
            patch.object(DatasetRepo, "save_shallow") as mock_save_dataset,
            patch.object(PipelineDatasetRepo, "save") as mock_save_pipeline_dataset,
        ):
            pde = PipelineDatasetRepo.get_or_create(fxt_dataset_storage_identifier)
            # request the entity again to test the cache
            pde2 = PipelineDatasetRepo.get_or_create(fxt_dataset_storage_identifier)

        mock_get_task_ids.assert_called_once_with()
        mock_save_dataset.assert_has_calls(
            [
                call(Dataset(purpose=DatasetPurpose.TEMPORARY_DATASET, id=ANY)),
                call(Dataset(purpose=DatasetPurpose.TEMPORARY_DATASET, id=ANY)),
            ]
        )
        mock_save_pipeline_dataset.assert_called_once_with(
            PipelineDataset(
                project_id=fxt_dataset_storage_identifier.project_id,
                dataset_storage_id=fxt_dataset_storage_identifier.dataset_storage_id,
                task_datasets=ANY,
            )
        )
        assert isinstance(pde, PipelineDataset)
        assert not isinstance(pde, NullPipelineDataset)
        assert id(pde2) == id(pde)

    def test_get_or_create_already_existing(self, request, fxt_dataset_storage_identifier) -> None:
        request.addfinalizer(lambda: PipelineDatasetRepo.get_or_create.cache_clear())
        pde_mock = MagicMock(spec=PipelineDataset)
        with (
            patch.object(TaskNodeRepo, "get_trainable_task_ids") as mock_get_task_ids,
            patch.object(DatasetRepo, "save_shallow") as mock_save_dataset,
            patch.object(PipelineDatasetRepo, "save") as mock_save_pde,
            patch.object(PipelineDatasetRepo, "get_one", return_value=pde_mock),
        ):
            pde = PipelineDatasetRepo.get_or_create(fxt_dataset_storage_identifier)

        mock_get_task_ids.assert_not_called()
        mock_save_dataset.assert_not_called()
        mock_save_pde.assert_not_called()
        assert pde == pde_mock

    def test_get_or_create_already_existing_race_cond(
        self, request, fxt_dataset_storage_identifier, fxt_ote_id
    ) -> None:
        request.addfinalizer(lambda: PipelineDatasetRepo.get_or_create.cache_clear())
        task_ids = [fxt_ote_id(201), fxt_ote_id(202)]
        pde_mock = MagicMock(spec=PipelineDataset)
        with (
            patch.object(TaskNodeRepo, "get_trainable_task_ids", return_value=task_ids) as mock_get_task_ids,
            patch.object(DatasetRepo, "save_shallow") as mock_save_dataset,
            patch.object(DatasetRepo, "delete_by_id") as mock_delete_dataset,
            patch.object(
                PipelineDatasetRepo,
                "save",
                side_effect=DuplicatePipelineDatasetException(fxt_dataset_storage_identifier),
            ),
            patch.object(PipelineDatasetRepo, "get_one", side_effect=[NullPipelineDataset(), pde_mock]),
        ):
            pde = PipelineDatasetRepo.get_or_create(fxt_dataset_storage_identifier)

        mock_get_task_ids.assert_called_once_with()
        assert mock_save_dataset.call_count == 2
        assert mock_delete_dataset.call_count == 2
        assert pde == pde_mock

    def test_save(self, request, fxt_dataset_storage_identifier) -> None:
        pde_repo = PipelineDatasetRepo(fxt_dataset_storage_identifier)
        request.addfinalizer(lambda: pde_repo.delete_all())
        pde = PipelineDataset(
            project_id=fxt_dataset_storage_identifier.project_id,
            dataset_storage_id=fxt_dataset_storage_identifier.dataset_storage_id,
            task_datasets={},
        )

        pde_repo.save(pde)
        with pytest.raises(DuplicatePipelineDatasetException):
            pde_repo.save(pde)

        assert not isinstance(pde_repo.get_one(), NullPipelineDataset)

    def test_delete_by_id(self, request, fxt_dataset_storage_identifier) -> None:
        pde_repo = PipelineDatasetRepo(fxt_dataset_storage_identifier)
        request.addfinalizer(lambda: pde_repo.delete_all())
        pde = PipelineDataset(
            project_id=fxt_dataset_storage_identifier.project_id,
            dataset_storage_id=fxt_dataset_storage_identifier.dataset_storage_id,
            task_datasets={},
        )
        pde_repo.save(pde)

        found_and_deleted = pde_repo.delete_by_id(id_=pde.id_)

        assert found_and_deleted
        assert isinstance(pde_repo.get_one(), NullPipelineDataset)
