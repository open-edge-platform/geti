# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import ANY, call, patch

import pytest
from iai_core_py.entities.dataset_entities import TaskDataset
from iai_core_py.entities.dataset_item import DatasetItem
from iai_core_py.entities.datasets import Dataset, DatasetPurpose
from iai_core_py.entities.project import Project
from iai_core_py.repos import DatasetRepo, LabelSchemaRepo

from jobs_common.utils.dataset_helpers import DatasetHelpers
from jobs_common.utils.subset_management.subset_manager import TaskSubsetManager


@pytest.mark.JobsComponent
class TestDatasetHelpers:
    def test_construct_and_save_train_dataset_for_task(
        self,
        fxt_session_ctx,
        fxt_detection_project,
        fxt_video_factory,
        fxt_video_frame_entity_factory,
        fxt_annotation_scene,
    ) -> None:
        project: Project = fxt_detection_project
        task_node = project.get_trainable_task_nodes()[0]
        dataset_storage = project.get_training_dataset_storage()
        video = fxt_video_factory()
        video_frames = [fxt_video_frame_entity_factory(video=video, index=i) for i in range(25)]
        input_dataset_items = [
            DatasetItem(
                id_=DatasetRepo.generate_id(),
                media=video_frame,
                annotation_scene=fxt_annotation_scene,
            )
            for video_frame in video_frames
        ]
        input_dataset = Dataset(items=input_dataset_items, id=DatasetRepo.generate_id())

        with (
            patch.object(LabelSchemaRepo, "get_latest_view_by_task") as mock_get_label_schema,
            patch.object(TaskDataset, "get_dataset", return_value=input_dataset) as mock_get_dataset,
            patch.object(TaskSubsetManager, "split") as mock_split,
            patch.object(TaskDataset, "save_subsets") as mock_save_subsets,
            patch("jobs_common.utils.dataset_helpers.publish_event") as mock_publish_event,
            patch.object(DatasetRepo, "save_deep") as mock_save_deep,
        ):
            train_dataset = DatasetHelpers.construct_and_save_train_dataset_for_task(
                task_dataset_entity=TaskDataset(
                    task_node_id=task_node.id_,
                    dataset_storage_id=project.training_dataset_storage_id,
                    dataset_id=input_dataset.id_,
                ),
                project_id=project.id_,
                task_node=task_node,
                dataset_storage=dataset_storage,
                max_training_dataset_size=1000,
                reshuffle_subsets=True,
            )

        mock_get_label_schema.assert_called_once_with(task_node_id=task_node.id_)
        mock_get_dataset.assert_called_once_with(dataset_storage=project.get_training_dataset_storage())
        mock_split.assert_called_once()
        mock_save_subsets.assert_called_once_with(
            dataset=input_dataset, dataset_storage_identifier=dataset_storage.identifier
        )
        mock_publish_event.assert_has_calls(
            [
                # two calls to dataset_updated because the dataset size is 25 and the max chunk size is 20
                call(topic="dataset_updated", body=ANY, key=str(task_node.id_).encode(), headers_getter=ANY),
                call(topic="dataset_updated", body=ANY, key=str(task_node.id_).encode(), headers_getter=ANY),
            ]
        )
        mock_save_deep.assert_called_once_with(train_dataset)
        assert train_dataset.purpose == DatasetPurpose.TRAINING
        assert len(train_dataset) == len(input_dataset)
