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
"""
ConfigurationManager tests
"""

from unittest.mock import patch

import pytest

from configuration import ConfigurableComponentRegister
from configuration.configuration_manager import ConfigurationManager

import sc_sdk.configuration.helper as otx_config_helper
from geti_fastapi_tools.exceptions import ModelNotFoundException
from geti_types import ID
from sc_sdk.configuration.elements.component_parameters import ComponentParameters, ComponentType
from sc_sdk.entities.model import NullModel
from sc_sdk.entities.model_storage import ModelStorage
from sc_sdk.repos import ConfigurableParametersRepo, ModelRepo, ModelStorageRepo, ProjectRepo
from sc_sdk.services.model_service import ModelService

WORKSPACE_ID = ID("workspace_id")


class TestConfigurationManager:
    def test_get_configuration_for_model(
        self,
        fxt_mongo_id,
        fxt_project_with_detection_task,
        fxt_model,
        fxt_model_storage_detection,
    ):
        detection_task = fxt_project_with_detection_task.tasks[-1]

        with (
            patch.object(ModelRepo, "get_by_id", return_value=fxt_model),
            patch.object(
                ConfigurationManager,
                "_ConfigurationManager__get_model_storages_by_task_id",
                return_value=[fxt_model_storage_detection],
            ),
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project_with_detection_task),
        ):
            (
                model_configuration,
                model_storage_id,
            ) = ConfigurationManager().get_configuration_for_model(
                workspace_id=fxt_project_with_detection_task.workspace_id,
                project_id=fxt_project_with_detection_task.id_,
                task_id=detection_task.id_,
                model_id=fxt_mongo_id(),
            )

        assert model_configuration == fxt_model.configuration.configurable_parameters
        assert model_storage_id == fxt_model_storage_detection.id_

    def test_get_configuration_for_algorithm_uninitialized_model_storage(
        self,
        fxt_project_with_detection_task,
        fxt_default_model_hyper_parameters,
        fxt_model_template_detection,
    ):
        # Arrange
        detection_task = fxt_project_with_detection_task.tasks[-1]
        algorithm_name = "test_model_template_id"

        # Set a non-default value for one of the parameters to make sure we're not
        # just returning the defaults, upon comparison later on
        fxt_default_model_hyper_parameters.learning_parameters.batch_size = 200
        fxt_model_template_detection.hyper_parameters.manually_set_data_and_validate(
            otx_config_helper.convert(
                fxt_default_model_hyper_parameters.data,
                target=dict,
                enum_to_str=True,
                id_to_str=True,
            )
        )
        model_storage = ModelStorage(
            id_=ModelStorageRepo.generate_id(),
            project_id=fxt_project_with_detection_task.id_,
            task_node_id=detection_task.id_,
            model_template=fxt_model_template_detection,
        )

        # Act
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project_with_detection_task),
            patch.object(ConfigurableParametersRepo, "save", return_value=None) as mock_save_hyper_parameters,
            patch.object(
                ModelService,
                "get_or_create_model_storage",
                return_value=model_storage,
            ) as mock_get_model_storage,
        ):
            hyper_parameters = ConfigurationManager().get_configuration_for_algorithm(
                workspace_id=fxt_project_with_detection_task.workspace_id,
                project_id=fxt_project_with_detection_task.id_,
                task_id=detection_task.id_,
                algorithm_name=algorithm_name,
            )

        # Assert
        mock_save_hyper_parameters.assert_called_once_with(hyper_parameters)
        mock_get_model_storage.assert_called_once_with(
            task_node=detection_task,
            model_template_id=algorithm_name,
            project_identifier=fxt_project_with_detection_task.identifier,
        )

        # Compare hyper parameters, ID's will differ but that is expected
        assert fxt_default_model_hyper_parameters.id_ != ID()
        hyper_parameters.id_ = fxt_default_model_hyper_parameters.id_
        assert hyper_parameters.data == fxt_default_model_hyper_parameters.data

    def test_get_configuration_for_algorithm_initialized_model_storage(
        self,
        fxt_project_with_detection_task,
        fxt_default_model_hyper_parameters,
        fxt_model_template_detection,
        fxt_model_storage_detection,
    ):
        # Arrange
        detection_task = fxt_project_with_detection_task.tasks[-1]
        algorithm_name = "test_model_template_id"

        # Set a non-default value for one of the parameters to make sure we're not
        # just returning the defaults, upon comparison later on
        fxt_default_model_hyper_parameters.learning_parameters.batch_size = 200
        fxt_model_template_detection.hyper_parameters.manually_set_data_and_validate(
            otx_config_helper.convert(
                fxt_default_model_hyper_parameters.data,
                target=dict,
                enum_to_str=True,
                id_to_str=True,
            )
        )
        fxt_model_template_detection.model_template_id = algorithm_name
        fxt_model_storage_detection._model_template = fxt_model_template_detection

        # Act
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project_with_detection_task),
            patch.object(
                ModelStorageRepo,
                "get_by_task_node_id",
                return_value=[fxt_model_storage_detection],
            ) as mock_get_model_storages,
            patch.object(
                ConfigurableParametersRepo,
                "get_or_create_hyper_parameters",
                return_value=fxt_default_model_hyper_parameters,
            ) as mock_get_hyper_parameters,
        ):
            hyper_parameters = ConfigurationManager().get_configuration_for_algorithm(
                workspace_id=fxt_project_with_detection_task.workspace_id,
                project_id=fxt_project_with_detection_task.id_,
                task_id=detection_task.id_,
                algorithm_name=algorithm_name,
            )

        # Assert
        assert hyper_parameters == fxt_default_model_hyper_parameters

        mock_get_model_storages.assert_called_once_with(task_node_id=detection_task.id_)
        mock_get_hyper_parameters.assert_called_once_with(model_storage=fxt_model_storage_detection)

    def test_get_configuration_for_model_not_found(self, fxt_mongo_id, fxt_project_with_detection_task, fxt_model):
        detection_task = fxt_project_with_detection_task.tasks[-1]

        with (
            pytest.raises(ModelNotFoundException),
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project_with_detection_task),
            patch.object(ModelRepo, "get_by_id", return_value=NullModel()),
            patch.object(ModelStorageRepo, "get_by_task_node_id", return_value=[]),
        ):
            ConfigurationManager().get_configuration_for_model(
                workspace_id=fxt_project_with_detection_task.workspace_id,
                project_id=fxt_project_with_detection_task.id_,
                task_id=detection_task.id_,
                model_id=fxt_mongo_id(),
            )

    def test_get_global_configuration(
        self,
        fxt_mongo_id,
        fxt_project_with_detection_task,
        fxt_configuration_2,
    ):
        global_components = [
            cmp for cmp in ComponentType if not cmp.metadata.per_task and cmp != ComponentType.NULL_COMPONENT
        ]

        with (
            patch.object(
                ConfigurableParametersRepo,
                "get_or_create_component_parameters",
                return_value=fxt_configuration_2,
            ) as mock_get_or_create_parameters,
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project_with_detection_task),
        ):
            global_configuration = ConfigurationManager().get_global_configuration(
                project_id=fxt_project_with_detection_task.id_,
                workspace_id=WORKSPACE_ID,
            )

            last_configuration_type = ConfigurableComponentRegister[
                global_components[-1].name
            ].value.get_configuration_type()
            mock_get_or_create_parameters.assert_called_with(
                data_instance_of=last_configuration_type,
                component=global_components[-1],
                task_id=None,
            )

        assert len(global_configuration) == len(global_components)
        for configuration in global_configuration:
            assert isinstance(configuration, ComponentParameters)
            assert configuration.task_id == ID()

    def test_get_configuration_for_task(
        self,
        fxt_mongo_id,
        fxt_project_with_detection_task,
        fxt_configuration_1,
        fxt_configuration_2,
        fxt_model_storage_detection,
    ):
        per_task_components = [cmp for cmp in ComponentType if cmp.metadata.per_task]
        task = fxt_project_with_detection_task.get_trainable_task_nodes()[-1]

        with (
            patch.object(
                ConfigurationManager,
                "_ConfigurationManager__get_active_model_storage_by_project_and_task_id",
                return_value=fxt_model_storage_detection,
            ),
            patch.object(
                ConfigurableParametersRepo,
                "get_or_create_hyper_parameters",
                return_value=fxt_configuration_1,
            ) as mock_get_hypers,
            patch.object(
                ConfigurableParametersRepo,
                "get_or_create_component_parameters",
                return_value=fxt_configuration_2,
            ) as mock_get_or_create_component_params,
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project_with_detection_task),
        ):
            task_configuration = ConfigurationManager().get_active_configuration_for_task(
                task_id=task.id_,
                project_id=fxt_project_with_detection_task.id_,
                workspace_id=WORKSPACE_ID,
            )

            mock_get_hypers.assert_called_once_with(model_storage=fxt_model_storage_detection)
            last_configuration_register_data = ConfigurableComponentRegister[per_task_components[-1].name].value
            configuration_type = last_configuration_register_data.get_configuration_type(
                task_type=task.task_properties.task_type
            )
            mock_get_or_create_component_params.assert_called_with(
                data_instance_of=configuration_type,
                component=per_task_components[-1],
                task_id=task.id_,
            )
        assert len(task_configuration) == len(per_task_components) + 1

    def test_get_configuration_for_task_chain(
        self,
        fxt_mongo_id,
        fxt_project_with_detection_task,
        fxt_configuration_1,
        fxt_configuration_2,
        fxt_model_storage,
    ):
        per_task_components = [cmp for cmp in ComponentType if cmp.metadata.per_task]

        with (
            patch.object(
                ModelService,
                "get_active_model_storage",
                return_value=fxt_model_storage,
            ),
            patch.object(
                ConfigurableParametersRepo,
                "get_or_create_hyper_parameters",
                return_value=fxt_configuration_1,
            ) as mock_get_hypers,
            patch.object(
                ConfigurableParametersRepo,
                "get_or_create_component_parameters",
                return_value=fxt_configuration_2,
            ) as mock_get_or_create_component_params,
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project_with_detection_task),
        ):
            trainable_task = fxt_project_with_detection_task.get_trainable_task_nodes()[-1]

            task_chain_configuration = ConfigurationManager().get_configuration_for_task_chain(
                workspace_id=WORKSPACE_ID,
                project_id=fxt_project_with_detection_task.id_,
            )

            mock_get_hypers.assert_called_once()
            last_configuration_register_data = ConfigurableComponentRegister[per_task_components[-1].name].value
            configuration_type = last_configuration_register_data.get_configuration_type(
                task_type=trainable_task.task_properties.task_type
            )
            mock_get_or_create_component_params.assert_called_with(
                data_instance_of=configuration_type,
                component=per_task_components[-1],
                task_id=trainable_task.id_,
            )
            assert len(task_chain_configuration) == len(fxt_project_with_detection_task.get_trainable_task_nodes())
            assert task_chain_configuration[0]["task"] == trainable_task
            assert len(task_chain_configuration[0]["configurations"]) == len(per_task_components) + 1
