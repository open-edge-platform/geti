# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements the repository for configuration entities
"""

import logging
from collections.abc import Callable
from copy import deepcopy
from typing import TypeVar

from pymongo import DESCENDING, IndexModel
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

import iai_core_py.configuration.helper as otx_config_helper
from iai_core_py.configuration.elements.component_parameters import ComponentParameters, NullComponentParameters
from iai_core_py.configuration.elements.configurable_parameters import ConfigurableParameters
from iai_core_py.configuration.elements.default_model_parameters import DefaultModelParameters
from iai_core_py.configuration.elements.entity_identifiers import (
    ComponentEntityIdentifier,
    EntityIdentifier,
    ModelEntityIdentifier,
)
from iai_core_py.configuration.elements.hyper_parameters import HyperParameters
from iai_core_py.configuration.enums.component_type import ComponentType
from iai_core_py.configuration.enums.configurable_parameter_type import ConfigurableParameterType
from iai_core_py.configuration.interfaces.configurable_parameters_interface import (
    IConfigurableParameterContainer,
    NullConfigurableParameterContainer,
)
from iai_core_py.entities.model_storage import ModelStorage
from iai_core_py.repos.base import ProjectBasedSessionRepo
from iai_core_py.repos.mappers.cursor_iterator import CursorIterator
from iai_core_py.repos.mappers.mongodb_mappers.configurable_parameters_mapper import ConfigurableParametersToMongo
from iai_core_py.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from iai_core_py.repos.model_storage_repo import ModelStorageRepo

from geti_types import ID, ProjectIdentifier, Session

logger = logging.getLogger(__name__)
TConfig = TypeVar("TConfig", bound=ConfigurableParameters)
TConfigurableParameters = TypeVar(
    "TConfigurableParameters",
    bound=IConfigurableParameterContainer[ConfigurableParameters],
)

WORKSPACE_ID = "workspace_id"
PROJECT_ID = "project_id"
ENTITY_IDENTIFIER_FIELD_NAME = "entity_identifier"


class ConfigurableParametersRepo(ProjectBasedSessionRepo[IConfigurableParameterContainer]):
    """
    This repository is responsible for making
    :class:`~iai_core_py.configuration.elements.Configuration` entities or subclasses thereof persistent in a database.

    The repository implements the interface :class:`~iai_core_py.entities.interfaces.repo_interface.IRepo`, meaning
    the repository follows the CRUD interface. CRUD stands for Create, Read, Update, Delete.
    It uses MongoDB to persist the serialized data.

    The :class:`ConfigurableParametersRepo` is a singleton class.
    It makes sure that all :class:`ConfigurableParametersRepo` instances are the same object.
    """

    collection_name = "configurable_parameters"

    def __init__(
        self,
        project_identifier: ProjectIdentifier,
        session: Session | None = None,
    ) -> None:
        super().__init__(
            collection_name=ConfigurableParametersRepo.collection_name,
            session=session,
            project_identifier=project_identifier,
        )

    @property
    def forward_map(self) -> Callable[[IConfigurableParameterContainer], dict]:
        return ConfigurableParametersToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], IConfigurableParameterContainer]:
        return ConfigurableParametersToMongo.backward

    @property
    def null_object(self) -> NullConfigurableParameterContainer:
        return NullConfigurableParameterContainer()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(
            cursor=mongo_cursor, mapper=ConfigurableParametersToMongo, parameter=None
        )

    @property
    def indexes(self) -> list[IndexModel]:
        super_indexes = super().indexes
        new_indexes = [
            IndexModel(  # for queries based on ModelEntityIdentifier
                [
                    (f"{ENTITY_IDENTIFIER_FIELD_NAME}.model_storage_id", DESCENDING),
                    (f"{ENTITY_IDENTIFIER_FIELD_NAME}.type", DESCENDING),
                ]
            ),
            IndexModel(  # for queries based on ComponentEntityIdentifier
                [
                    (f"{ENTITY_IDENTIFIER_FIELD_NAME}.task_id", DESCENDING),
                    (f"{ENTITY_IDENTIFIER_FIELD_NAME}.type", DESCENDING),
                    (f"{ENTITY_IDENTIFIER_FIELD_NAME}.component", DESCENDING),
                ]
            ),
        ]
        return super_indexes + new_indexes

    @staticmethod
    def __construct_query_dict(identifier_dict: dict[str, str]) -> dict[str, str]:
        """
        Construct a dictionary to query MongoDB, from a dictionary containing identifiers. Queries using nested
        dicts have to be formatted using .dot notation, this method takes care to properly format the query dict.

        :param identifier_dict: Dictionary containing the identifiers and values to query for
        :return: Flat dictionary formatted appropriately for performing MongoDB queries.
        """
        query = {}
        for key, value in identifier_dict.items():
            query[f"{ENTITY_IDENTIFIER_FIELD_NAME}.{key}"] = value
        return query

    def get_latest_by_identifier(
        self,
        entity_identifier: EntityIdentifier | dict,
        include_single_use: bool = False,
    ) -> IConfigurableParameterContainer:
        """
        Retrieve the latest Configuration entity with fields matching those specified in `entity_identifier` from
        the database.

        :param entity_identifier: The entity identifier to match, either as an object or dictionary
        :param include_single_use: If True, the method will also consider hyper-parameters
            marked as 'single-use' when trying to get the latest set of parameters.
        :return: Latest Configuration for the ConfigurableEntity matching the entity_identifier
        """
        if isinstance(entity_identifier, EntityIdentifier):
            entity_identifier_dict = entity_identifier.as_dict(exclude_keys=(WORKSPACE_ID, PROJECT_ID))
        else:
            entity_identifier_dict = entity_identifier
        serialized_identifiers = ConfigurableParametersToMongo.map_identifiers_to_strings(entity_identifier_dict)
        query: dict = self.__construct_query_dict(serialized_identifiers)
        if not include_single_use:
            query["single_use"] = {"$ne": True}  # False or unset
        return self.get_one(extra_filter=query, latest=True)

    def get_latest_component_parameters(
        self,
        component_type: ComponentType,
        task_id: ID | None = None,
    ) -> ComponentParameters:
        """
        Fetch the latest ComponentParameters for the component identified by `component_type` from the repository. For
        components that are defined per-task, a `task_id` must be specified to retrieve the config for the appropriate
        task

        :param component_type: ComponentType of the component to retrieve the latest config for
        :param task_id: Optional ID of the task to retrieve the ComponentConfig for, if the component defines its
            configuration per-task. Defaults to None
        :return: instance of the latest ComponentParameters for the component with type `component_type` and optional
            task_id `task_id` in the workspace
        """
        if task_id is None:
            task_id = ID()
        config = self.get_latest_by_identifier(
            {
                "component": component_type,
                "task_id": task_id,
                "type": ConfigurableParameterType.COMPONENT_PARAMETERS,
            }
        )
        if isinstance(config, NullConfigurableParameterContainer):
            config = NullComponentParameters()
        if not isinstance(config, ComponentParameters):
            raise ConfigurationTypeError(f"Received invalid configuration type: {type(config)}")
        return config

    def _get_or_create(
        self,
        data_instance_of: type[TConfig],
        container_instance_of: type[TConfigurableParameters],
        entity_identifier: EntityIdentifier,
    ) -> TConfigurableParameters:
        """
        Get the latest set of configurable parameters that satisfy the search criteria
        specified in `entity_identifier`, or create a new configuration if no prior
        one exists. The entity_identifier can either be an instance of a
        ModelEntityIdentifier or a ComponentEntityIdentifier.

        :param data_instance_of: The type (subclass of ConfigurableParameters) that
            holds the implementation of the configurable parameter data. The returned
            configurable parameter data will be an instance of this type
        :param entity_identifier: EntityIdentifier or dictionary object that uniquely
            identifies the entity to which the configurable parameters apply
        :return: The configurable parameters with their data attribute updated to
            reflect the latest values in the database
        """
        configurable_parameters = container_instance_of.from_entity_identifier(
            entity_identifier=entity_identifier, id=self.generate_id()
        )

        # Mypy misses the `header` argument, but this should be defined in the
        # data_instance_of type
        base_config_data = data_instance_of()  # type: ignore[call-arg]

        # Query the database to get the latest matching config
        latest_config: IConfigurableParameterContainer[ConfigurableParameters] = self.get_latest_by_identifier(
            entity_identifier=entity_identifier
        )

        if isinstance(latest_config, NullConfigurableParameterContainer) or latest_config.data is None:
            # If there is no saved config yet, commit the default one to the repository
            configurable_parameters.data = base_config_data
            self.save(configurable_parameters)
        else:
            # Otherwise, update the base config according to what is stored in the repo.
            try:
                new_config_data = deepcopy(base_config_data)
                otx_config_helper.substitute_values(
                    new_config_data,
                    value_input=latest_config.data,
                    allow_missing_values=True,
                )
                configurable_parameters.data = new_config_data
            except ValueError:
                # If the latest config is not valid with the base config, save the base config instead. This can
                # occur if the user has configuration data from a previous version in the database.
                logger.warning(
                    "Some configurable parameter values were invalid and have been overwritten with the "
                    "base configuration."
                )
                configurable_parameters.data = base_config_data
                self.save(configurable_parameters)
            configurable_parameters.id_ = latest_config.id_
        # Mypy doesn't properly recognize the return type
        return configurable_parameters  # type: ignore[return-value]

    def get_or_create_hyper_parameters(
        self,
        model_storage: ID | ModelStorage,
        data_instance_of: type[TConfig] | None = None,
        include_single_use: bool = False,
    ) -> HyperParameters[TConfig]:
        """
        Get the latest set of hyper parameters belonging to the ModelStorage. The
        `model_storage` argument can either be an ID referencing
        a ModelStorage or the actual ModelStorage object. If an ID is passed the
        ModelStorage object is retrieved from the database, so
        when available the object should be passed for better performance.

        The hyper parameters will be returned as an instance of
        the HyperParameters class, with its `data` attribute set to contain the
        parameter data as an instance of the type specified in `data_instance_of`. If
        no type is specified, the parameters will be an instance of
        `ConfigurableParameters`.

        :param model_storage: ModelStorage or ID of the ModelStorage for which
            hyper parameters should be retrieved or created in the repository.
        :param data_instance_of: The type (subclass of ConfigurableParameters) that
            holds the implementation of the configurable parameter data. The returned
            configurable parameter data will be an instance of this type. If specified,
            this will overwrite the hyper parameters defined in the model template
            associated with the model storage
        :param include_single_use: If True, the method will also consider hyper-parameters
            marked as 'single-use' when trying to get the latest set of parameters.
        :return: HyperParameter object containing the latest or newly created set of
            hyper parameters for the model storage.
        """
        if isinstance(model_storage, ID):
            model_storage_id = model_storage
            model_storage = ModelStorageRepo(self.identifier).get_by_id(model_storage_id)
        elif isinstance(model_storage, ModelStorage):
            model_storage_id = model_storage.id_
        else:
            raise ValueError(
                f"Invalid input model_storage of type "
                f"{type(model_storage)}, please specify either a "
                f"ModelStorage or an ID."
            )

        entity_identifier = ModelEntityIdentifier(  # type: ignore
            workspace_id=self.identifier.workspace_id,
            project_id=self.identifier.project_id,
            model_storage_id=model_storage_id,
        )
        requires_saving: bool = True
        parameter_id = ID()
        if data_instance_of is not None:
            # If a type is specified, this takes precedence over the model template
            hyper_parameters: HyperParameters[TConfig] = self._get_or_create(
                data_instance_of=data_instance_of,
                container_instance_of=HyperParameters,
                entity_identifier=entity_identifier,
            )
            requires_saving = False
            parameter_id = hyper_parameters.id
        else:
            # If no type is given, try to get the parameters from the template instead
            mongo_config: IConfigurableParameterContainer[ConfigurableParameters] = self.get_latest_by_identifier(
                entity_identifier={
                    "model_storage_id": model_storage_id,
                    "type": ConfigurableParameterType.HYPER_PARAMETERS,
                },
                include_single_use=include_single_use,
            )
            hyper_parameter_data = model_storage.model_template.hyper_parameters
            if hyper_parameter_data.has_valid_configurable_parameters:
                # If the model template parameters are valid, retrieve the parameters
                template_config_data = hyper_parameter_data.data
                data = otx_config_helper.create(template_config_data)
                if not isinstance(data, ConfigurableParameters):
                    raise ValueError(
                        f"Invalid configurable parameter input in model_template with "
                        f"name: {model_storage.model_template.name}. Unable to create "
                        f"ConfigurableParameters out of input yaml file: "
                        f" {hyper_parameter_data.base_path}."
                    )
                if not (isinstance(mongo_config, NullConfigurableParameterContainer) or mongo_config.data is None):
                    # Bring the parameters up to date by filling in values from the db
                    otx_config_helper.substitute_values(data, mongo_config.data, allow_missing_values=True)
                    parameter_id = mongo_config.id
                    requires_saving = True
            # If template parameters are not valid, either use the latest
            # parameters from Mongo or create a default set of parameters
            elif not isinstance(mongo_config, NullConfigurableParameterContainer) and mongo_config.data is not None:
                data = mongo_config.data
                parameter_id = mongo_config.id
                requires_saving = False
            else:
                data = DefaultModelParameters()

            hyper_parameters = HyperParameters.from_entity_identifier(  # type: ignore[assignment]
                entity_identifier=entity_identifier, data=data, id=parameter_id
            )
        hyper_parameters.id_ = self.generate_id() if parameter_id == ID() else parameter_id
        if requires_saving:
            self.save(hyper_parameters)
        return hyper_parameters

    def get_or_create_component_parameters(
        self,
        data_instance_of: type[TConfig],
        component: ComponentType,
        task_id: ID | None = None,
    ) -> ComponentParameters[TConfig]:
        """
        Get the latest set of component parameters belonging to the Component identified
        by `component`, for the project specified by `project_id` and the task
        identified by `task_id`. The component parameters will be returned as an
        instance of the ComponentParameters class, with its `data` attribute set to
        contain the parameter data as an instance of the type specified in
        `data_instance_of`.

        :param data_instance_of: The type (subclass of ConfigurableParameters) that
            holds the implementation of the configurable parameter data. The returned
            configurable parameter data will be an instance of this type
        :param project_id: ID that identifies the Project in which the
            component to retrieve the parameters for lives.
        :param component: ComponentType instance that identifies the component for
            which parameters should be retrieved or created in the repository.
        :param task_id: Optional ID of the task to which the component parameters apply
        :return: The latest set of component parameters for the component type
        """
        entity_identifier = ComponentEntityIdentifier(  # type: ignore
            workspace_id=self.identifier.workspace_id,
            project_id=self.identifier.project_id,
            component=component,
            task_id=task_id,
        )
        component_parameters: ComponentParameters[TConfig] = self._get_or_create(
            data_instance_of=data_instance_of,
            container_instance_of=ComponentParameters,
            entity_identifier=entity_identifier,
        )
        return component_parameters

    def delete_all_by_model_storage_id(self, model_storage_id: ID) -> None:
        """
        Delete all configurable parameters for the given `model_storage_id`.

        Note: only those configurable relative to a model storage will be considered;
        for example, the hyper-parameters.

        :param model_storage_id: ID of the model storage whose params should be deleted
        """
        query: dict = {f"{ENTITY_IDENTIFIER_FIELD_NAME}.model_storage_id": IDToMongo.forward(model_storage_id)}
        self.delete_all(extra_filter=query)


class ConfigurationTypeError(RuntimeError):
    """
    This error is raised when an invalid configuration type is returned from the database. For example, if a
    configuration of type `ModelConfig` is returned where a `ComponentConfig` is expected.
    """
