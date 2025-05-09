# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os
import time
from unittest.mock import call, patch

from coordination.configuration_manager.task_node_config import TaskNodeConfig
from entities.dataset_item_count import DatasetItemCount, LabelData
from storage.repos import DatasetItemCountRepo
from storage.repos.auto_train_activation_repo import ProjectBasedAutoTrainActivationRepo
from usecases.auto_train import AutoTrainUseCase

from geti_types import CTX_SESSION_VAR, DatasetStorageIdentifier
from iai_core.configuration.elements.component_parameters import ComponentType
from iai_core.repos import ConfigurableParametersRepo, DatasetRepo


class TestAutoTrainUseCase:
    def test_debouncer(self, request, fxt_db_project_service):
        """
        <b>Description:</b>
        This tests checks that the debouncer properly delays 'check_auto_train' calls so that we don't immediately
        set auto-training readiness when requirements are met.

        <b>Input data:</b>
        An empty project

        <b>Steps:</b>
        1. Create the project and other necessary entities
        2. Quickly check auto training conditions twice and assert that auto-training is not activated
        3. Wait for >5 seconds and assert that auto-training readiness is set
        """
        # Create a project and get the required entities
        fxt_db_project_service.create_empty_project()
        with (
            patch.object(
                AutoTrainUseCase,
                "_check_conditions_and_set_auto_train_readiness",
                return_value=None,
            ) as mock_check_auto_train,
            patch.dict(os.environ, {"AUTO_TRAIN_DEBOUNCE_TIME": "0.5"}),
        ):
            auto_train_use_case = AutoTrainUseCase()
            request.addfinalizer(auto_train_use_case.stop)

            # Quickly check auto training twice and assert that auto-training is not checked
            auto_train_use_case._check_conditions_and_set_auto_train_readiness_debounce(
                project_identifier=fxt_db_project_service.project.identifier
            )
            time.sleep(0.1)
            auto_train_use_case._check_conditions_and_set_auto_train_readiness_debounce(
                project_identifier=fxt_db_project_service.project.identifier
            )
            mock_check_auto_train.assert_not_called()

            # Wait for the required amount of time and assert that auto-training is checked
            time.sleep(0.6)
            mock_check_auto_train.assert_called_with(
                project_identifier=fxt_db_project_service.project.identifier,
                session=CTX_SESSION_VAR.get(),
                bypass_debouncer=False,
            )

    def test_check_auto_train(self, request, fxt_db_project_service):
        """
        <b>Description:</b>
        This tests verifies that auto-training correctly checks the missing annotations
        and auto-training configuration

        <b>Input data:</b>
        A task chain project

        <b>Steps:</b>
        1. Create the task chain project and other necessary entities
        2. Set the number of dataset items in the counter for both tasks to 100 and
           set auto-training to True
        3. Let the AutoTrainUseCase scan for ready tasks and verify that auto-training readiness
           is set for both tasks.
        4. Set the number of dataset items in the counter for the second task to 0,
           making it non-ready. Verify that the first task gets auto-trained.
        5. Disable auto-train for the first task too, then verify that no task will now
           train automatically.
        """
        # Step 1: set up the task chain project
        workspace_id = fxt_db_project_service.workspace_id
        project = fxt_db_project_service.create_annotated_detection_classification_project()
        dataset_storage = fxt_db_project_service.dataset_storage
        labels = fxt_db_project_service.label_schema.get_labels(include_empty=True)
        task_node_1 = fxt_db_project_service.task_node_1
        task_node_2 = fxt_db_project_service.task_node_2
        trainable_task_nodes = [task_node_1, task_node_2]
        dataset_item_count_repo: DatasetItemCountRepo = DatasetItemCountRepo(
            dataset_storage_identifier=DatasetStorageIdentifier(
                workspace_id=workspace_id,
                project_id=project.id_,
                dataset_storage_id=dataset_storage.id_,
            ),
        )
        config_param_repo = ConfigurableParametersRepo(project.identifier)
        request.addfinalizer(lambda: dataset_item_count_repo.delete_all())

        # Step 2: for each task, set dataset item count to 100 and auto-training to True
        for task_node in trainable_task_nodes:
            dataset_item_count = DatasetItemCount(
                task_node_id=task_node.id_,
                task_label_data=[LabelData.from_label(label) for label in labels],
                n_dataset_items=100,
                n_items_per_label={},
                unassigned_dataset_items=[DatasetRepo.generate_id() for _ in range(100)],
            )
            dataset_item_count_repo.save(dataset_item_count)

            task_configuration = config_param_repo.get_or_create_component_parameters(
                data_instance_of=TaskNodeConfig,
                task_id=task_node.id_,
                component=ComponentType.TASK_NODE,
            )
            task_configuration.data.auto_training = True
            config_param_repo.save(task_configuration)

        # Step 3: let the AutoTrainUseCase scan for ready tasks and set their readiness
        with patch.object(
            ProjectBasedAutoTrainActivationRepo,
            "set_auto_train_readiness_by_task_id",
            return_value=None,
        ) as mock_set_readiness:
            AutoTrainUseCase._check_conditions_and_set_auto_train_readiness(
                session=CTX_SESSION_VAR.get(), project_identifier=project.identifier
            )
            mock_set_readiness.assert_has_calls(
                [
                    call(
                        task_node_id=task_node_1.id_,
                        readiness=True,
                        bypass_debouncer=True,
                        raise_exc_on_missing=False,
                    ),
                    call(
                        task_node_id=task_node_2.id_,
                        readiness=True,
                        bypass_debouncer=True,
                        raise_exc_on_missing=False,
                    ),
                ]
            )

        # Step 4: make the second task non-ready by removing the dataset items
        # from the count and assert only auto-training for the first task is activated
        second_task_dataset_item_count = dataset_item_count_repo.get_by_id(id_=task_node_2.id_)
        second_task_dataset_item_count.n_dataset_items = 0
        dataset_item_count_repo.save(second_task_dataset_item_count)
        with patch.object(
            ProjectBasedAutoTrainActivationRepo,
            "set_auto_train_readiness_by_task_id",
            return_value=None,
        ) as mock_set_readiness:
            AutoTrainUseCase._check_conditions_and_set_auto_train_readiness(
                session=CTX_SESSION_VAR.get(), project_identifier=project.identifier
            )
            mock_set_readiness.assert_has_calls(
                [
                    call(
                        task_node_id=task_node_1.id_,
                        readiness=True,
                        bypass_debouncer=True,
                        raise_exc_on_missing=False,
                    ),
                    call(
                        task_node_id=task_node_2.id_,
                        readiness=False,
                        bypass_debouncer=True,
                        raise_exc_on_missing=False,
                    ),
                ]
            )

        # Step 5: disable auto-training for the first task and assert that no tasks is set for auto-training
        task_configuration = config_param_repo.get_or_create_component_parameters(
            data_instance_of=TaskNodeConfig,
            task_id=trainable_task_nodes[0].id_,
            component=ComponentType.TASK_NODE,
        )
        task_configuration.data.auto_training = False
        config_param_repo.save(task_configuration)
        with patch.object(
            ProjectBasedAutoTrainActivationRepo,
            "set_auto_train_readiness_by_task_id",
            return_value=None,
        ) as mock_set_readiness:
            AutoTrainUseCase._check_conditions_and_set_auto_train_readiness(
                session=CTX_SESSION_VAR.get(), project_identifier=project.identifier
            )
            mock_set_readiness.assert_has_calls(
                [
                    call(
                        task_node_id=task_node_1.id_,
                        readiness=False,
                        bypass_debouncer=True,
                        raise_exc_on_missing=False,
                    ),
                    call(
                        task_node_id=task_node_2.id_,
                        readiness=False,
                        bypass_debouncer=True,
                        raise_exc_on_missing=False,
                    ),
                ]
            )
