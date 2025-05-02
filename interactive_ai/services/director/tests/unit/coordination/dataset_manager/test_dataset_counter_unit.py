# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import patch

from coordination.dataset_manager.dataset_counter import DatasetCounterUseCase
from entities.dataset_item_count import DeletedDatasetItemCountData, NewDatasetItemCountData, NullDatasetItemCount
from entities.dataset_item_labels import DatasetItemLabels, NullDatasetItemLabels
from service.label_schema_service import LabelSchemaService
from storage.repos import DatasetItemCountRepo, DatasetItemLabelsRepo

from iai_core_py.entities.label import Label
from iai_core_py.repos import DatasetRepo, ProjectRepo
from iai_core_py.utils.dataset_helper import DatasetHelper


class TestDatasetCounterUseCase:
    def test_on_project_create_count_not_present(self, request, fxt_project, fxt_label_schema) -> None:
        """
        Tests the 'on_project_create' method when the dataset item count is not yet present in the repo
        """
        task_node = fxt_project.get_trainable_task_nodes()[0]
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project) as mock_get_project,
            patch.object(
                DatasetItemCountRepo,
                "get_by_id",
                return_value=NullDatasetItemCount(),
            ) as mock_get_dataset_item_count,
            patch.object(DatasetItemCountRepo, "save", return_value=None) as mock_save_dataset_item_count,
            patch.object(
                LabelSchemaService,
                "get_latest_label_schema_for_task",
                return_value=fxt_label_schema,
            ) as mock_get_label_schema,
        ):
            DatasetCounterUseCase.on_project_create(workspace_id=fxt_project.workspace_id, project_id=fxt_project.id_)

            mock_get_project.assert_called_once_with(fxt_project.id_)
            mock_get_label_schema.assert_called_once_with(
                project_identifier=fxt_project.identifier,
                task_node_id=task_node.id_,
            )
            mock_get_dataset_item_count.assert_called_once_with(id_=task_node.id_)
            mock_save_dataset_item_count.assert_called_once()

    def test_on_project_create_count_present(
        self,
        request,
        fxt_project,
        fxt_label_schema,
        fxt_empty_dataset_item_count,
    ) -> None:
        """
        Tests the 'on_project_create' method when the dataset item count is already present in the repo
        """
        task_node = fxt_project.get_trainable_task_nodes()[0]
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project) as mock_get_project,
            patch.object(
                DatasetItemCountRepo,
                "get_by_id",
                return_value=fxt_empty_dataset_item_count,
            ) as mock_get_dataset_item_count,
            patch.object(DatasetItemCountRepo, "save", return_value=None) as mock_save_dataset_item_count,
            patch.object(
                LabelSchemaService,
                "get_latest_label_schema_for_task",
                return_value=fxt_label_schema,
            ) as mock_get_label_schema,
        ):
            DatasetCounterUseCase.on_project_create(workspace_id=fxt_project.workspace_id, project_id=fxt_project.id_)

            mock_get_project.assert_called_once_with(fxt_project.id_)
            mock_get_label_schema.assert_called_once_with(
                project_identifier=fxt_project.identifier,
                task_node_id=task_node.id_,
            )
            mock_get_dataset_item_count.assert_called_once_with(id_=task_node.id_)
            mock_save_dataset_item_count.assert_not_called()

    def test_on_project_update(
        self,
        request,
        fxt_project,
        fxt_label,
        fxt_empty_dataset_item_count,
    ) -> None:
        assert fxt_empty_dataset_item_count.task_label_data[0].name == "dog"
        task_node = fxt_project.get_trainable_task_nodes()[0]
        renamed_label = Label(
            name="renamed",
            domain=fxt_label.domain,
            color=fxt_label.color,
            hotkey=fxt_label.hotkey,
            creation_date=fxt_label.creation_date,
            id_=fxt_label.id_,
            ephemeral=False,
        )
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project) as mock_get_project,
            patch.object(
                DatasetItemCountRepo,
                "get_by_id",
                return_value=fxt_empty_dataset_item_count,
            ) as mock_get_dataset_item_count,
            patch.object(DatasetItemCountRepo, "save", return_value=None) as mock_save_dataset_item_count,
            patch.object(
                LabelSchemaService,
                "get_latest_labels_for_task",
                return_value=[renamed_label],
            ) as mock_get_label_schema,
        ):
            result = DatasetCounterUseCase.on_project_update(
                workspace_id=fxt_project.workspace_id, project_id=fxt_project.id_
            )

            mock_get_project.assert_called_once_with(fxt_project.id_)
            mock_get_label_schema.assert_called_once_with(
                project_identifier=fxt_project.identifier,
                task_node_id=task_node.id_,
                include_empty=False,
            )
            mock_get_dataset_item_count.assert_called_once_with(id_=task_node.id_)
            mock_save_dataset_item_count.assert_called_once_with(fxt_empty_dataset_item_count)
            assert fxt_empty_dataset_item_count.task_label_data[0].name == "renamed"
            assert result is None

    def test_on_dataset_update(
        self,
        request,
        fxt_project,
        fxt_label_schema,
        fxt_mongo_id,
        fxt_dataset_item,
    ) -> None:
        # Arrange
        new_dataset_item = fxt_dataset_item(0)
        deleted_dataset_item = fxt_dataset_item(1)
        assigned_dataset_item = fxt_dataset_item(2)
        task_node = fxt_project.get_trainable_task_nodes()[0]
        dataset_id = fxt_mongo_id(0)
        labels = fxt_label_schema.get_labels(include_empty=False)
        new_dataset_item_count_data = NewDatasetItemCountData(
            count=1,
            dataset_item_ids=[new_dataset_item.id_],
            per_label_count={labels[0]: 1},
        )
        deleted_dataset_item_count_data = DeletedDatasetItemCountData(
            count=1,
            dataset_item_ids=[deleted_dataset_item.id_],
            per_label_count={labels[0]: 1},
        )

        # Act
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project) as mock_get_project,
            patch.object(
                DatasetCounterUseCase,
                "_process_new_items",
                return_value=new_dataset_item_count_data,
            ) as mock_process_new_items,
            patch.object(
                DatasetCounterUseCase,
                "_process_deleted_items",
                return_value=deleted_dataset_item_count_data,
            ) as mock_process_deleted_items,
            patch.object(DatasetItemCountRepo, "update_count_data", return_value=None) as mock_save_dataset_item_count,
            patch.object(
                LabelSchemaService,
                "get_latest_labels_for_task",
                return_value=labels,
            ) as mock_get_task_labels,
        ):
            DatasetCounterUseCase.on_dataset_update(
                workspace_id=fxt_project.workspace_id,
                project_id=fxt_project.id_,
                task_node_id=task_node.id_,
                dataset_id=dataset_id,
                new_dataset_items=[new_dataset_item.id_],
                deleted_dataset_items=[deleted_dataset_item.id_],
                assigned_dataset_items=[assigned_dataset_item.id_],
            )

        # Assert
        mock_get_project.assert_called_once_with(fxt_project.id_)
        mock_process_new_items.assert_called_once_with(
            dataset_storage_identifier=fxt_project.get_training_dataset_storage().identifier,
            task_node=task_node,
            task_label_ids=[label.id_ for label in labels],
            dataset_id=dataset_id,
            new_item_ids=[new_dataset_item.id_],
        )
        mock_process_deleted_items.assert_called_once_with(
            dataset_storage_identifier=fxt_project.get_training_dataset_storage().identifier,
            deleted_item_ids=[deleted_dataset_item.id_],
        )
        mock_save_dataset_item_count.assert_called_once_with(
            id_=task_node.id_,
            new_dataset_item_count_data=new_dataset_item_count_data,
            deleted_dataset_item_count_data=deleted_dataset_item_count_data,
            assigned_dataset_items=[assigned_dataset_item.id_],
        )
        mock_get_task_labels.assert_called_once_with(
            project_identifier=fxt_project.identifier,
            task_node_id=task_node.id_,
            include_empty=False,
        )

    def test_process_new_items(
        self,
        request,
        fxt_dataset_storage,
        fxt_task,
        fxt_mongo_id,
        fxt_dataset_item,
    ) -> None:
        # Arrange
        new_dataset_item = fxt_dataset_item()
        new_dataset_item_label_ids = list(
            DatasetHelper.get_dataset_item_label_ids(new_dataset_item, include_empty=False)
        )
        expected_dataset_item_labels = DatasetItemLabels(
            dataset_item_id=new_dataset_item.id_,
            label_ids=new_dataset_item_label_ids,
        )
        dataset_id = fxt_mongo_id()

        # Act
        with (
            patch.object(DatasetRepo, "get_items_from_dataset", return_value=[new_dataset_item]) as mock_get_items,
            patch.object(DatasetItemLabelsRepo, "save_many", return_value=None) as mock_save_many,
        ):
            new_dataset_item_count = DatasetCounterUseCase._process_new_items(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                task_node=fxt_task,
                task_label_ids=new_dataset_item_label_ids,
                dataset_id=dataset_id,
                new_item_ids=[new_dataset_item.id_],
            )

        # Assert
        mock_get_items.assert_called_once_with(dataset_id=dataset_id, dataset_item_ids=[new_dataset_item.id_])
        mock_save_many.assert_called_once_with(instances=[expected_dataset_item_labels])
        assert new_dataset_item_count.count == 1
        assert new_dataset_item_count.dataset_item_ids == [new_dataset_item.id_]
        assert new_dataset_item_count.per_label_count == dict.fromkeys(new_dataset_item_label_ids, 1)

    def test_process_new_items_empty(
        self,
        request,
        fxt_dataset_storage,
        fxt_task,
        fxt_mongo_id,
        fxt_empty_dataset_item,
    ) -> None:
        # Arrange
        new_dataset_item = fxt_empty_dataset_item()
        new_dataset_item_label_ids = list(
            DatasetHelper.get_dataset_item_label_ids(new_dataset_item, include_empty=False)
        )
        dataset_id = fxt_mongo_id()

        # Act
        with (
            patch.object(DatasetRepo, "get_items_from_dataset", return_value=[new_dataset_item]) as mock_get_items,
            patch.object(DatasetItemLabelsRepo, "save_many", return_value=None),
        ):
            new_dataset_item_count = DatasetCounterUseCase._process_new_items(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                task_node=fxt_task,
                task_label_ids=new_dataset_item_label_ids,
                dataset_id=dataset_id,
                new_item_ids=[new_dataset_item.id_],
            )

        # Assert
        mock_get_items.assert_called_once_with(dataset_id=dataset_id, dataset_item_ids=[new_dataset_item.id_])
        assert new_dataset_item_count.count == 0
        assert new_dataset_item_count.dataset_item_ids == []
        assert new_dataset_item_count.per_label_count == {}

    def test_process_deleted_items(
        self,
        request,
        fxt_dataset_item,
        fxt_dataset_storage,
    ) -> None:
        # Arrange
        deleted_dataset_item = fxt_dataset_item()
        deleted_dataset_item_label_ids = list(
            DatasetHelper.get_dataset_item_label_ids(deleted_dataset_item, include_empty=False)
        )
        dataset_item_labels = DatasetItemLabels(
            dataset_item_id=deleted_dataset_item.id_,
            label_ids=deleted_dataset_item_label_ids,
        )

        # Act
        with (
            patch.object(
                DatasetItemLabelsRepo,
                "get_by_id",
                return_value=dataset_item_labels,
            ) as mock_get_dataset_item_labels,
            patch.object(DatasetItemLabelsRepo, "delete_by_id", return_value=None) as mock_delete_dataset_item_labels,
        ):
            delete_dataset_item_count_data = DatasetCounterUseCase._process_deleted_items(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                deleted_item_ids=[deleted_dataset_item.id_],
            )

        # Assert
        mock_get_dataset_item_labels.assert_called_once_with(deleted_dataset_item.id_)
        mock_delete_dataset_item_labels.assert_called_once_with(deleted_dataset_item.id_)
        assert delete_dataset_item_count_data.count == 1
        assert delete_dataset_item_count_data.dataset_item_ids == [deleted_dataset_item.id_]
        assert sum(delete_dataset_item_count_data.per_label_count.values()) == 1

    def test_process_deleted_items_label_not_exist(
        self,
        request,
        fxt_empty_dataset_item,
        fxt_dataset_storage,
    ) -> None:
        """
        Checks that if the label is not present in label data, the method does not fail and still correctly
        decrements the total counter.
        """
        # Arrange
        deleted_dataset_item = fxt_empty_dataset_item()

        # Act
        with (
            patch.object(
                DatasetItemLabelsRepo,
                "get_by_id",
                return_value=NullDatasetItemLabels(),
            ) as mock_get_dataset_item_labels,
            patch.object(DatasetItemLabelsRepo, "delete_by_id", return_value=None) as mock_delete_dataset_item_labels,
        ):
            delete_dataset_item_count_data = DatasetCounterUseCase._process_deleted_items(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                deleted_item_ids=[deleted_dataset_item.id_],
            )

        # Assert
        mock_get_dataset_item_labels.assert_called_once_with(deleted_dataset_item.id_)
        mock_delete_dataset_item_labels.assert_called_once_with(deleted_dataset_item.id_)
        assert delete_dataset_item_count_data.count == 0
        assert delete_dataset_item_count_data.dataset_item_ids == [deleted_dataset_item.id_]
        assert sum(delete_dataset_item_count_data.per_label_count.values()) == 0
