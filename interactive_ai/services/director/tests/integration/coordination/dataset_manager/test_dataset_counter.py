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

from math import ceil, log
from unittest.mock import patch

from coordination.dataset_manager.dataset_counter import DatasetCounterUseCase
from coordination.dataset_manager.dataset_counter_config import DatasetCounterConfig
from coordination.dataset_manager.dynamic_required_num_annotations import DynamicRequiredAnnotations
from coordination.dataset_manager.missing_annotations_helper import MissingAnnotationsHelper

from geti_types import DatasetStorageIdentifier
from sc_sdk.configuration.elements.component_parameters import ComponentType
from sc_sdk.entities.metrics import NullPerformance, Performance, ScoreMetric
from sc_sdk.entities.model import Model
from sc_sdk.entities.subset import Subset
from sc_sdk.repos import ConfigurableParametersRepo, DatasetRepo, EvaluationResultRepo, LabelSchemaRepo, ModelRepo
from sc_sdk.repos.dataset_entity_repo import PipelineDatasetRepo


class TestDatasetCounter:
    def test_get_task_required_annotations(
        self,
        request,
        fxt_db_project_service,
        fxt_empty_dataset,
        fxt_dataset_item,
    ):
        """
        <b>Description:</b>

        <b>Input data:</b>

        <b>Steps:</b>
        1. Initialize a PipelineDataset and save a configuration
        2. Check that the correct required number is given for an empty dataset
        3. Add two annotations and check that the required number reduces by 2
        4. Set label constraint to True, and assert that now the unused label has 10 required annotations for both
         manual and auto-training.
        5. Add enough annotations to start training, and simulate that training has been started by setting the subsets
         in the dataset. Assert that manual training now has 0 required annotations, but auto training needs 7 more
         annotations to start. Assert that the label constraint is no longer enforced, as it is not relevant for
         retraining.
        """
        project = fxt_db_project_service.create_empty_project()
        dataset_storage = fxt_db_project_service.dataset_storage
        label_schema = fxt_db_project_service.label_schema
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
        )

        # Step 1
        with patch.object(
            LabelSchemaRepo,
            "get_latest_view_by_task",
            return_value=label_schema,
        ):
            pipeline_dataset_entity = PipelineDatasetRepo.get_or_create(dataset_storage_identifier)
            request.addfinalizer(lambda: PipelineDatasetRepo(dataset_storage_identifier).delete_all())
            task_node = project.get_trainable_task_nodes()[0]
            task_dataset = pipeline_dataset_entity.task_datasets[task_node.id_]

            config_params_repo = ConfigurableParametersRepo(project_identifier=project.identifier)
            dataset_counter_config = config_params_repo.get_or_create_component_parameters(
                data_instance_of=DatasetCounterConfig,
                component=ComponentType.DATASET_COUNTER,
                task_id=task_node.id_,
            )
            dataset_counter_config.data.required_images_auto_training = 10
            dataset_counter_config.data.label_constraint_first_training = False
            # The "use_dynamic_required_annotations" has to be False to test if the above value
            # of required_images_auto_training is used correctly
            dataset_counter_config.data.use_dynamic_required_annotations = False
            config_params_repo.save(dataset_counter_config)

            # Step 2
            DatasetCounterUseCase.on_dataset_update(
                workspace_id=project.workspace_id,
                project_id=project.id_,
                task_node_id=task_node.id_,
                dataset_id=task_dataset.dataset_id,
                new_dataset_items=[],
                deleted_dataset_items=[],
                assigned_dataset_items=[],
            )
            missing_annotations = MissingAnnotationsHelper.get_missing_annotations_for_task(
                dataset_storage_identifier=dataset_storage.identifier,
                task_node=task_node,
            )
            assert missing_annotations.total_missing_annotations_auto_training == 10
            assert missing_annotations.total_missing_annotations_manual_training == 3
            assert missing_annotations.missing_annotations_per_label == {}

            # Step 3
            dataset = fxt_empty_dataset
            for _i in range(2):
                dataset.append(fxt_dataset_item())
            dataset_repo = DatasetRepo(dataset_storage.identifier)
            dataset_repo.save_deep(dataset)
            request.addfinalizer(lambda: dataset_repo.delete_by_id(dataset.id_))

            task_dataset.add_dataset(
                new_dataset=dataset,
                dataset_storage_identifier=dataset_storage.identifier,
            )
            DatasetCounterUseCase.on_dataset_update(
                workspace_id=project.workspace_id,
                project_id=project.id_,
                dataset_id=task_dataset.dataset_id,
                task_node_id=task_node.id_,
                new_dataset_items=[dataset_item.id_ for dataset_item in dataset],
                deleted_dataset_items=[],
                assigned_dataset_items=[],
            )
            missing_annotations = MissingAnnotationsHelper.get_missing_annotations_for_task(
                dataset_storage_identifier=dataset_storage.identifier,
                task_node=task_node,
            )
            assert missing_annotations.total_missing_annotations_auto_training == 8
            assert missing_annotations.total_missing_annotations_manual_training == 1

            # Step 4
            dataset_counter_config.data.label_constraint_first_training = True
            config_params_repo.save(dataset_counter_config)
            missing_annotations = MissingAnnotationsHelper.get_missing_annotations_for_task(
                dataset_storage_identifier=dataset_storage.identifier,
                task_node=task_node,
            )
            labels = fxt_db_project_service.label_schema.get_labels(include_empty=False)
            assert missing_annotations.missing_annotations_per_label == {label.id_: 10 for label in labels}
            assert missing_annotations.total_missing_annotations_auto_training == 10

            # Step 5
            new_items_dataset = fxt_empty_dataset
            for _i in range(8):
                new_items_dataset.append(fxt_dataset_item())
            dataset_repo.save_deep(new_items_dataset)
            request.addfinalizer(lambda: dataset_repo.delete_by_id(new_items_dataset.id_))

            pipeline_dataset_entity.task_datasets[task_node.id_].add_dataset(
                new_dataset=new_items_dataset,
                dataset_storage_identifier=dataset_storage_identifier,
            )
            full_dataset = task_dataset.get_dataset(dataset_storage=dataset_storage)
            for item in full_dataset:
                item.subset = Subset.TRAINING
            task_dataset.save_subsets(
                dataset=full_dataset,
                dataset_storage_identifier=dataset_storage.identifier,
            )
            DatasetCounterUseCase.on_dataset_update(
                workspace_id=project.workspace_id,
                project_id=project.id_,
                dataset_id=task_dataset.dataset_id,
                task_node_id=task_node.id_,
                new_dataset_items=[dataset_item.id_ for dataset_item in new_items_dataset],
                deleted_dataset_items=[],
                assigned_dataset_items=[dataset_item.id_ for dataset_item in full_dataset],
            )
            missing_annotations = MissingAnnotationsHelper.get_missing_annotations_for_task(
                dataset_storage_identifier=dataset_storage.identifier,
                task_node=task_node,
            )
            assert missing_annotations.total_missing_annotations_auto_training == 10
            assert missing_annotations.total_missing_annotations_manual_training == 0
            assert missing_annotations.missing_annotations_per_label == {}

    def test_get_task_required_annotations_label_schema_change(
        self,
        request,
        fxt_db_project_service,
        fxt_classification_label_factory,
        fxt_dataset_storage,
    ):
        """
        This test checks that the required annotations counter is updated properly
        upon a label schema change

        Steps:
        1. Create project and training dataset
        2. Simulate label addition by adding a label to the dataset
        3. Request missing annotation count, without signalling label schema change
        4. Signal label schema change to dataset counter
        5. Request missing annotation count again and verify that it has changed
        """
        # Step 1: Create project and training dataset
        project = fxt_db_project_service.create_annotated_detection_classification_project(num_images_per_label=5)
        DatasetCounterUseCase.on_project_create(workspace_id=project.workspace_id, project_id=project.id_)
        task_node = project.get_trainable_task_nodes()[0]
        dataset_storage = project.get_training_dataset_storage()

        config_params_repo = ConfigurableParametersRepo(project.identifier)
        dataset_counter_config = config_params_repo.get_or_create_component_parameters(
            data_instance_of=DatasetCounterConfig,
            component=ComponentType.DATASET_COUNTER,
            task_id=task_node.id_,
        )
        dataset_counter_config.data.label_constraint_first_training = True
        config_params_repo.save(dataset_counter_config)

        missing_annotations = MissingAnnotationsHelper.get_missing_annotations_for_task(
            dataset_storage_identifier=dataset_storage.identifier,
            task_node=task_node,
        )
        assert len(missing_annotations.missing_annotations_per_label) == 1
        assert missing_annotations.total_missing_annotations_auto_training == 12

        # Step 2: Add classification label to the dataset
        new_label = fxt_classification_label_factory(0)
        project_label_schema = fxt_db_project_service.label_schema
        project_label_schema.add_labels_to_group_by_group_name(
            group_name=project_label_schema.get_groups()[0].name, labels=[new_label]
        )
        task_label_schema = fxt_db_project_service.label_schema_1
        task_label_schema.add_labels_to_group_by_group_name(
            group_name=task_label_schema.get_groups()[0].name, labels=[new_label]
        )
        label_schema_repo = LabelSchemaRepo(project.identifier)
        label_schema_repo.save(project_label_schema)
        label_schema_repo.save(task_label_schema)
        request.addfinalizer(lambda: label_schema_repo.delete_all())
        DatasetCounterUseCase.on_project_update(workspace_id=project.workspace_id, project_id=project.id_)

        # Step 3: Request missing annotations based on previous and new dataset
        missing_annotations = MissingAnnotationsHelper.get_missing_annotations_for_task(
            dataset_storage_identifier=dataset_storage.identifier,
            task_node=task_node,
        )
        assert len(missing_annotations.missing_annotations_per_label) == 2
        assert missing_annotations.total_missing_annotations_auto_training == 24


