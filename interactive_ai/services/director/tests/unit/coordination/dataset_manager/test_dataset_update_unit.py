# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import patch

import pytest

from coordination.dataset_manager.dataset_update import DatasetUpdateUseCase

from iai_core_py.entities.dataset_entities import TaskDataset
from iai_core_py.entities.datasets import Dataset
from iai_core_py.entities.subset import Subset
from iai_core_py.repos import AnnotationSceneRepo, DatasetRepo, ProjectRepo
from iai_core_py.utils.dataset_helper import DatasetHelper


class TestDatasetUpdateUseCase:
    def test_update_dataset_with_new_annotation_scene(
        self,
        fxt_db_project_service,
        fxt_mongo_id,
        fxt_annotation_scene,
        fxt_dataset_item,
    ) -> None:
        project = fxt_db_project_service.create_empty_project()
        dataset_storage = project.get_training_dataset_storage()
        pipeline_dataset_entity = fxt_db_project_service.get_pipeline_dataset()
        dataset_item = fxt_dataset_item()
        expected_new_items_dataset = Dataset(items=[fxt_dataset_item], id=fxt_mongo_id())
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=project) as mock_get_project,
            patch.object(AnnotationSceneRepo, "get_by_id", return_value=fxt_annotation_scene) as mock_get_scene,
            patch.object(
                DatasetHelper,
                "annotation_scene_to_dataset_item",
                return_value=[dataset_item],
            ) as mock_scene_to_item,
            patch.object(
                DatasetUpdateUseCase, "_update_dataset_with_new_items", return_value=None
            ) as mock_update_dataset,
            patch.object(DatasetRepo, "generate_id", return_value=fxt_mongo_id()) as mock_generate_id,
        ):
            DatasetUpdateUseCase.update_dataset_with_new_annotation_scene(
                project_id=project.id_, annotation_scene_id=fxt_annotation_scene.id_
            )

            mock_get_project.assert_called_once_with(project.id_)
            mock_get_scene.assert_called_once_with(fxt_annotation_scene.id_)
            mock_scene_to_item.assert_called_once_with(
                annotation_scene=fxt_annotation_scene,
                dataset_storage=dataset_storage,
                subset=Subset.UNASSIGNED,
            )
            mock_update_dataset.assert_called_once_with(
                new_items_dataset_for_task=expected_new_items_dataset,
                pipeline_dataset_entity=pipeline_dataset_entity,
                dataset_storage_identifier=dataset_storage.identifier,
                project=project,
            )
            mock_generate_id.assert_called_once_with()

    @pytest.mark.parametrize(
        "lazyfxt_dataset_item, lazyfxt_dataset",
        [
            ("fxt_dataset_item", "fxt_dataset"),
            ("fxt_empty_dataset_item", "fxt_empty_dataset"),
        ],
        ids=[
            "Non-empty dataset item",
            "Empty dataset item",
        ],
    )
    def test_update_dataset_with_new_items(
        self, request, fxt_db_project_service, lazyfxt_dataset_item, lazyfxt_dataset
    ) -> None:
        dataset_item = request.getfixturevalue(lazyfxt_dataset_item)()
        dataset = request.getfixturevalue(lazyfxt_dataset)
        project = fxt_db_project_service.create_empty_project()
        dataset_storage = project.get_training_dataset_storage()
        pipeline_dataset_entity = fxt_db_project_service.get_pipeline_dataset()
        labels = fxt_db_project_service.label_schema.get_labels(include_empty=True)
        label_ids = [label.id_ for label in labels]
        task_node = fxt_db_project_service.task_node_1
        media_identifiers = [item.media_identifier for item in dataset]
        with (
            patch.object(DatasetUpdateUseCase, "filter_dataset", return_value=dataset) as mock_filter_dataset,
            patch.object(
                TaskDataset,
                "get_dataset_items_for_media_identifiers",
                return_value=[dataset_item],
            ) as mock_get_dataset_items,
            patch.object(
                DatasetUpdateUseCase,
                "_set_subset_for_already_existing_annotations",
                return_value=None,
            ) as mock_set_subsets,
            patch.object(TaskDataset, "add_dataset", return_value=None) as mock_add_dataset,
        ):
            DatasetUpdateUseCase._update_dataset_with_new_items(
                new_items_dataset_for_task=dataset,
                pipeline_dataset_entity=pipeline_dataset_entity,
                project=project,
                dataset_storage_identifier=dataset_storage.identifier,
            )

            mock_filter_dataset.assert_called_once_with(dataset=dataset, task_label_ids=label_ids, task_node=task_node)
            mock_get_dataset_items.assert_called_once_with(
                media_identifiers=media_identifiers,
                dataset_storage_identifier=dataset_storage.identifier,
            )
            mock_set_subsets.assert_called_once_with(
                media_identifiers=media_identifiers,
                current_dataset_items_for_task=[dataset_item],
                new_items_dataset_for_task=dataset,
                task_label_ids=label_ids,
            )
            mock_add_dataset.assert_called_once_with(
                new_dataset=dataset,
                dataset_storage_identifier=dataset_storage.identifier,
            )

    def test_set_subset_for_already_existing_annotations(self, fxt_label, fxt_dataset_item, fxt_mongo_id) -> None:
        old_dataset_item = fxt_dataset_item()
        new_dataset_item = fxt_dataset_item()
        old_dataset_item.subset = Subset.TRAINING
        new_dataset_item.subset = Subset.UNASSIGNED
        new_dataset_item.roi = old_dataset_item.roi
        new_items_dataset = Dataset(items=[new_dataset_item], id=fxt_mongo_id())
        media_identifiers = [old_dataset_item.media_identifier]
        label_ids = new_dataset_item.annotation_scene.get_label_ids(include_empty=True)

        DatasetUpdateUseCase._set_subset_for_already_existing_annotations(
            media_identifiers=media_identifiers,
            current_dataset_items_for_task=[old_dataset_item],
            new_items_dataset_for_task=new_items_dataset,
            task_label_ids=label_ids,
        )

        assert new_dataset_item.subset == Subset.TRAINING

    def test_filter_dataset_items_removed(self, fxt_dataset_item, fxt_task, fxt_mongo_id) -> None:
        dataset_item = fxt_dataset_item()
        dataset = Dataset(items=[dataset_item], id=fxt_mongo_id())

        result = DatasetUpdateUseCase.filter_dataset(dataset=dataset, task_label_ids=[], task_node=fxt_task)

        assert len(result) == 0

    def test_filter_dataset_items_no_items_removed(self, fxt_dataset_item, fxt_task, fxt_mongo_id) -> None:
        dataset_item = fxt_dataset_item()
        item_label_ids = dataset_item.annotation_scene.get_label_ids(include_empty=True)
        dataset = Dataset(items=[dataset_item], id=fxt_mongo_id())

        result = DatasetUpdateUseCase.filter_dataset(dataset=dataset, task_label_ids=item_label_ids, task_node=fxt_task)

        assert len(result) == 1

    def test_delete_media_from_datasets(self, fxt_db_project_service, fxt_mongo_id) -> None:
        project = fxt_db_project_service.create_empty_project()
        dataset_storage = project.get_training_dataset_storage()
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=project) as mock_get_project,
            patch.object(TaskDataset, "remove_items_for_media", return_value=[fxt_mongo_id()]) as mock_remove_items,
        ):
            DatasetUpdateUseCase.delete_media_from_datasets(
                project_id=project.id_,
                media_id=fxt_mongo_id(),
            )

            mock_get_project.assert_called_once_with(project.id_)
            mock_remove_items.assert_called_once_with(
                media_id=fxt_mongo_id(),
                dataset_storage_identifier=dataset_storage.identifier,
            )
