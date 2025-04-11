# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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
from unittest.mock import patch

import pytest

from communication.controllers.optimization_controller import OptimizationController
from communication.exceptions import NotReadyForOptimizationException

from geti_types import ID
from grpc_interfaces.job_submission.client import GRPCJobsClient
from sc_sdk.entities.datasets import Dataset
from sc_sdk.entities.model import ModelOptimizationType
from sc_sdk.entities.model_template import EntryPoints
from sc_sdk.repos import DatasetRepo, ModelRepo


class TestOptimizationController:
    def test_start_pot_job(self, fxt_db_project_service, fxt_pot_hyperparameters, fxt_mock_jobs_client) -> None:
        """
        <b>Description:</b>
        Test POT optimization job creation

        <b>Input data:</b>
        1. A dummy project and model
        2. A dummy optimization config as dictionary

        <b>Expected results:</b>
        Test passes if:
        1. Job has been submitted
        2. Returned dictionary contains correct name and project_id.

        <b>Steps</b>
        1. Create an instance of the OptimizationController, which starts the Director as
            well
        2. Mock get_by_id from ProjectRepo, ModelStorageRepo
           and ModelRepo
        3. Mock submit from the GRPCJobsClient
        4. Run start_optimization
        5. Assert GRPCJobsClient.submit has been called
        6. Assert returned Job REST view contains correct name and project_id
        7. Stop the Director
        """
        # Arrange
        project = fxt_db_project_service.create_annotated_detection_project()
        task_node = fxt_db_project_service.task_node_1
        dataset_storage = fxt_db_project_service.dataset_storage
        model = fxt_db_project_service.create_and_save_model(hyper_parameters=fxt_pot_hyperparameters.data)
        model.optimization_type = ModelOptimizationType.NONE
        model.model_storage.model_template.entrypoints = EntryPoints(base="Base interface", nncf="NNCF interface")
        model_repo = ModelRepo(model.model_storage_identifier)
        model_repo.save(model)
        # Act
        with patch.object(GRPCJobsClient, "submit", return_value=None):
            result = OptimizationController().start_optimization(
                project_id=project.id_,
                model_storage_id=model.model_storage.id_,
                model_id=model.id_,
                author=ID("dummy_user"),
            )

        # Assert
        fxt_mock_jobs_client._jobs_client.submit.assert_called_once_with(
            priority=1,
            job_name="Optimization",
            job_type="optimize_pot",
            key=f'{{"dataset_storage_id": "{dataset_storage.id_}",'
            f' "model_storage_id": "{model.model_storage.id_}",'
            f' "optimization_parameters": {{"stat_subset_size": 300}},'
            f' "project_id": "{project.id_}",'
            f' "type": "optimize_pot",'
            f' "workspace_id": "{project.workspace_id}"}}',
            payload={
                "dataset_storage_id": dataset_storage.id_,
                "model_id": model.id_,
                "model_storage_id": model.model_storage.id_,
                "project_id": project.id_,
                "enable_optimize_from_dataset_shard": True,
                "max_number_of_annotations": None,
                "min_annotation_size": None,
            },
            metadata={
                "base_model_id": model.id_,
                "model_storage_id": model.model_storage.id_,
                "optimization_type": "POT",
                "optimized_model_id": None,
                "project": {
                    "id": project.id_,
                    "name": "test annotated detection project",
                },
                "task": {
                    "model_architecture": "mock_detection",
                    "model_template_id": "detection",
                    "task_id": task_node.id_,
                },
            },
            duplicate_policy="reject",
            gpu_num_required=None,
            author=ID("dummy_user"),
            project_id=project.id_,
            cancellable=True,
            cost=None,
        )
        model_repo.get_by_id(model.id_)
        assert result["job_id"] is not None

    def test_optimization_not_possible(
        self,
        fxt_db_project_service,
        fxt_pot_hyperparameters,
    ) -> None:
        """
        <b>Description:</b>
        Test that the optimization controller raises the correct errors when optimization is not possible

        <b>Input data:</b>
        1. An model with an empty dataset
        2. A model that can be optimized

        <b>Expected results:</b>
        Test passes if:
        1. Requesting optimization for a model with an empty dataset is blocked
        2. Requesting optimization twice for a model with same parameters is blocked

        <b>Steps</b>
        1. Create an instance of the OptimizationController, which starts the Director as
            well
        2. Mock get_by_id from ProjectRepo, ModelStorageRepo
            and ModelRepo
        3. Check that NotReadyForOptimizationException if the dataset is empty
        """
        # Arrange
        project = fxt_db_project_service.create_annotated_detection_project()

        empty_dataset = Dataset(id=DatasetRepo.generate_id())
        model_empty_dataset = fxt_db_project_service.create_and_save_model(dataset=empty_dataset)
        model_empty_dataset.optimization_type = ModelOptimizationType.NONE
        model_repo = ModelRepo(model_empty_dataset.model_storage.identifier)
        model_repo.save(model_empty_dataset)

        model = fxt_db_project_service.create_and_save_model(hyper_parameters=fxt_pot_hyperparameters.data)
        model.optimization_type = ModelOptimizationType.NONE
        model.model_storage.model_template.entrypoints = EntryPoints(base="Base interface", nncf="NNCF interface")
        model_repo.save(model)

        # Act
        with pytest.raises(NotReadyForOptimizationException):
            OptimizationController().start_optimization(
                project_id=project.id_,
                model_storage_id=model_empty_dataset.model_storage.id_,
                model_id=model_empty_dataset.id_,
                author=ID("dummy_user"),
            )
