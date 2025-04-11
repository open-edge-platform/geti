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
from pathlib import Path

import pytest
from _pytest.fixtures import FixtureRequest

import sc_sdk.configuration.helper as otx_config_helper
from sc_sdk.configuration.elements.component_parameters import ComponentParameters, ComponentType
from sc_sdk.configuration.elements.configurable_parameters import ConfigurableParameters
from sc_sdk.configuration.elements.default_model_parameters import DefaultModelParameters
from sc_sdk.configuration.elements.hyper_parameters import HyperParameters
from sc_sdk.configuration.interfaces.configurable_parameters_interface import IConfigurableParameterContainer
from sc_sdk.entities.project import Project
from sc_sdk.repos import ConfigurableParametersRepo
from sc_sdk.services.model_service import ModelService
from tests.configuration.dummy_config import DatasetManagerConfig
from tests.test_helpers import generate_random_annotated_project, register_model_template


@pytest.mark.ScSdkComponent
class TestConfigurationRepos:
    @staticmethod
    def __get_path_to_file(filename: str):
        """
        Return the path to the file named 'filename', which lives in the tests/configuration directory
        """
        return str(Path(__file__).parent / Path(filename))

    def __repo_saving_and_tests(
        self,
        project: Project,
        configurable_parameters: IConfigurableParameterContainer[ConfigurableParameters],
        request: FixtureRequest,
    ) -> ConfigurableParametersRepo:
        """
        Basic test routine for ConfigurableParametersRepo
        """
        repository = ConfigurableParametersRepo(project.identifier)

        # create serialized config for comparison later on
        assert configurable_parameters.data is not None
        config_serialized = otx_config_helper.convert(configurable_parameters.data, dict)

        # Persist and fetch config from repository
        repository.save(configurable_parameters)

        request.addfinalizer(lambda: repository.delete_by_id(configurable_parameters.id_))
        config_fetched = repository.get_by_id(configurable_parameters.id_)
        assert config_fetched.data is not None
        config_fetched_serialized = otx_config_helper.convert(config_fetched.data, dict)

        # Remove id's to make a comparison
        config_serialized.pop("id")
        config_fetched_serialized.pop("id")

        # Check that the config data before and after saving are equal
        assert config_serialized == config_fetched_serialized

        # Assert that substituting the fetched config id into the initial config works
        assert configurable_parameters.id_ == config_fetched.id_
        return repository

    def test_config_repo(self, request) -> None:
        """
        <b>Description:</b>
        This test verifies that a Configuration can be saved to and loaded from the
        ConfigurableParametersRepo, and
        that the config is assigned an ID upon saving. It also asserts that saving
        another config to the repo using the
        same identifiers results in a later config.id_

        <b>Input data:</b>
        Dummy configuration -- DatasetManagerConfig

        <b>Expected results:</b>
        Test passes if the config is assigned an ID upon saving, and if the config
        fetched from the repository has the
        same ID as was assigned upon saving. Also, saving an second config to the
        repository should result in the
        `get_or_create` method returning config 2 instead of config 1

        <b>Steps</b>
        1. Create project
        2. Create 2 distinct DatasetManagerConfig configurations
        3. Save config 1 to repository
        4. Fetch latest config from repository, check that ID's match
        5. Save config 2 to repository
        6. Fetch latest config from repository, check that ID matches config 2's ID
        7. Check that latest config parameter values match config 2 parameter values
        """
        # Create project and initialize two different configs
        register_model_template(request, type(None), "detection", "DETECTION", trainable=True)
        project = generate_random_annotated_project(
            request,
            "__Test component config",
            "",
            "detection",
            number_of_images=0,
        )[0]

        config_data = DatasetManagerConfig(  # type:ignore
            description="TEST ONLY",
            header="TEST ONLY",
        )
        config_data_2 = DatasetManagerConfig(  # type:ignore
            description="TEST ONLY",
            header="TEST ONLY",
        )
        config_data_2.label_constraints = False

        repo: ConfigurableParametersRepo = ConfigurableParametersRepo(project.identifier)
        conf_params: ComponentParameters = ComponentParameters(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            component=ComponentType.DATASET_COUNTER,
            id_=repo.generate_id(),
            data=config_data,
        )
        conf_params_2 = copy.deepcopy(conf_params)
        conf_params_2.data = config_data_2
        conf_params_2.id_ = repo.generate_id()

        # Save config, test that fetching the latest config from the repo works
        repo.save(conf_params)
        cfg_id = conf_params.id_
        latest_config = repo.get_or_create_component_parameters(
            data_instance_of=DatasetManagerConfig,
            component=ComponentType.DATASET_COUNTER,
            task_id=None,
        )
        assert cfg_id == latest_config.id_

        # Save config_2, test that fetching the latest config now yields config_2
        assert cfg_id != conf_params_2.id_
        repo.save(conf_params_2)
        latest_config = repo.get_or_create_component_parameters(
            data_instance_of=DatasetManagerConfig,
            component=ComponentType.DATASET_COUNTER,
            task_id=None,
        )
        assert cfg_id != latest_config.id_
        assert conf_params_2.id_ == latest_config.id_
        assert latest_config.data is not None
        assert latest_config.data.label_constraints is False

    def test_component_config_repo(self, request) -> None:
        """
        <b>Description:</b>
        This test verifies that a ComponentConfiguration can be saved to and loaded
        from the ConfigurableParametersRepo, and
        that the config is assigned an ID upon saving

        <b>Input data:</b>
        Dummy configuration -- DatasetManagerConfig

        <b>Expected results:</b>
        Test passes if the config is assigned an ID upon saving, and if the config
        fetched from the repository is equal
        to the one saved to the repository, apart from its ID

        <b>Steps</b>
        1. Create project
        2. Create DatasetManagerConfig configuration
        3. Save config to repository
        4. Fetch config from repository
        5. Verify that contents of fetched config and original config are equal
        """
        # Create project and initialize config
        register_model_template(request, type(None), "detection", "DETECTION", trainable=True)
        project = generate_random_annotated_project(
            request,
            "__Test component config",
            "",
            "detection",
            number_of_images=0,
        )[0]
        config = DatasetManagerConfig(  # type:ignore
            description="TEST ONLY",
            header="TEST ONLY",
        )

        conf_params: ComponentParameters = ComponentParameters(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            component=ComponentType.DATASET_COUNTER,
            id_=ConfigurableParametersRepo.generate_id(),
            data=config,
        )

        # Test saving to and fetching from the repository
        self.__repo_saving_and_tests(project=project, configurable_parameters=conf_params, request=request)

    def test_task_specific_component_config_repo(self, request) -> None:
        """
        <b>Description:</b>
        This test verifies that a ComponentParameters object can be saved to and loaded
        from the ConfigurableParametersRepo, using
        a task ID to make the config task specific. It also tests that saving and
        loading works for all tasks in the
        project independently.

        <b>Input data:</b>
        Dummy configuration -- DatasetManagerConfig

        <b>Expected results:</b>
        Test passes if the configurations can be saved and fetched for each task in the
        project independently, and if a
        list of configurations for all tasks in the project can be fetched.

        <b>Steps</b>
        1. Create project
        2. Create DatasetManagerConfig configuration
        3. Set task_id of the config and save config to repository
        4. Fetch config from repository
        5. Verify that contents of fetched config and original config are equal
        6. Copy config and set task_id to the next task in the project
        7. Save and fetch config, verify that contents of fetched config and original
            config are equal
        8. Fetch list of configurations for all tasks in the project
        9. Assert that list has length 2, and that contents of fetched configs match
            the original configs.
        """
        # Create project and initialize repo and config
        register_model_template(
            request,
            task=type(None),
            model_template_id="detection",
            task_type="DETECTION",
            trainable=True,
        )
        project = generate_random_annotated_project(
            request,
            name="__Test component config",
            description="",
            model_template_id="detection",
            number_of_images=0,
        )[0]
        repository = ConfigurableParametersRepo(project.identifier)
        config = DatasetManagerConfig(  # type:ignore
            description="TEST ONLY",
            header="TEST ONLY",
        )

        # Set task id for the component config, so that it only affects the last task
        # in the project
        conf_params: ComponentParameters[ConfigurableParameters] = ComponentParameters(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            component=ComponentType.DATASET_COUNTER,
            id_=ConfigurableParametersRepo.generate_id(),
            task_id=project.tasks[-1].id_,
            data=config,
        )

        # Save to and fetch from the repository
        repository.save(conf_params)
        request.addfinalizer(lambda: repository.delete_by_id(conf_params.id_))
        fetched_config: ComponentParameters[ConfigurableParameters] = repository.get_latest_component_parameters(
            component_type=conf_params.component,
            task_id=project.tasks[-1].id_,
        )
        assert fetched_config.data is not None

        config_dict = otx_config_helper.convert(config, dict)
        fetched_config_dict = otx_config_helper.convert(fetched_config.data, dict)
        config_dict.pop("id")
        fetched_config_dict.pop("id")

        # Test fetching by component and task id
        assert config_dict == fetched_config_dict

        # Add another config for a different task to the project
        conf_params_0: ComponentParameters[ConfigurableParameters] = copy.deepcopy(conf_params)

        # Overwrite task_id and id, then save to repo
        conf_params_0.task_id = project.tasks[0].id_
        conf_params_0.id_ = repository.generate_id()

        repository.save(conf_params_0)
        request.addfinalizer(lambda: repository.delete_by_id(conf_params_0.id_))

        # Test that fetching works for both tasks individually
        fetched_config_0: ComponentParameters[ConfigurableParameters] = repository.get_latest_component_parameters(
            component_type=conf_params_0.component,
            task_id=conf_params_0.task_id,
        )
        refetched_config: ComponentParameters[ConfigurableParameters] = repository.get_latest_component_parameters(
            component_type=conf_params.component,
            task_id=conf_params.task_id,
        )
        assert refetched_config.data is not None

        refetched_config_dict = otx_config_helper.convert(refetched_config.data, dict)
        refetched_config_dict.pop("id")

        assert config_dict == refetched_config_dict
        assert conf_params_0.data is not None
        conf_dict_0 = otx_config_helper.convert(conf_params_0.data, dict)
        conf_dict_0.pop("id")
        assert fetched_config_0.data is not None
        fetched_conf_dict_0 = otx_config_helper.convert(fetched_config_0.data, dict)
        fetched_conf_dict_0.pop("id")
        assert conf_dict_0 == fetched_conf_dict_0

        # Test that fetching by project through get_all works
        all_configs = [
            config
            for config in repository.get_all()
            if isinstance(config, ComponentParameters) and config.project_id == project.id_
        ]
        assert len(all_configs) == 2

    def test_get_or_create_component_config_repo(self, request) -> None:
        """
        <b>Description:</b>
        This test verifies that the latest ComponentConfig can be retrieved from the
        ConfigurableParametersRepo, or that it
        will be created if it does not exist yet.

        <b>Input data:</b>
        Dummy configuration -- DatasetManagerConfig

        <b>Expected results:</b>
        Test passes if latest config for a component can be retrieved from the
        repository

        <b>Steps</b>
        1. Create project
        2. get_or_create config using repository
        3. Check that parameter values match config definition
        4. Create new configuration, change parameter values and save to repository
        5. Retrieve latest configuration from repository
        6. Check that the latest config holds the updated values.
        """
        # Create project and initialize repo and config
        register_model_template(request, type(None), "detection", "DETECTION", trainable=True)
        project = generate_random_annotated_project(
            request,
            "__Test component config",
            "",
            "detection",
            number_of_images=0,
        )[0]
        repository = ConfigurableParametersRepo(project.identifier)
        # Test that creating the config works
        config = repository.get_or_create_component_parameters(
            data_instance_of=DatasetManagerConfig,
            component=ComponentType.DATASET_COUNTER,
            task_id=project.tasks[-1].id_,
        )
        request.addfinalizer(lambda: repository.delete_by_id(config.id_))

        assert config.data is not None
        assert config.data.subset_parameters.test_proportion == 0.15

        # Create a new config and change the test proportion, check that get_or_create
        # returns the latest config.
        config_data = DatasetManagerConfig(header="Test dm config")  # type:ignore
        configurable_parameters: ComponentParameters = ComponentParameters(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            component=ComponentType.DATASET_COUNTER,
            id_=ConfigurableParametersRepo.generate_id(),
            task_id=project.tasks[-1].id_,
            data=config_data,
        )
        new_config_data = DatasetManagerConfig(header="Test dm config 2")  # type:ignore
        new_config_data.subset_parameters.test_proportion = 0.5
        cp_2 = copy.deepcopy(configurable_parameters)
        cp_2.data = new_config_data
        repository.save(cp_2)
        request.addfinalizer(lambda: repository.delete_by_id(cp_2.id_))

        latest_config = repository.get_or_create_component_parameters(
            data_instance_of=DatasetManagerConfig,
            component=ComponentType.DATASET_COUNTER,
            task_id=project.tasks[-1].id_,
        )

        assert latest_config.data is not None
        assert latest_config.data.subset_parameters.test_proportion == 0.5

    def test_hyper_parameters_repo(self, request) -> None:
        """
        <b>Description:</b>
        This test verifies that a default set of hyperparameters can be saved to and
        fetched from the ConfigurableParametersRepo

        <b>Input data:</b>
        ModelConfig - The default set of hyperparameters

        <b>Expected results:</b>
        Test passes if hyperparameters can be saved to and fetched from the repository

        <b>Steps</b>
        1. Create project
        2. Create default set of hyper parameters
        3. Change parameter values
        4. Save hyperparameters to ConfigurableParametersRepo
        5. Fetch hyperparameters for model storage
        6. Assert that parameter values match the saved parameters
        """
        # Create project and initialize repo and config
        register_model_template(request, type(None), "detection", "DETECTION", trainable=True)
        project = generate_random_annotated_project(
            request,
            "__Test component config",
            "",
            "detection",
            number_of_images=0,
        )[0]

        model_storage = ModelService.get_active_model_storage(
            project_identifier=project.identifier,
            task_node_id=project.get_trainable_task_nodes()[-1].id_,
        )

        configurable_parameters = DefaultModelParameters()

        configurable_parameters.learning_parameters.batch_size = 567
        configurable_parameters.learning_parameters.epochs = 1000

        hyper_parameters: HyperParameters = HyperParameters(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            model_storage_id=model_storage.id_,
            id_=ConfigurableParametersRepo.generate_id(),
            data=configurable_parameters,
        )

        repository = self.__repo_saving_and_tests(
            project=project, configurable_parameters=hyper_parameters, request=request
        )

        fetched_config: HyperParameters = repository.get_or_create_hyper_parameters(model_storage=model_storage)

        assert hyper_parameters == fetched_config
