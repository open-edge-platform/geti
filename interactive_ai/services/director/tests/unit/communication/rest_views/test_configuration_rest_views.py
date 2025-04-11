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
import copy

from communication.views.configuration_rest_views import ConfigurationRESTViews

from sc_sdk.configuration.elements.component_parameters import ComponentType
from sc_sdk.configuration.elements.entity_identifiers import ComponentEntityIdentifier


class TestSCConfigurationRESTViews:
    def test_config_to_rest(self, fxt_configuration, fxt_configuration_rest):
        result = ConfigurationRESTViews._config_to_rest(config=fxt_configuration)

        assert result == fxt_configuration_rest

    def test_config_from_rest(
        self,
        fxt_configuration_rest,
        fxt_configuration_rest_restructured,
        fxt_model_entity_identifier,
        fxt_mongo_id,
        fxt_project,
    ):
        (
            restructured_dict,
            entity_identifier,
        ) = ConfigurationRESTViews._config_dict_from_rest(
            rest_input=fxt_configuration_rest,
            workspace_id=fxt_model_entity_identifier.workspace_id,
            project_id=fxt_project.id_,
            task_id=fxt_mongo_id(),
        )

        assert restructured_dict == fxt_configuration_rest_restructured

        assert entity_identifier == fxt_model_entity_identifier

    def test_config_list_to_rest(
        self,
        fxt_configuration_1,
        fxt_configuration_rest_1,
        fxt_configuration_2,
        fxt_configuration_rest_2,
    ):
        # arrange
        config_list = [fxt_configuration_1, fxt_configuration_2]

        # act
        result = ConfigurationRESTViews._config_list_to_rest(configs=config_list)

        # assert
        assert result == [fxt_configuration_rest_1, fxt_configuration_rest_2]

    def test_config_list_from_rest_dict(
        self,
        fxt_configuration_rest_1,
        fxt_configuration_rest_restructured_1,
        fxt_configuration_rest_2,
        fxt_configuration_rest_restructured_2,
        fxt_model_entity_identifier,
        fxt_component_entity_identifier,
    ):
        configs = {"components": [fxt_configuration_rest_1, fxt_configuration_rest_2]}

        result = ConfigurationRESTViews.config_list_from_rest_dict(
            rest_input=configs,
            workspace_id=fxt_component_entity_identifier.workspace_id,
            project_id=fxt_component_entity_identifier.project_id,
            task_id=fxt_component_entity_identifier.task_id,
        )

        assert result == [
            (fxt_configuration_rest_restructured_1, fxt_model_entity_identifier),
            (fxt_configuration_rest_restructured_2, fxt_component_entity_identifier),
        ]

    def test_task_config_list_to_rest(
        self,
        fxt_configuration_1,
        fxt_configuration_rest_1,
        fxt_configuration_2,
        fxt_configuration_rest_2,
        fxt_task,
    ):
        config_list = [fxt_configuration_1, fxt_configuration_2]

        result = ConfigurationRESTViews.task_config_list_to_rest(task=fxt_task, configs=config_list)

        assert result == {
            "components": [fxt_configuration_rest_1, fxt_configuration_rest_2],
            "task_id": fxt_task.id_,
            "task_title": fxt_task.title,
        }

    def test_hyper_parameters_to_rest(
        self,
        fxt_hyper_parameters_with_groups,
        fxt_default_learning_parameters_rest_response,
        fxt_dummy_parameter_group_rest_response,
    ):
        result_list = ConfigurationRESTViews._hyper_parameters_to_rest(fxt_hyper_parameters_with_groups)

        assert fxt_hyper_parameters_with_groups.data is not None
        hyper_params = fxt_hyper_parameters_with_groups.data
        assert len(result_list) == len(hyper_params.groups)

        learning_parameters = next(
            cfg_dict for cfg_dict in result_list if cfg_dict["header"] == hyper_params.learning_parameters.header
        )
        lp_entity_identifier = learning_parameters.pop("entity_identifier")
        assert lp_entity_identifier["type"] == "HYPER_PARAMETER_GROUP"
        assert lp_entity_identifier["model_storage_id"] == str(fxt_hyper_parameters_with_groups.model_storage_id)
        assert learning_parameters == fxt_default_learning_parameters_rest_response

        dummy_parameter_group = next(
            cfg_dict for cfg_dict in result_list if cfg_dict["header"] == hyper_params.dummy_group.header
        )
        dpg_entity_identifier = dummy_parameter_group.pop("entity_identifier")
        assert dpg_entity_identifier["type"] == "HYPER_PARAMETER_GROUP"
        assert dpg_entity_identifier["model_storage_id"] == str(fxt_hyper_parameters_with_groups.model_storage_id)
        assert dpg_entity_identifier["workspace_id"] == str(fxt_hyper_parameters_with_groups.workspace_id)
        assert dummy_parameter_group == fxt_dummy_parameter_group_rest_response

    def test_task_config_list_to_rest_grouped_hyper_parameters(
        self,
        fxt_hyper_parameters_with_groups,
        fxt_configuration_2,
        fxt_configuration_rest_2,
        fxt_default_learning_parameters_rest_response,
        fxt_dummy_parameter_group_rest_response,
        fxt_hyper_parameter_group_entity_identifier_rest,
        fxt_task,
    ):
        # Arrange
        config_list = [fxt_hyper_parameters_with_groups, fxt_configuration_2]
        learning_parameters_rest = fxt_default_learning_parameters_rest_response
        learning_parameters_rest["entity_identifier"] = copy.deepcopy(
            fxt_hyper_parameter_group_entity_identifier_rest(group_name="learning_parameters")
        )
        dummy_group_rest = fxt_dummy_parameter_group_rest_response
        dummy_group_rest["entity_identifier"] = copy.deepcopy(
            fxt_hyper_parameter_group_entity_identifier_rest(group_name="dummy_group")
        )

        # Act
        result = ConfigurationRESTViews.task_config_list_to_rest(task=fxt_task, configs=config_list)

        # Assert
        assert result == {
            "components": [
                dummy_group_rest,
                learning_parameters_rest,
                fxt_configuration_rest_2,
            ],
            "task_id": fxt_task.id_,
            "task_title": fxt_task.title,
        }

    def test_config_list_from_rest_dict_hyper_parameter_groups(
        self,
        fxt_default_learning_parameters_rest_request,
        fxt_dummy_parameter_group_rest_request,
        fxt_model_storage,
        fxt_configuration_rest_2,
        fxt_hyper_parameters_with_groups,
        fxt_configuration_rest_restructured_2,
        fxt_hyper_parameters_with_groups_rest_request_restructured,
        fxt_task,
        fxt_project,
    ):
        configs = {
            "components": [
                fxt_default_learning_parameters_rest_request,
                fxt_dummy_parameter_group_rest_request,
                fxt_configuration_rest_2,
            ]
        }
        component_entity_identifier = ComponentEntityIdentifier(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
            component=ComponentType.DATASET_COUNTER,
            task_id=fxt_task.id_,
        )

        result = ConfigurationRESTViews.config_list_from_rest_dict(
            rest_input=configs,
            workspace_id=fxt_project.workspace_id,
            project_id=component_entity_identifier.project_id,
            task_id=component_entity_identifier.task_id,
        )

        assert result == [
            (fxt_configuration_rest_restructured_2, component_entity_identifier),
            (
                fxt_hyper_parameters_with_groups_rest_request_restructured,
                fxt_hyper_parameters_with_groups.entity_identifier,
            ),
        ]
