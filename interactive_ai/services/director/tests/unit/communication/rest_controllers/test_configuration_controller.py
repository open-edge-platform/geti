# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import call, patch

import pytest
from testfixtures import compare

from communication.controllers.configuration_controller import ConfigurationRESTController
from communication.data_validator import ConfigurationRestValidator
from communication.views.configuration_rest_views import ConfigurationRESTViews
from configuration import ConfigurationValidator
from configuration.configuration_manager import ConfigurationManager

from geti_fastapi_tools.exceptions import BadRequestException
from geti_fastapi_tools.responses import success_response_rest
from geti_types import ID
from iai_core_py.configuration.elements.configurable_parameters import ConfigurableParameters
from iai_core_py.configuration.elements.hyper_parameters import HyperParameters
from iai_core_py.entities.project import Project
from iai_core_py.repos import ConfigurableParametersRepo, ProjectRepo


@pytest.fixture
def configuration_controller():
    return ConfigurationRESTController()


class TestConfigurationRESTController:
    def test_get_full_configuration(self, configuration_controller, fxt_task_chain_project):
        project_id = ID("dummy_project_id")
        workspace_id = ID("dummy_workspace_id")

        with (
            patch.object(
                ProjectRepo,
                "get_by_id",
                return_value=fxt_task_chain_project,
            ),
            patch.object(
                ConfigurationManager,
                "get_full_configuration",
                return_value=[{"dummy": "configuration"}, {"dummy": "configuration"}],
            ) as get_full_configuration_mocked,
            patch.object(
                ConfigurationRESTViews,
                "full_config_to_rest_dict",
                return_value={"dummy": "dict"},
            ) as full_config_to_rest_dict_mocked,
        ):
            result = configuration_controller.get_full_configuration(
                project_id=project_id,
                workspace_id=workspace_id,
            )

        get_full_configuration_mocked.assert_called_with(project_id=project_id, workspace_id=workspace_id)
        full_config_to_rest_dict_mocked.assert_called_with(
            global_config={"dummy": "configuration"},
            task_chain_config={"dummy": "configuration"},
        )

        assert result == {"dummy": "dict"}

    def test_get_global_configuration(
        self,
        configuration_controller,
        fxt_task_chain_project,
    ):
        project_id = ID("dummy_project_id")
        workspace_id = ID("dummy_workspace_id")
        global_config_with_task_id = {
            "description": "hello",
            "entity_identifier": {
                "component": "dummy",
                "project_id": "1234",
                "task_id": "",
                "type": "dummy",
                "workspace_id": "5678",
            },
        }
        with (
            patch.object(
                ProjectRepo,
                "get_by_id",
                return_value=fxt_task_chain_project,
            ),
            patch.object(
                ConfigurationManager,
                "get_global_configuration",
                return_value={"dummy": "configuration"},
            ) as get_global_configuration_mocked,
            patch.object(
                ConfigurationRESTViews,
                "_config_list_to_rest",
                return_value=[global_config_with_task_id],
            ) as config_list_to_rest_mocked,
        ):
            result = configuration_controller.get_global_configuration(
                project_id=project_id,
                workspace_id=workspace_id,
            )

        get_global_configuration_mocked.assert_called_with(project_id=project_id, workspace_id=workspace_id)
        config_list_to_rest_mocked.assert_called_with({"dummy": "configuration"})
        global_config_without_task_id = {
            "description": "hello",
            "entity_identifier": {
                "component": "dummy",
                "project_id": "1234",
                "type": "dummy",
                "workspace_id": "5678",
            },
        }
        assert result == {"global": [global_config_without_task_id]}

    def test_get_task_chain_configuration(
        self,
        configuration_controller,
        fxt_task_chain_project,
    ):
        project_id = ID("dummy_project_id")
        workspace_id = ID("dummy_workspace_id")

        with (
            patch.object(
                ProjectRepo,
                "get_by_id",
                return_value=fxt_task_chain_project,
            ),
            patch.object(
                ConfigurationManager,
                "get_configuration_for_task_chain",
                return_value={"dummy": "configuration"},
            ) as get_configuration_for_task_chain_mocked,
            patch.object(
                ConfigurationRESTViews,
                "task_chain_config_to_rest_dict",
                return_value={"dummy": "dict"},
            ) as task_chain_config_to_rest_dict_mocked,
        ):
            result = configuration_controller.get_task_chain_configuration(
                project_id=project_id,
                workspace_id=workspace_id,
            )

        get_configuration_for_task_chain_mocked.assert_called_with(project_id=project_id, workspace_id=workspace_id)
        task_chain_config_to_rest_dict_mocked.assert_called_with({"dummy": "configuration"})

        assert result == {"dummy": "dict"}

    def test_get_task_or_model_configuration_successful(self, configuration_controller, fxt_task_chain_project):
        task_id = fxt_task_chain_project.task_ids[0]
        project_id = fxt_task_chain_project.id_
        workspace_id = fxt_task_chain_project.workspace_id

        with (
            patch.object(
                ConfigurationManager,
                "get_active_configuration_for_task",
                return_value="dummy_return_value",
            ) as get_configuration_for_task_mocked,
            patch.object(
                ConfigurationRESTViews,
                "task_config_list_to_rest",
                return_value={"dummy": "dict"},
            ) as task_config_list_to_rest_mocked,
        ):
            result = configuration_controller.get_task_or_model_configuration(
                task_id=task_id,
                project_id=project_id,
                workspace_id=workspace_id,
            )
        get_configuration_for_task_mocked.assert_called_with(
            task_id=task_id, project_id=project_id, workspace_id=workspace_id
        )
        task_config_list_to_rest_mocked.assert_called_with(
            task=fxt_task_chain_project.task_graph.tasks[0],
            configs="dummy_return_value",
        )

        assert result == {"dummy": "dict"}

    def test_get_task_or_model_configuration_successful_additional_model(
        self, configuration_controller, fxt_task_chain_project
    ):
        task_id = fxt_task_chain_project.task_ids[0]
        project_id = fxt_task_chain_project.id_
        workspace_id = fxt_task_chain_project.workspace_id
        model_id = ID("dummy_model_id")
        dummy_config_data = ConfigurableParameters(header="Dummy")
        dummy_model_storage_id = ID("dummy_model_storage_id")
        dummy_config_id = ID("dummy_config_param_id")
        dummy_hyper_parameters = HyperParameters(
            workspace_id=workspace_id,
            project_id=project_id,
            model_storage_id=dummy_model_storage_id,
            id_=dummy_config_id,
            data=dummy_config_data,
        )

        with (
            patch.object(
                ConfigurationManager,
                "get_configuration_for_model",
                return_value=[dummy_config_data, dummy_model_storage_id],
            ) as get_configuration_for_model_mocked,
            patch.object(
                ConfigurationRESTViews,
                "task_config_list_to_rest",
                return_value={"dummy": "dict"},
            ) as model_config_to_rest_list_mocked,
            patch.object(
                ConfigurableParametersRepo,
                "generate_id",
                return_value=dummy_config_id,
            ),
        ):
            result = configuration_controller.get_task_or_model_configuration(
                task_id=task_id,
                project_id=project_id,
                workspace_id=workspace_id,
                model_id=model_id,
            )
        get_configuration_for_model_mocked.assert_called_with(
            model_id=model_id,
            task_id=task_id,
            project_id=project_id,
            workspace_id=workspace_id,
        )
        model_config_to_rest_list_mocked.assert_called_with(
            task=fxt_task_chain_project.task_graph.tasks[0],
            configs=[dummy_hyper_parameters],
        )

        assert result == {"dummy": "dict"}

    def test_get_task_or_model_configuration_successful_additional_algorithm(
        self, configuration_controller, fxt_task_chain_project
    ):
        task_id = fxt_task_chain_project.task_ids[0]
        project_id = fxt_task_chain_project.id_
        workspace_id = fxt_task_chain_project.workspace_id
        algorithm = "detection"

        with (
            patch.object(
                ConfigurationManager,
                "get_configuration_for_algorithm",
                return_value={"dummy": "config"},
            ) as get_configuration_for_algorithm_mocked,
            patch.object(
                ConfigurationRESTViews,
                "task_config_list_to_rest",
                return_value={"dummy": "dict"},
            ) as task_config_list_to_rest_mocked,
        ):
            result = configuration_controller.get_task_or_model_configuration(
                task_id=task_id,
                project_id=project_id,
                workspace_id=workspace_id,
                algorithm_name=algorithm,
            )
        get_configuration_for_algorithm_mocked.assert_called_with(
            algorithm_name=algorithm,
            task_id=task_id,
            project_id=project_id,
            workspace_id=workspace_id,
        )
        task_config_list_to_rest_mocked.assert_called_with(
            task=fxt_task_chain_project.task_graph.tasks[0],
            configs=[{"dummy": "config"}],
        )

        assert result == {"dummy": "dict"}

    def test_get_task_or_model_configuration_invalid_argument_combo(
        self, configuration_controller, fxt_task_chain_project
    ):
        task_id = fxt_task_chain_project.task_ids[0]
        project_id = fxt_task_chain_project.id_
        workspace_id = fxt_task_chain_project.workspace_id

        with pytest.raises(BadRequestException) as error:
            configuration_controller.get_task_or_model_configuration(
                task_id=task_id,
                project_id=project_id,
                workspace_id=workspace_id,
                algorithm_name="detection",
                model_id=ID("dummy_model_id"),
            )

        assert str(error.value) == "Cannot use both model_id and algorithm name as query parameters"

    def test_set_taskchain_configuration_successful(
        self,
        configuration_controller,
        fxt_task_chain_project,
        fxt_configuration_dict,
        fxt_configuration_2,
    ):
        project_id = fxt_task_chain_project.id_
        workspace_id = fxt_task_chain_project.workspace_id
        dummy_return = [[["a", "b"], ["c", "d"]], [["e", "f"], ["g", "h"]]]
        dummy_append = fxt_configuration_2

        with (
            patch.object(
                ProjectRepo,
                "get_by_id",
                return_value=fxt_task_chain_project,
            ) as get_project_by_id_mocked,
            patch.object(
                ConfigurationRESTViews,
                "_task_chain_config_from_rest_list",
                return_value=dummy_return,
            ) as task_chain_config_from_rest_list_mocked,
            patch.object(
                ConfigurationValidator, "_validate_entity_identifier", return_value=True
            ) as validate_entity_identifier_mocked,
            patch.object(
                ConfigurationValidator,
                "_validate_and_update_config_values",
                return_value=dummy_append,
            ) as validate_and_update_config_mocked,
            patch.object(
                ConfigurationManager, "save_configuration_list", return_value=True
            ) as save_configuration_mocked,
        ):
            result = configuration_controller.set_task_chain_configuration(
                project_id=project_id,
                workspace_id=workspace_id,
                set_request=fxt_configuration_dict,
            )

        get_project_by_id_mocked.assert_called_with(project_id)
        task_chain_config_from_rest_list_mocked.assert_called_with(
            fxt_configuration_dict["task_chain"],
            workspace_id=workspace_id,
            project_id=project_id,
        )
        validate_entity_identifier_mocked.assert_has_calls(
            [
                call(
                    entity_identifier="b",
                    project=fxt_task_chain_project,
                    task_id=fxt_task_chain_project.get_trainable_task_nodes()[0].id_,
                ),
                call(
                    entity_identifier="d",
                    project=fxt_task_chain_project,
                    task_id=fxt_task_chain_project.get_trainable_task_nodes()[0].id_,
                ),
                call(
                    entity_identifier="f",
                    project=fxt_task_chain_project,
                    task_id=fxt_task_chain_project.get_trainable_task_nodes()[1].id_,
                ),
                call(
                    entity_identifier="h",
                    project=fxt_task_chain_project,
                    task_id=fxt_task_chain_project.get_trainable_task_nodes()[1].id_,
                ),
            ]
        )
        validate_and_update_config_mocked.assert_has_calls(
            [
                call(input_config="a", entity_identifier="b"),
                call(input_config="c", entity_identifier="d"),
            ]
        )
        save_configuration_mocked.assert_has_calls(
            [
                call(
                    workspace_id=workspace_id,
                    project_id=project_id,
                    configurable_parameter_list=[
                        dummy_append,
                        dummy_append,
                        dummy_append,
                        dummy_append,
                    ],
                )
            ]
        )

        compare(result, success_response_rest(), ignore_eq=True)

    def test_set_global_configuration_successful(
        self,
        configuration_controller,
        fxt_task_chain_project,
        fxt_configuration_dict,
        fxt_configuration_2,
    ):
        project_id = ID("dummy_project_id")
        workspace_id = ID("dummy_workspace_id")
        dummy_return = [["a", "b"], ["c", "d"]]
        dummy_append = fxt_configuration_2

        with (
            patch.object(
                ProjectRepo,
                "get_by_id",
                return_value=fxt_task_chain_project,
            ) as get_project_by_id_mocked,
            patch.object(
                ConfigurationRESTViews,
                "config_list_from_rest_dict",
                return_value=dummy_return,
            ) as config_list_from_rest_dict_mocked,
            patch.object(
                ConfigurationValidator,
                "_validate_and_update_config_values",
                return_value=dummy_append,
            ) as validate_and_update_config_mocked,
            patch.object(
                ConfigurationManager, "save_configuration_list", return_value=True
            ) as save_configuration_list_mocked,
        ):
            result = configuration_controller.set_global_configuration(
                project_id=project_id,
                workspace_id=workspace_id,
                set_request=fxt_configuration_dict,
            )

        get_project_by_id_mocked.assert_called_with(project_id)
        config_list_from_rest_dict_mocked.assert_called_with(
            {"components": fxt_configuration_dict["global"]},
            workspace_id=workspace_id,
            project_id=project_id,
        )
        validate_and_update_config_mocked.assert_has_calls(
            [
                call(input_config="a", entity_identifier="b"),
                call(input_config="c", entity_identifier="d"),
            ]
        )
        save_configuration_list_mocked.assert_has_calls(
            [
                call(
                    workspace_id=workspace_id,
                    project_id=project_id,
                    configurable_parameter_list=[dummy_append, dummy_append],
                )
            ]
        )

        compare(result, success_response_rest(), ignore_eq=True)

    def test_set_task_configuration_successful(
        self,
        configuration_controller,
        fxt_task_chain_project,
        fxt_configuration_dict,
        fxt_configuration_2,
    ):
        project_id = fxt_task_chain_project.id_
        workspace_id = fxt_task_chain_project.workspace_id
        task_id = fxt_task_chain_project.task_ids[0]
        dummy_return = [["a", "b"], ["c", "d"]]
        dummy_append = fxt_configuration_2

        with (
            patch.object(
                ProjectRepo,
                "get_by_id",
                return_value=fxt_task_chain_project,
            ) as get_project_by_id_mocked,
            patch.object(
                Project,
                "get_trainable_task_node_by_id",
                return_value=fxt_task_chain_project.task_graph.tasks[0],
            ) as get_task_by_id_mocked,
            patch.object(
                ConfigurationRestValidator,
                "validate_task_configuration",
                return_value=True,
            ) as validate_task_configuration_mocked,
            patch.object(
                ConfigurationRESTViews,
                "config_list_from_rest_dict",
                return_value=dummy_return,
            ) as config_list_from_rest_dict_mocked,
            patch.object(
                ConfigurationValidator, "_validate_entity_identifier", return_value=True
            ) as validate_entity_identifier_mocked,
            patch.object(
                ConfigurationValidator,
                "_validate_and_update_config_values",
                return_value=dummy_append,
            ) as validate_and_update_config_mocked,
            patch.object(
                ConfigurationManager, "save_configuration_list", return_value=True
            ) as save_configuration_list_mocked,
        ):
            result = configuration_controller.set_task_configuration(
                task_id=task_id,
                project_id=project_id,
                workspace_id=workspace_id,
                set_request=fxt_configuration_dict,
            )

        get_project_by_id_mocked.assert_called_with(project_id)
        get_task_by_id_mocked.assert_called_with(task_id=task_id)
        validate_task_configuration_mocked.assert_called_with(fxt_configuration_dict)
        config_list_from_rest_dict_mocked.assert_called_with(
            fxt_configuration_dict,
            workspace_id=workspace_id,
            project_id=project_id,
            task_id=task_id,
        )
        validate_entity_identifier_mocked.assert_has_calls(
            [
                call(
                    entity_identifier="b",
                    project=fxt_task_chain_project,
                    task_id=task_id,
                ),
                call(
                    entity_identifier="d",
                    project=fxt_task_chain_project,
                    task_id=task_id,
                ),
            ]
        )
        validate_and_update_config_mocked.assert_has_calls(
            [
                call(input_config="a", entity_identifier="b"),
                call(input_config="c", entity_identifier="d"),
            ]
        )
        save_configuration_list_mocked.assert_has_calls(
            [
                call(
                    workspace_id=workspace_id,
                    project_id=project_id,
                    configurable_parameter_list=[dummy_append, dummy_append],
                )
            ]
        )

        compare(result, success_response_rest(), ignore_eq=True)

    def test_set_full_configuration_successful(
        self,
        configuration_controller,
        fxt_task_chain_project,
        fxt_configuration_dict,
    ):
        project_id = ID("dummy_project_id")
        workspace_id = ID("dummy_workspace_id")

        with (
            patch.object(
                ProjectRepo,
                "get_by_id",
                return_value=fxt_task_chain_project,
            ) as get_project_by_id_mocked,
            patch.object(
                ConfigurationRestValidator,
                "validate_full_configuration",
                return_value=True,
            ) as validate_full_configuration_mocked,
            patch.object(
                ConfigurationRESTController,
                "set_global_configuration",
                return_value=success_response_rest(),
            ) as set_global_configuration_mocked,
            patch.object(
                ConfigurationRESTController,
                "set_task_chain_configuration",
                return_value=success_response_rest(),
            ) as set_task_chain_configuration_mocked,
        ):
            result = configuration_controller.set_full_configuration(
                project_id=project_id,
                workspace_id=workspace_id,
                set_request=fxt_configuration_dict,
            )

        get_project_by_id_mocked.assert_called_with(project_id)
        validate_full_configuration_mocked.assert_called_with(fxt_configuration_dict)
        set_global_configuration_mocked.assert_called_with(
            project_id=project_id,
            workspace_id=workspace_id,
            set_request=fxt_configuration_dict,
        )
        set_task_chain_configuration_mocked.assert_called_with(
            project_id=project_id,
            workspace_id=workspace_id,
            set_request=fxt_configuration_dict,
        )

        compare(result, success_response_rest(), ignore_eq=True)

    def test_rescale_subset_values(self, fxt_subset_manager_config):
        subset_parameters = fxt_subset_manager_config.data.subset_parameters
        subset_parameters.train_proportion = 1.0

        ConfigurationRESTController._rescale_subset_manager_config(subset_manager_config=fxt_subset_manager_config)

        assert (
            subset_parameters.train_proportion
            + subset_parameters.test_proportion
            + subset_parameters.validation_proportion
            == 1.0
        )

    def test_rescale_subset_values_float_sum(self, fxt_subset_manager_config):
        subset_parameters = fxt_subset_manager_config.data.subset_parameters
        subset_parameters.train_proportion = 0.8
        subset_parameters.test_proportion = 0.1
        subset_parameters.validation_proportion = 0.1

        ConfigurationRESTController._rescale_subset_manager_config(subset_manager_config=fxt_subset_manager_config)

        assert (
            subset_parameters.train_proportion
            + subset_parameters.test_proportion
            + subset_parameters.validation_proportion
            == 1.0
        )
