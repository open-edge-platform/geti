# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from coordination.dataset_manager.dataset_update import DatasetUpdateUseCase

from iai_core.entities.annotation import AnnotationScene
from iai_core.entities.subset import Subset
from iai_core.repos import AnnotationSceneRepo
from iai_core.repos.dataset_entity_repo import PipelineDatasetRepo


class TestDatasetUpdateUseCase:
    def test_add_and_delete_annotation_scene(self, fxt_db_project_service):
        """
        <b>Description:</b>
        Tests that DatasetUpdateUseCase.update_dataset_with_new_annotation_scene properly adds new annotation scenes to
        the dataset and DatasetUpdateUseCase.delete_media_from_datasets properly deletes them.

        <b>Input data:</b>
        An empty detection project

        <b>Steps</b>
        1. Create a detection project
        2. Add an image and annotate it
        3. Add the annotation to the dataset using update_dataset_with_new_annotation_scene and assert that
        the dataset now contains one item
        4. Add an image and annotate it with the empty label
        5. Add the annotation to the dataset and assert that the dataset now contains two items
        6. Delete the dataset items for the media using delete_media_from_datasets and assert that the number of
        dataset items is now 0
        """
        # Create empty project
        fxt_db_project_service.create_empty_project()

        # Create an image and annotation and update the dataset
        image = fxt_db_project_service.create_and_save_random_image("dummy_image")
        annotation_label = fxt_db_project_service.label_schema.get_labels(include_empty=False)[0]
        annotation_scene = fxt_db_project_service.create_and_save_random_annotation_scene(
            image=image, labels=[annotation_label]
        )
        DatasetUpdateUseCase.update_dataset_with_new_annotation_scene(
            project_id=fxt_db_project_service.project.id_,
            annotation_scene_id=annotation_scene.id_,
        )

        # Assert that the dataset was updated correctly
        pipeline_dataset_entity = PipelineDatasetRepo.get_or_create(fxt_db_project_service.dataset_storage.identifier)
        task_dataset_entity = pipeline_dataset_entity.task_datasets[fxt_db_project_service.task_node_1.id_]
        dataset = task_dataset_entity.get_dataset(dataset_storage=fxt_db_project_service.dataset_storage)
        assert len(dataset) == 1
        assert dataset[0].media_identifier.media_id == image.id_
        assert dataset[0].annotation_scene == annotation_scene

        # Add an annotation with the empty label and assert that is also added correctly
        image2 = fxt_db_project_service.create_and_save_random_image("dummy_image")
        empty_label = next(
            label for label in fxt_db_project_service.label_schema.get_labels(include_empty=True) if label.is_empty
        )
        annotation_scene_empty_label = fxt_db_project_service.create_and_save_random_annotation_scene(
            image=image2, labels=[empty_label], full_size_rectangle=True
        )
        DatasetUpdateUseCase.update_dataset_with_new_annotation_scene(
            project_id=fxt_db_project_service.project.id_,
            annotation_scene_id=annotation_scene_empty_label.id_,
        )
        dataset = task_dataset_entity.get_dataset(dataset_storage=fxt_db_project_service.dataset_storage)
        assert len(dataset) == 2
        assert dataset[1].media_identifier.media_id == image2.id_
        assert dataset[1].annotation_scene == annotation_scene_empty_label

        DatasetUpdateUseCase.delete_media_from_datasets(
            project_id=fxt_db_project_service.project.id_,
            media_id=image.id_,
        )
        DatasetUpdateUseCase.delete_media_from_datasets(
            project_id=fxt_db_project_service.project.id_,
            media_id=image2.id_,
        )
        dataset = task_dataset_entity.get_dataset(dataset_storage=fxt_db_project_service.dataset_storage)
        assert len(dataset) == 0

    def test_copy_subsets_for_identical_annotation(self, fxt_db_project_service):
        """
        <b>Description:</b>
        Tests that DatasetUpdateUseCase.update_dataset_with_new_annotation_scene properly copies the subset from
        previous dataset items, in the case that the annotations are identical.

        <b>Input data:</b>
        An empty detection project

        <b>Steps</b>
        1. Create a detection project
        2. Add an image and annotate it
        3. Add the annotation to the dataset using update_dataset_with_new_annotation_scene
        4. Manually set the dataset item's subset to 'TRAINING' to simulate that it has been trained
        5. Add the same annotation to the dataset again, with a new annotation scene and annotation ID
        6. Assert that the new dataset item refers to the new annotation scene, but still has the 'TRAINING' subset
        from the previous dataset item
        7. Add another annotation scene to the dataset for the same media, this time a non-identical one
        8. Assert that this new dataset item has the 'UNASSIGNED' subset, as it is a new item.
        """
        # Create empty project with an annotated image and pass that annotation to the dataset update mechanism
        fxt_db_project_service.create_empty_project()
        image = fxt_db_project_service.create_and_save_random_image("dummy_image")
        annotation_label = fxt_db_project_service.label_schema.get_labels(include_empty=False)[0]
        annotation_scene_1 = fxt_db_project_service.create_and_save_random_annotation_scene(
            image=image, labels=[annotation_label]
        )
        DatasetUpdateUseCase.update_dataset_with_new_annotation_scene(
            project_id=fxt_db_project_service.project.id_,
            annotation_scene_id=annotation_scene_1.id_,
        )

        # Set the subset of the dataset item to TRAINED to simulate training of that item
        pipeline_dataset_entity = PipelineDatasetRepo.get_or_create(fxt_db_project_service.dataset_storage.identifier)
        task_dataset_entity = pipeline_dataset_entity.task_datasets[fxt_db_project_service.task_node_1.id_]
        dataset = task_dataset_entity.get_dataset(dataset_storage=fxt_db_project_service.dataset_storage)
        dataset[0].subset = Subset.TRAINING
        task_dataset_entity.save_subsets(
            dataset=dataset,
            dataset_storage_identifier=fxt_db_project_service.dataset_storage.identifier,
        )

        # Make an annotation scene that is identical, save it and pass it to the dataset update mechanism
        annotation_scene_2 = AnnotationScene(
            kind=annotation_scene_1.kind,
            media_identifier=annotation_scene_1.media_identifier,
            media_height=annotation_scene_1.media_height,
            media_width=annotation_scene_1.media_width,
            id_=AnnotationSceneRepo.generate_id(),
            annotations=annotation_scene_1.annotations,
        )
        annotation_scene_2 = fxt_db_project_service.save_annotation_scene_and_state(annotation_scene=annotation_scene_2)
        DatasetUpdateUseCase.update_dataset_with_new_annotation_scene(
            project_id=fxt_db_project_service.project.id_,
            annotation_scene_id=annotation_scene_2.id_,
        )

        # Assert that the new dataset item correctly has the same subset as the previous item had before
        dataset = task_dataset_entity.get_dataset(dataset_storage=fxt_db_project_service.dataset_storage)
        assert len(dataset) == 1
        assert dataset[0].subset == Subset.TRAINING

        # Now, upload an annotation scene that is NOT identical to the dataset update mechanism
        annotation_scene_3 = fxt_db_project_service.create_and_save_random_annotation_scene(
            image=image, labels=[annotation_label]
        )
        DatasetUpdateUseCase.update_dataset_with_new_annotation_scene(
            project_id=fxt_db_project_service.project.id_,
            annotation_scene_id=annotation_scene_3.id_,
        )

        # Assert that the new dataset item has the subset 'UNASSIGNED' as it should be regarded as a new item
        dataset = task_dataset_entity.get_dataset(dataset_storage=fxt_db_project_service.dataset_storage)
        assert len(dataset) == 1
        assert dataset[0].subset == Subset.UNASSIGNED
