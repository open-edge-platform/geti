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
import copy
from unittest.mock import patch

import pytest

from communication.exceptions import (
    ConfigurationMismatchException,
    InvalidConfigurationException,
    TaskNotFoundException,
)
from configuration import ConfigurationValidator

from geti_fastapi_tools.exceptions import InvalidEntityIdentifierException
from geti_types import ProjectIdentifier
from iai_core.configuration.elements.component_parameters import ComponentType
from iai_core.configuration.elements.entity_identifiers import ComponentEntityIdentifier, ModelEntityIdentifier


class TestConfigurationValidator:
    def test_validate_entity_identifier(
        self,
        fxt_mongo_id,
        fxt_project_with_detection_task,
        fxt_component_entity_identifier,
    ):
        project = fxt_project_with_detection_task
        task = fxt_project_with_detection_task.tasks[-1]
        entity_identifier = ComponentEntityIdentifier(
            workspace_id=fxt_project_with_detection_task.workspace_id,
            component=ComponentType.DATASET_COUNTER,
            project_id=fxt_project_with_detection_task.id_,
            task_id=task.id_,
        )
        invalid_task_id = fxt_mongo_id(1)

        ConfigurationValidator._validate_entity_identifier(entity_identifier, project=project, task_id=task.id_)
        ConfigurationValidator._validate_entity_identifier(
            entity_identifier,
            project=project,
            task_id=None,
        )
        with pytest.raises(TaskNotFoundException):
            ConfigurationValidator._validate_entity_identifier(
                entity_identifier, project=project, task_id=invalid_task_id
            )
        with pytest.raises(TaskNotFoundException):
            ConfigurationValidator._validate_entity_identifier(
                fxt_component_entity_identifier, project=project, task_id=None
            )

    def test_validate_model_entity_identifier(self, fxt_mongo_id, fxt_model_storage, fxt_project):
        entity_identifier = ModelEntityIdentifier(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
            model_storage_id=fxt_model_storage.id_,
        )
        invalid_entity_identifier = ModelEntityIdentifier(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
            model_storage_id=fxt_mongo_id(20),
        )
        project_id = fxt_mongo_id(3)
        task_id = fxt_mongo_id(4)
        project = fxt_project
        project.id_ = project_id

        # test a valid identifier task-level (i.e. model storage belongs to the task)
        with patch.object(
            ConfigurationValidator,
            "_ConfigurationValidator__get_model_storages_by_task_id",
            return_value=[fxt_model_storage],
        ) as mock_get_model_storages:
            ConfigurationValidator._validate_entity_identifier(
                entity_identifier=entity_identifier,
                project=project,
                task_id=task_id,
            )
        mock_get_model_storages.assert_called_once_with(
            project_identifier=ProjectIdentifier(
                project.workspace_id,
                project.id_,
            ),
            task_id=task_id,
        )

        # test an invalid identifier task-level (i.e. model storage isn't in the task)
        with (
            patch.object(
                ConfigurationValidator,
                "_ConfigurationValidator__get_model_storages_by_task_id",
                return_value=[fxt_model_storage],
            ),
            pytest.raises(InvalidEntityIdentifierException),
        ):
            ConfigurationValidator._validate_entity_identifier(
                entity_identifier=invalid_entity_identifier,
                project=project,
                task_id=task_id,
            )

        # test a valid identifier project-level (i.e. model storage belongs to project)
        with patch.object(
            ConfigurationValidator,
            "_ConfigurationValidator__get_model_storages_by_task_id",
            return_value=[fxt_model_storage],
        ) as mock_get_model_storages:
            ConfigurationValidator._validate_entity_identifier(
                entity_identifier=entity_identifier,
                project=project,
            )
        mock_get_model_storages.assert_called_once_with(
            project_identifier=ProjectIdentifier(
                project.workspace_id,
                project.id_,
            ),
            task_id=project.get_trainable_task_nodes()[0].id_,
        )

        # test an invalid identifier project-level (i.e. model storage isn't in project)
        with (
            patch.object(
                ConfigurationValidator,
                "_ConfigurationValidator__get_model_storages_by_task_id",
                return_value=[fxt_model_storage],
            ),
            pytest.raises(InvalidEntityIdentifierException),
        ):
            ConfigurationValidator._validate_entity_identifier(
                entity_identifier=invalid_entity_identifier,
                project=project,
            )

    def test_validate_input_config_data(
        self,
        fxt_default_model_hyper_parameters,
        fxt_default_model_hyper_parameters_data,
        fxt_model_entity_identifier,
    ):
        valid_params = fxt_default_model_hyper_parameters_data
        valid_params["learning_parameters"]["batch_size"]["value"] += 5
        invalid_params_neg_bs = copy.deepcopy(valid_params)
        invalid_params_neg_bs["learning_parameters"]["batch_size"]["value"] = -10
        invalid_params_unknown_param = copy.deepcopy(valid_params)
        invalid_params_unknown_param["learning_parameters"]["foo"] = {"value": "bar"}
        invalid_params_unknown_group = copy.deepcopy(valid_params)
        invalid_params_unknown_group["foo_parameters"] = {
            "foo": {"value": "bar"},
            "dummy": {"value": "dummy"},
        }
        with patch.object(
            ConfigurationValidator,
            "_get_latest_config_by_entity_identifier",
            return_value=fxt_default_model_hyper_parameters,
        ):
            ConfigurationValidator._validate_and_update_config_values(
                input_config=valid_params, entity_identifier=fxt_model_entity_identifier
            )

        with (
            patch.object(
                ConfigurationValidator,
                "_get_latest_config_by_entity_identifier",
                return_value=fxt_default_model_hyper_parameters,
            ),
            pytest.raises(ConfigurationMismatchException),
        ):
            ConfigurationValidator._validate_and_update_config_values(
                input_config=invalid_params_unknown_param,
                entity_identifier=fxt_model_entity_identifier,
            )

        with (
            patch.object(
                ConfigurationValidator,
                "_get_latest_config_by_entity_identifier",
                return_value=fxt_default_model_hyper_parameters,
            ),
            pytest.raises(ConfigurationMismatchException),
        ):
            ConfigurationValidator()._validate_and_update_config_values(
                input_config=invalid_params_unknown_group,
                entity_identifier=fxt_model_entity_identifier,
            )

        with (
            patch.object(
                ConfigurationValidator,
                "_get_latest_config_by_entity_identifier",
                return_value=fxt_default_model_hyper_parameters,
            ),
            pytest.raises(InvalidConfigurationException),
        ):
            ConfigurationValidator._validate_and_update_config_values(
                input_config=invalid_params_neg_bs,
                entity_identifier=fxt_model_entity_identifier,
            )