class TestDynamicRequiredAnnotations:
    @staticmethod
    def calculate_required_num_images(current_performance, dataset_count):
        """
        Formula for calculating the required number of images for auto-training. This is essentially the same
        calculation used in DynamicRequiredAnnotations.
        :param current_performance: Current performance of the latest model
        :param dataset_count: Number of images used (for train/val/test) till the last round
        :return: Required number of images for auto-training
        """
        # Estimated target performance is 10 % relative improvement from current performance
        target_performance = current_performance * 1.1
        target_performance = min(target_performance, 0.9999)
        if current_performance >= 1.0:
            return dataset_count
        required_images = ceil(((log(1 - target_performance) / log(1 - current_performance)) - 1) * dataset_count)
        return 12 if required_images < 12 else required_images

    def test_dynamic_required_annotations(
        self,
        request,
        fxt_db_project_service,
        fxt_empty_dataset,
        fxt_dataset_item,
    ):
        """
        Test to check if the dynamic required annotations' calculation is done correctly and
        is updated in the missing annotations

        Steps:
        1. Create a project and a training dataset
        2. Case 1 - check if without use_dynamic_required_annotations, the missing annotations are the same as
            default value
        3. Set the use_dynamic_required_annotations to True
        4. Add 100 new dataset items - 90 assigned(used) and 10 unassigned.
        5. Case 2 - Check if without any active model, the missing annotations are calculated correctly (default value)
        6. Case 3 - Model with zero performance - check if the missing annotations are still the default
        7. Case 4 - Model with a performance of 0.5 - check if the missing annotations are calculated correctly
        8. Case 5 - Model with a performance of 0.95 (target performance goes above 1.0) -  check if the missing
            annotations are calculated correctly by clipping target performance to not go beyond 1.0
        9. Case 6 - Model with a performance of 1.0 - Check if the number of missing annotations is the same as current
                    dataset size
        """

        # Create a project and training dataset
        project = fxt_db_project_service.create_annotated_detection_project(num_images_per_label=5)

        dataset_storage = project.get_training_dataset_storage()
        pipeline_dataset_entity = PipelineDatasetRepo.get_or_create(
            dataset_storage_identifier=dataset_storage.identifier
        )

        DatasetCounterUseCase.on_project_create(workspace_id=project.workspace_id, project_id=project.id_)

        task_node = project.get_trainable_task_nodes()[0]

        config_params_repo = ConfigurableParametersRepo(project.identifier)

        dataset_counter_config = config_params_repo.get_or_create_component_parameters(
            data_instance_of=DatasetCounterConfig,
            component=ComponentType.DATASET_COUNTER,
            task_id=task_node.id_,
        )
        config_params_repo.save(dataset_counter_config)

        # By default, the use_dynamic_required_annotations should be True
        assert dataset_counter_config.data.use_dynamic_required_annotations is True

        # Set the "use_dynamic_required_annotations" to False
        dataset_counter_config.data.use_dynamic_required_annotations = False
        config_params_repo.save(dataset_counter_config)

        missing_annotations = MissingAnnotationsHelper.get_missing_annotations_for_task(
            dataset_storage_identifier=dataset_storage.identifier,
            task_node=task_node,
        )

        # Case 1: Dynamic required annotations is not used.
        # Check if the number of missing annotations are the same as the default value
        assert missing_annotations.total_missing_annotations_auto_training == 12

        # Set the "use_dynamic_required_annotations" to True
        dataset_counter_config.data.use_dynamic_required_annotations = True
        config_params_repo.save(dataset_counter_config)

        # Add 100 new dataset items - 90 assigned(used) and 10 unassigned.
        dataset_repo = DatasetRepo(dataset_storage.identifier)
        new_items_dataset = fxt_empty_dataset

        total_num_images = 100
        num_images_assigned = 90

        for k in range(total_num_images):
            new_items_dataset.append(fxt_dataset_item())

        dataset_repo.save_deep(new_items_dataset)
        request.addfinalizer(lambda: dataset_repo.delete_by_id(new_items_dataset.id_))

        pipeline_dataset_entity.task_datasets[task_node.id_].add_dataset(
            new_dataset=new_items_dataset,
            dataset_storage_identifier=dataset_storage.identifier,
        )

        DatasetCounterUseCase.on_dataset_update(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_id=pipeline_dataset_entity.task_datasets[task_node.id_].dataset_id,
            task_node_id=task_node.id_,
            new_dataset_items=[dataset_item.id_ for dataset_item in new_items_dataset],
            deleted_dataset_items=[],
            assigned_dataset_items=[dataset_item.id_ for dataset_item in new_items_dataset[:num_images_assigned]],
        )

        assert (
            DynamicRequiredAnnotations._get_model_performance_and_dataset_size(project=project, task_node=task_node)[0]
            == NullPerformance()
        )

        DynamicRequiredAnnotations.on_model_activated(project_identifier=project.identifier, task_node_id=task_node.id_)

        missing_annotations = MissingAnnotationsHelper.get_missing_annotations_for_task(
            dataset_storage_identifier=dataset_storage.identifier,
            task_node=task_node,
        )
        # Case 2: No active model, so the missing annotations should be calculated based on the default value.
        assert missing_annotations.total_missing_annotations_auto_training == (
            12 - (total_num_images - num_images_assigned)
        )

        # Dummy model - otherwise DynamicRequiredAnnotations._update_dynamic_required_num_annotations() will return
        # without calculation if there is no model or a NullModel
        dummy_model = fxt_db_project_service.create_and_save_model()

        # model's test accuracy
        model_performance = 0.0
        with (
            patch.object(
                ModelRepo,
                "get_latest",
                return_value=dummy_model,
            ),
            patch.object(
                EvaluationResultRepo,
                "get_performance_by_model_ids",
                return_value=Performance(score=ScoreMetric(value=model_performance, name="accuracy")),
            ),
            patch.object(
                Model,
                "get_train_dataset",
                return_value=new_items_dataset[:num_images_assigned],
            ),
        ):
            DynamicRequiredAnnotations.on_model_activated(
                project_identifier=project.identifier, task_node_id=task_node.id_
            )

        missing_annotations = MissingAnnotationsHelper.get_missing_annotations_for_task(
            dataset_storage_identifier=dataset_storage.identifier,
            task_node=task_node,
        )

        # Case 3: When model performance is 0 - the number shouldn't have changed
        assert missing_annotations.total_missing_annotations_auto_training == (
            12 - (total_num_images - num_images_assigned)
        )

        # When model performance is non-zero - the required number of annotations should match the calculation
        # Case 4: Model performance is a normal number - 0.5
        # Case 5: Model performance is quite high (0.9) such that target performance when calculated is > 1.0 but is
        # (supposed to be)clipped is at 0.9999
        # Case 6: Model performance is already 1.0 - required number of annotations should match the current
        # dataset size
        model_performances = [0.5, 0.9, 1.0]
        for model_performance in model_performances:
            with (
                patch.object(
                    ModelRepo,
                    "get_latest",
                    return_value=dummy_model,
                ),
                patch.object(
                    EvaluationResultRepo,
                    "get_performance_by_model_ids",
                    return_value=Performance(score=ScoreMetric(value=model_performance, name="accuracy")),
                ),
                patch.object(
                    Model,
                    "get_train_dataset",
                    return_value=new_items_dataset[:num_images_assigned],
                ),
            ):
                DynamicRequiredAnnotations.on_model_activated(
                    project_identifier=project.identifier, task_node_id=task_node.id_
                )

            required_num_annotations = self.calculate_required_num_images(
                current_performance=model_performance, dataset_count=num_images_assigned
            )

            missing_annotations = MissingAnnotationsHelper.get_missing_annotations_for_task(
                dataset_storage_identifier=dataset_storage.identifier,
                task_node=task_node,
            )

            assert missing_annotations.total_missing_annotations_auto_training == (
                required_num_annotations - (total_num_images - num_images_assigned)
            )
