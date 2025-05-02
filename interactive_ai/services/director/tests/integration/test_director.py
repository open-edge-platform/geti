# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from typing import cast
from unittest.mock import patch

from tests.test_helpers import get_unannotated_dataset

from coordination.dataset_manager.dataset_counter import DatasetCounterUseCase
from coordination.dataset_manager.dataset_counter_config import DatasetCounterConfig
from coordination.dataset_manager.dataset_update import DatasetUpdateUseCase
from coordination.dataset_manager.missing_annotations_helper import MissingAnnotationsHelper
from storage.repos.auto_train_activation_repo import ProjectBasedAutoTrainActivationRepo
from usecases.auto_train import AutoTrainUseCase

from geti_types import CTX_SESSION_VAR
from iai_core_py.configuration.elements.component_parameters import ComponentType
from iai_core_py.repos import ConfigurableParametersRepo, ImageRepo
from iai_core_py.repos.dataset_entity_repo import PipelineDatasetRepo


class TestIntegrationDirector:
    def test_annotation_training_workflow(self, fxt_db_project_service) -> None:
        """
        <b>Description:</b>
        The test checks a standard workflow for the director:
        upload images, annotate images, change configuration and start training.

        <b>Input data:</b>
        An empty project, three dummy images and annotations

        <b>Expected results:</b>
        The dataset manager is capable of fetching a correct unannotated dataset
        Auto-train is triggered when the required number of annotated media is met

        <b>Steps</b>
        1. Create an empty detection project and initialize coordinator
        2. Assert that the unannotated dataset is empty and that the
           number of required annotations is the default from the DatasetCounterConfig
        3. Create and save three images
        4. Assert that the active set and unannotated dataset now contain the three images
        5. Create and save annotation scenes and states for the images
        6. Assert that the images are removed from the unannotated dataset,
           and the required number of annotations goes down by three.
        7. Set the number of required annotations to three and check that training is triggered.
        """
        # 1. Create an empty detection project
        fxt_db_project_service.create_empty_project()
        project = fxt_db_project_service.project
        task_node = fxt_db_project_service.task_node_1
        dataset_storage = fxt_db_project_service.dataset_storage

        # 2. Assert that the unannotated datasets is empty,
        # and that the number of required annotations is the default one
        unannotated_dataset = get_unannotated_dataset(
            project=project,
            dataset_storage=dataset_storage,
        )
        assert len(unannotated_dataset) == 0

        DatasetCounterUseCase.on_project_create(
            workspace_id=project.workspace_id,
            project_id=project.id_,
        )
        missing_annotations = MissingAnnotationsHelper.get_missing_annotations_for_task(
            dataset_storage_identifier=dataset_storage.identifier,
            task_node=task_node,
        )
        default_required_annotations = DatasetCounterConfig().get_metadata(  # type: ignore[call-arg]
            parameter_name="required_images_auto_training"
        )["default_value"]
        assert missing_annotations.total_missing_annotations_auto_training == default_required_annotations

        # 3. Create and save three images
        for i in range(3):
            fxt_db_project_service.create_and_save_random_image(name="image" + str(i))

        # 4. Assert that the active set and unannotated dataset now contain the three images
        unannotated_dataset = get_unannotated_dataset(
            project=project,
            dataset_storage=dataset_storage,
        )
        assert len(unannotated_dataset) == 3

        # 5. Create and save annotation scenes and states for the images
        for image in ImageRepo(dataset_storage.identifier).get_all():
            annotation_scene = fxt_db_project_service.create_and_save_random_annotation_scene(
                image=image,
                labels=fxt_db_project_service.label_schema_1.get_labels(include_empty=False),
            )

            DatasetUpdateUseCase.update_dataset_with_new_annotation_scene(
                project_id=project.id_,
                annotation_scene_id=annotation_scene.id_,
            )
        pipeline_dataset_entity = PipelineDatasetRepo.get_or_create(dataset_storage.identifier)
        task_dataset = pipeline_dataset_entity.task_datasets[task_node.id_]
        new_dataset_item_ids = [item.id_ for item in task_dataset.get_dataset(dataset_storage=dataset_storage)]

        DatasetCounterUseCase.on_dataset_update(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            task_node_id=task_node.id_,
            new_dataset_items=new_dataset_item_ids,
            deleted_dataset_items=[],
            assigned_dataset_items=[],
            dataset_id=task_dataset.dataset_id,
        )

        # 6. Assert that the images are removed from unannotated dataset,
        # and the required number of annotations goes down by three.
        unannotated_dataset = get_unannotated_dataset(
            project=project,
            dataset_storage=dataset_storage,
        )
        assert len(unannotated_dataset) == 0
        missing_annotations = MissingAnnotationsHelper.get_missing_annotations_for_task(
            dataset_storage_identifier=dataset_storage.identifier,
            task_node=task_node,
        )
        assert missing_annotations.total_missing_annotations_auto_training == default_required_annotations - 3

        # 7. Set the number of required annotations to three and check that training is triggered.
        with patch.object(
            ProjectBasedAutoTrainActivationRepo, "set_auto_train_readiness_by_task_id"
        ) as mock_set_readiness:
            config_repo = ConfigurableParametersRepo(project.identifier)
            config = config_repo.get_or_create_component_parameters(
                data_instance_of=DatasetCounterConfig,
                component=ComponentType.DATASET_COUNTER,
                task_id=task_node.id_,
            )
            configuration = cast("DatasetCounterConfig", config.data)
            configuration.required_images_auto_training = 3
            config_repo.save(config)
            fxt_db_project_service._set_auto_train(True)
            AutoTrainUseCase._check_conditions_and_set_auto_train_readiness(
                session=CTX_SESSION_VAR.get(),
                project_identifier=project.identifier,
            )
            missing_annotations = MissingAnnotationsHelper.get_missing_annotations_for_task(
                dataset_storage_identifier=dataset_storage.identifier,
                task_node=task_node,
            )
            assert missing_annotations.total_missing_annotations_auto_training == 0
            mock_set_readiness.assert_called_once_with(
                task_node_id=task_node.id_, readiness=True, bypass_debouncer=True, raise_exc_on_missing=False
            )
