# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from geti_types import ID
from iai_core.entities.subset import Subset
from iai_core.repos import AnnotationSceneRepo
from iai_core.repos.dataset_entity_repo import PipelineDatasetRepo


class TestDataset:
    def test_dataset_entity(self, request, fxt_db_project_service, fxt_dataset_non_empty):
        """
        <b>Description:</b>
        Check that the PipelineDataset and TaskDataset behave as expected.

        <b>Input data:</b>
        A detection project and a non-empty dataset

        <b>Expected results:</b>
        Test passes if the TaskDataset and PipelineDataset behave as expected

        <b>Steps</b>
        1. Create a project with a detection task
        2. Create the pipeline dataset and assert it has the proper project and task IDs
        3. Add a dataset to the task dataset entity and assert that the items are properly added, testing add_dataset
        4. Update the subsets and save, then assert that the subsets are updated, testing save_dataset
        5. Remove a list of media identifiers, testing remove_items_for_media_identifiers
        6. Re-add the dataset and remove media, testing remove_items_for_media
        """
        project = fxt_db_project_service.create_empty_project()
        dataset_storage = fxt_db_project_service.dataset_storage
        task_node = fxt_db_project_service.task_node_1
        annotation_scene_repo = AnnotationSceneRepo(dataset_storage.identifier)

        # Create pipeline dataset and assert it has the correct project and tasks
        pipeline_dataset = PipelineDatasetRepo.get_or_create(dataset_storage.identifier)
        assert pipeline_dataset.project_id == project.id_
        assert [task_node.id_] == list(pipeline_dataset.task_datasets.keys())
        task_dataset_entity = pipeline_dataset.task_datasets[task_node.id_]
        assert len(task_dataset_entity.get_dataset(dataset_storage)) == 0

        # Add a dataset to the task dataset entity and assert that the items are properly added
        for item in fxt_dataset_non_empty:
            item.annotation_scene.id_ = ID()
            annotation_scene_repo.save(item.annotation_scene)
        task_dataset_entity.add_dataset(
            new_dataset=fxt_dataset_non_empty,
            dataset_storage_identifier=dataset_storage.identifier,
        )
        updated_dataset = task_dataset_entity.get_dataset(dataset_storage=dataset_storage)
        assert len(updated_dataset) == len(fxt_dataset_non_empty)

        # Update the subsets and save, then assert that the subsets are updated
        for item in updated_dataset:
            item.subset = Subset.TRAINING
        task_dataset_entity.save_dataset(
            dataset=updated_dataset,
            dataset_storage_identifier=dataset_storage.identifier,
        )
        updated_dataset_2 = task_dataset_entity.get_dataset(dataset_storage=dataset_storage)
        assert all(item.subset == Subset.TRAINING for item in updated_dataset_2)

        # Delete the media identifiers for the dataset items, and check that they are properly deleted.
        media_identifiers = {item.media_identifier for item in updated_dataset_2}
        task_dataset_entity.remove_items_for_media_identifiers(
            media_identifiers=list(media_identifiers),
            dataset_storage_identifier=dataset_storage.identifier,
        )
        updated_dataset_3 = task_dataset_entity.get_dataset(dataset_storage=dataset_storage)
        assert len(updated_dataset_3) == 0

        # Re-add the dataset and remove it for the media, then check that the dataset items are properly deleted
        task_dataset_entity.add_dataset(
            new_dataset=fxt_dataset_non_empty,
            dataset_storage_identifier=dataset_storage.identifier,
        )
        media_ids = {item.media_identifier.media_id for item in fxt_dataset_non_empty}
        for media_id in media_ids:
            task_dataset_entity.remove_items_for_media(
                media_id=media_id, dataset_storage_identifier=dataset_storage.identifier
            )
        updated_dataset_5 = task_dataset_entity.get_dataset(dataset_storage=dataset_storage)
        assert len(updated_dataset_5) == 0
