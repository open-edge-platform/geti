# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from tests.fixtures.database import DETECTION_CLASSIFICATION_PIPELINE_DATA  # type: ignore[attr-defined]

from iai_core_py.entities.datasets import DatasetPurpose
from iai_core_py.entities.label import Domain
from iai_core_py.repos import DatasetRepo
from iai_core_py.utils.dataset_helper import DatasetHelper


class TestDatasetCreation:
    def test_create_task_inference_dataset(self, request, fxt_db_project_service) -> None:
        """
        <b>Description:</b>
        Tests that create_task_inference_dataset_from_media_identifiers properly creates a dataset for task inference

        <b>Input data:</b>
        A task chain project with a media and annotation scene

        <b>Steps</b>
        1. Create a detection->classification project.
        2. Add an image and an annotation scene with a detection and classification label
        3. Generate an inference dataset for the classification task with the image
           and assert the dataset with one item is properly created
        4. Check that the dataset was correctly saved in the repo
        """
        model_templates = fxt_db_project_service.create_detection_classification_model_templates()
        project = fxt_db_project_service.create_empty_project(
            pipeline_data=DETECTION_CLASSIFICATION_PIPELINE_DATA,
            model_templates=model_templates,
        )
        dataset_storage = fxt_db_project_service.dataset_storage
        image = fxt_db_project_service.create_and_save_random_image(name="dummy_image")
        labels = fxt_db_project_service.label_schema.get_labels(include_empty=False)
        detection_label = next(label for label in labels if label.domain == Domain.DETECTION)
        classification_label = next(label for label in labels if label.domain == Domain.CLASSIFICATION)
        fxt_db_project_service.create_and_save_random_annotation_scene(
            image=image, labels=[detection_label, classification_label]
        )

        task_inference_dataset = DatasetHelper.create_dataset_up_to_task_from_media_identifiers(
            media_identifiers=[image.media_identifier],
            task_node=fxt_db_project_service.task_node_2,
            project=project,
            dataset_storage=dataset_storage,
            dataset_purpose=DatasetPurpose.TASK_INFERENCE,
            save_to_db=True,
        )

        # Assert that the dataset is created with the correct media and prediction scene
        assert len(task_inference_dataset) == 1
        dataset_item = task_inference_dataset[0]
        assert dataset_item.media_identifier == image.media_identifier
        assert dataset_item.annotation_scene.media_identifier == image.media_identifier
        assert len(dataset_item.annotation_scene.annotations) == 1

        # Assert that the dataset in the repo is consistent with the one that was created
        dataset_from_repo = DatasetRepo(dataset_storage.identifier).get_by_id(task_inference_dataset.id_)
        assert dataset_from_repo == task_inference_dataset
        dataset_item = dataset_from_repo[0]
        assert dataset_item.annotation_scene.media_identifier == image.media_identifier
        assert len(dataset_item.annotation_scene.annotations) == 1
