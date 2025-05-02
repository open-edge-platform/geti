# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import call, patch

import pytest

from coordination.dataset_manager.dataset_suspender import DatasetSuspender

from iai_core_py.entities.annotation_scene_state import AnnotationSceneState
from iai_core_py.entities.dataset_entities import PipelineDataset, TaskDataset
from iai_core_py.entities.dataset_item import DatasetItem
from iai_core_py.entities.suspended_scenes import SuspendedAnnotationScenesDescriptor
from iai_core_py.repos import ProjectRepo, SuspendedAnnotationScenesRepo
from iai_core_py.repos.dataset_entity_repo import PipelineDatasetRepo
from iai_core_py.utils.dataset_helper import DatasetHelper


def do_nothing(*args, **kwargs):
    pass


@pytest.fixture
def mock_suspended_ann_scenes_descriptor_repo():
    with patch.object(SuspendedAnnotationScenesRepo, "__init__", new=do_nothing):
        yield


class TestDatasetSuspender:
    def test_suspend_dataset_items(
        self,
        mock_project_repo,
        mock_suspended_ann_scenes_descriptor_repo,
        fxt_ote_id,
        fxt_detection_classification_chain_project,
    ) -> None:
        workspace_id = fxt_ote_id(0)
        project = fxt_detection_classification_chain_project
        dataset_storage = project.get_training_dataset_storage()
        suspended_ann_scenes_descriptor = SuspendedAnnotationScenesDescriptor(
            id_=SuspendedAnnotationScenesRepo.generate_id(),
            project_id=project.id_,
            dataset_storage_id=dataset_storage,
            scenes_ids=(fxt_ote_id(1), fxt_ote_id(2)),
        )
        task_dataset_entities = {
            task_node.id_: TaskDataset(
                task_node_id=task_node.id_,
                dataset_storage_id=dataset_storage.id_,
                dataset_id=fxt_ote_id(3),
            )
            for task_node in project.get_trainable_task_nodes()
        }
        pipeline_dataset_entity = PipelineDataset(
            project_id=project.id_,
            task_datasets=task_dataset_entities,
            dataset_storage_id=dataset_storage.id_,
        )
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=project) as mock_get_project,
            patch.object(
                SuspendedAnnotationScenesRepo,
                "get_by_id",
                return_value=suspended_ann_scenes_descriptor,
            ) as mock_get_descriptor,
            patch.object(SuspendedAnnotationScenesRepo, "delete_by_id") as mock_delete_descriptor,
            patch.object(
                PipelineDatasetRepo, "get_or_create", return_value=pipeline_dataset_entity
            ) as mock_get_pipeline_dataset,
            patch.object(
                DatasetSuspender, "suspend_items_by_annotation_scene_ids_for_task"
            ) as mock_suspend_items_by_scene_for_task,
        ):
            DatasetSuspender.suspend_dataset_items(
                suspended_scenes_descriptor_id=suspended_ann_scenes_descriptor.id_,
                workspace_id=workspace_id,
                project_id=project.id_,
            )

            mock_get_project.assert_called_once_with(project.id_)
            mock_get_descriptor.assert_called_once_with(suspended_ann_scenes_descriptor.id_)
            mock_get_pipeline_dataset.assert_called_once_with(dataset_storage.identifier)
            mock_suspend_items_by_scene_for_task.assert_has_calls(
                [
                    call(
                        annotation_scene_ids=suspended_ann_scenes_descriptor.scenes_ids,
                        task_dataset_entity=next(iter(task_dataset_entities.values())),
                        project=project,
                        dataset_storage=dataset_storage,
                    ),
                    call(
                        annotation_scene_ids=suspended_ann_scenes_descriptor.scenes_ids,
                        task_dataset_entity=list(task_dataset_entities.values())[1],
                        project=project,
                        dataset_storage=dataset_storage,
                    ),
                ]
            )
            mock_delete_descriptor.assert_called_once_with(suspended_ann_scenes_descriptor.id_)

    def test_suspend_items_by_annotation_scene_ids_for_task(
        self,
        fxt_ote_id,
        fxt_project,
        fxt_dataset_non_empty,
    ) -> None:
        project = fxt_project
        dataset_storage = project.get_training_dataset_storage()
        task_dataset_entity = TaskDataset(
            task_node_id=fxt_ote_id(1),
            dataset_storage_id=fxt_ote_id(2),
            dataset_id=fxt_ote_id(3),
        )
        annotation_scene_ids = [fxt_ote_id(4), fxt_ote_id(5)]
        with (
            patch.object(task_dataset_entity, "get_dataset", return_value=fxt_dataset_non_empty),
            patch.object(task_dataset_entity, "save_dataset"),
            patch.object(
                DatasetHelper, "compute_dataset_item_ignored_label_ids"
            ) as mock_compute_item_ignored_label_ids,
        ):
            DatasetSuspender.suspend_items_by_annotation_scene_ids_for_task(
                annotation_scene_ids=annotation_scene_ids,
                task_dataset_entity=task_dataset_entity,
                project=project,
                dataset_storage=dataset_storage,
            )

        assert mock_compute_item_ignored_label_ids.call_count == len(fxt_dataset_non_empty)

    @pytest.mark.parametrize("cropped", [False, True], ids=["first task", "second task"])
    def test_set_item_ignored_label_ids(
        self,
        cropped,
        fxt_ote_id,
        fxt_dataset_item,
        fxt_dataset_storage,
        fxt_media_identifier,
        fxt_detection_label_factory,
    ) -> None:
        # if cropped, the dummy dataset item will use the first annotation as ROI
        dataset_item = fxt_dataset_item(cropped=cropped)
        labels = [fxt_detection_label_factory(i) for i in range(6)]  # 6 dummy labels
        label_ids = {label.id_ for label in labels}
        revisited_labels_full_scene = {labels[0].id_, labels[1].id_}
        revisited_labels_per_annotation = {
            dataset_item.annotation_scene.annotations[0].id_: (
                labels[2].id_,
                labels[3].id_,
            ),
            dataset_item.annotation_scene.annotations[1].id_: (
                labels[4].id_,
                labels[5].id_,
            ),
        }
        annotation_scene_state = AnnotationSceneState(
            id_=fxt_ote_id(7),
            media_identifier=fxt_media_identifier,
            annotation_scene_id=fxt_ote_id(8),
            annotation_state_per_task={},
            unannotated_rois={},
            labels_to_revisit_full_scene=revisited_labels_full_scene,
            labels_to_revisit_per_annotation=revisited_labels_per_annotation,
        )
        with patch.object(DatasetItem, "get_shapes_label_ids", return_value=label_ids):
            result = DatasetHelper.compute_dataset_item_ignored_label_ids(
                item=dataset_item,
                dataset_storage=fxt_dataset_storage,
                annotation_scene_state=annotation_scene_state,
            )

        if cropped:
            assert result == {labels[2].id_, labels[3].id_}  # first ann
        else:
            assert result == {labels[0].id_, labels[1].id_}  # full scene
