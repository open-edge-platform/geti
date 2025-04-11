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

from entities.auto_train_activation import AutoTrainActivation, NullAutoTrainActivation
from entities.dataset_item_count import DatasetItemCount, NullDatasetItemCount
from entities.dataset_item_labels import DatasetItemLabels, NullDatasetItemLabels
from service.project_service import ProjectService
from storage.repos import DatasetItemCountRepo, DatasetItemLabelsRepo
from storage.repos.auto_train_activation_repo import ProjectBasedAutoTrainActivationRepo

from geti_types import CTX_SESSION_VAR, DatasetStorageIdentifier, ProjectIdentifier


class TestProjectService:
    def test_delete_project_entities(
        self,
        fxt_db_project_service,
    ) -> None:
        # Arrange
        project = fxt_db_project_service.create_empty_project()
        project_identifier = ProjectIdentifier(workspace_id=project.workspace_id, project_id=project.id_)
        dataset_storage = project.get_training_dataset_storage()
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
        )

        auto_train_activation_repo = ProjectBasedAutoTrainActivationRepo(project_identifier)
        auto_train_activation_entity = AutoTrainActivation(
            task_node_id=project.id_,
            session=CTX_SESSION_VAR.get(),
        )
        auto_train_activation_repo.save(auto_train_activation_entity)

        dataset_item_count_repo = DatasetItemCountRepo(dataset_storage_identifier=dataset_storage_identifier)
        dataset_item_count_entity = DatasetItemCount(
            task_node_id=project.id_,
            task_label_data=[],
            n_dataset_items=1,
            n_items_per_label={},
            unassigned_dataset_items=[],
        )
        dataset_item_count_repo.save(dataset_item_count_entity)
        dataset_item_labels_repo = DatasetItemLabelsRepo(dataset_storage_identifier=dataset_storage_identifier)
        dataset_item_labels_entity = DatasetItemLabels(dataset_item_id=project.id_, label_ids=[])
        dataset_item_labels_repo.save(dataset_item_labels_entity)

        ProjectService.delete_entities(
            project_id=project.id_,
            workspace_id=project.workspace_id,
            dataset_storage_id=dataset_storage.id_,
        )

        # Assert
        assert isinstance(DatasetItemLabelsRepo(dataset_storage_identifier).get_one(), NullDatasetItemLabels)
        assert isinstance(DatasetItemCountRepo(dataset_storage_identifier).get_one(), NullDatasetItemCount)
        assert isinstance(auto_train_activation_repo.get_one(), NullAutoTrainActivation)
