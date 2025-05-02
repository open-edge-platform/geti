#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

"""Interfaces for MongoDB mappers"""

from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar

from iai_core_py.entities.dataset_storage import DatasetStorage
from iai_core_py.entities.model_storage import ModelStorage, ModelStorageIdentifier
from iai_core_py.entities.project import Project

from geti_types import DatasetStorageIdentifier, ProjectIdentifier

# Python object (before mapping)
MappableEntityType = TypeVar("MappableEntityType")
# MongoDB compatible type (after mapping)
MappedEntityType = TypeVar("MappedEntityType")

MapperForwardParametersType = TypeVar("MapperForwardParametersType")
MapperBackwardParametersType = TypeVar("MapperBackwardParametersType")
MapperInitParametersType = TypeVar("MapperInitParametersType")


class IMapperForward(Generic[MappableEntityType, MappedEntityType], metaclass=ABCMeta):
    """
    Interface for stateless forward mappers that can convert Python objects to their
    serialized MongoDB representation (BSON). The conversion needs no extra parameters.
    """

    @staticmethod
    @abstractmethod
    def forward(instance: MappableEntityType) -> MappedEntityType:
        """
        Convert an object to its BSON-equivalent representation.

        :param instance: Python object to serialize
        :return: Serialized representation of the object
        """


class IMapperBackward(Generic[MappableEntityType, MappedEntityType], metaclass=ABCMeta):
    """
    Interface for stateless backward mappers that can build Python objects from a
    serialized MongoDB representation (BSON). The conversion needs no extra parameters.
    """

    @staticmethod
    @abstractmethod
    def backward(instance: MappedEntityType) -> MappableEntityType:
        """
        Build an object from its BSON-equivalent representation.

        :param instance: Serialized representation of the object
        :return: Python object
        """


class IMapperProjectBackward(Generic[MappableEntityType, MappedEntityType], metaclass=ABCMeta):
    """
    Interface for stateless backward mappers that can convert Python objects to their
    serialized MongoDB representation (BSON).
    An additional Project parameter must be provided for the conversion.
    """

    @staticmethod
    @abstractmethod
    def backward(instance: MappedEntityType, project: Project) -> MappableEntityType:
        """
        Build an object from its BSON-equivalent representation.

        :param instance: Serialized representation of the object
        :param project: Project associated with the object
        :return: Deserialized Python object
        """


class IMapperProjectIdentifierBackward(Generic[MappableEntityType, MappedEntityType], metaclass=ABCMeta):
    """
    Interface for stateless backward mappers that can convert Python objects to their
    serialized MongoDB representation (BSON).
    An additional ProjectIdentifier parameter must be provided for the conversion.
    """

    @staticmethod
    @abstractmethod
    def backward(instance: MappedEntityType, project_identifier: ProjectIdentifier) -> MappableEntityType:
        """
        Build an object from its BSON-equivalent representation.

        :param instance: Serialized representation of the object
        :param project_identifier: Identifier of the project where the object is stored
        :return: Deserialized Python object
        """


class IMapperDatasetStorageForward(Generic[MappableEntityType, MappedEntityType], metaclass=ABCMeta):
    """
    Interface for stateless forward mappers that can convert Python objects to their
    serialized MongoDB representation (BSON).
    An additional DatasetStorage parameter must be provided for the conversion.
    """

    @staticmethod
    @abstractmethod
    def forward(instance: MappableEntityType, dataset_storage: DatasetStorage) -> MappedEntityType:
        """
        Convert an object to its BSON-equivalent representation.

        :param instance: Python object to serialize
        :param dataset_storage: DatasetStorage associated with the object
        :return: Serialized representation of the object
        """


class IMapperDatasetStorageBackward(Generic[MappableEntityType, MappedEntityType], metaclass=ABCMeta):
    """
    Interface for stateless backward mappers that can convert Python objects to their
    serialized MongoDB representation (BSON).
    An additional DatasetStorage parameter must be provided for the conversion.
    """

    @staticmethod
    @abstractmethod
    def backward(instance: MappedEntityType, dataset_storage: DatasetStorage) -> MappableEntityType:
        """
        Build an object from its BSON-equivalent representation.

        :param instance: Dict representation of the object
        :param dataset_storage: DatasetStorage associated with the object
        :return: Deserialized Python object
        """


class IMapperDatasetStorageIdentifierBackward(Generic[MappableEntityType, MappedEntityType], metaclass=ABCMeta):
    """
    Interface for stateless backward mappers that can convert Python objects to their
    serialized MongoDB representation (BSON).
    An additional DatasetStorageIdentifier parameter must be provided for the conversion
    """

    @staticmethod
    @abstractmethod
    def backward(
        instance: MappedEntityType, dataset_storage_identifier: DatasetStorageIdentifier
    ) -> MappableEntityType:
        """
        Build an object from its BSON-equivalent representation.

        :param instance: Serialized representation of the object
        :param dataset_storage_identifier: Identifier of the dataset storage that
            contains the object
        :return: Deserialized Python object
        """


class IMapperModelStorageForward(Generic[MappableEntityType, MappedEntityType], metaclass=ABCMeta):
    """
    Interface for stateless forward mappers that can convert Python objects to their
    serialized MongoDB representation (BSON).
    An additional ModelStorage parameter must be provided for the conversion.
    """

    @staticmethod
    @abstractmethod
    def forward(instance: MappableEntityType, model_storage: ModelStorage) -> MappedEntityType:
        """
        Convert an object to its BSON-equivalent representation.

        :param instance: Python object to serialize
        :param model_storage: ModelStorage associated with the object
        :return: Serialized representation of the object
        """


class IMapperModelStorageBackward(Generic[MappableEntityType, MappedEntityType], metaclass=ABCMeta):
    """
    Interface for stateless backward mappers that can convert Python objects to their
    serialized MongoDB representation (BSON).
    An additional ModelStorage parameter must be provided for the conversion.
    """

    @staticmethod
    @abstractmethod
    def backward(instance: MappedEntityType, model_storage: ModelStorage) -> MappableEntityType:
        """
        Build an object from its BSON-equivalent representation.

        :param instance: Dict representation of the object
        :param model_storage: ModelStorage associated with the object
        :return: Deserialized Python object
        """


class IMapperModelStorageIdentifierBackward(Generic[MappableEntityType, MappedEntityType], metaclass=ABCMeta):
    """
    Interface for stateless backward mappers that can convert Python objects to their
    serialized MongoDB representation (BSON).
    An additional ModelStorageIdentifier parameter must be provided for the conversion
    """

    @staticmethod
    @abstractmethod
    def backward(instance: MappedEntityType, model_storage_identifier: ModelStorageIdentifier) -> MappableEntityType:
        """
        Build an object from its BSON-equivalent representation.

        :param instance: Serialized representation of the object
        :param model_storage_identifier: Identifier of the model storage that
            contains the object
        :return: Deserialized Python object
        """


class IMapperParametricForward(
    Generic[MappableEntityType, MappedEntityType, MapperForwardParametersType],
    metaclass=ABCMeta,
):
    """
    Interface for stateless forward mappers that can convert Python objects to their
    serialized MongoDB representation (BSON).
    Additional parameters of custom type must be provided for the conversion.
    """

    @staticmethod
    @abstractmethod
    def forward(instance: MappableEntityType, parameters: MapperForwardParametersType) -> MappedEntityType:
        """
        Convert an object to its BSON-equivalent representation.

        :param instance: Python object to serialize
        :param parameters: Parameters to control the mapping process
        :return: Serialized representation of the object
        """


class IMapperParametricBackward(
    Generic[MappableEntityType, MappedEntityType, MapperBackwardParametersType],
    metaclass=ABCMeta,
):
    """
    Interface for stateless backward mappers that can convert Python objects to their
    serialized MongoDB representation (BSON).
    Additional parameters of custom type must be provided for the conversion.
    """

    @staticmethod
    @abstractmethod
    def backward(instance: MappedEntityType, parameters: MapperBackwardParametersType) -> MappableEntityType:
        """
        Build an object from its BSON-equivalent representation.

        :param instance: Dict representation of the object
        :param parameters: Parameters to control the mapping process
        :return: Deserialized Python object
        """


class IMapperSimple(
    IMapperForward[MappableEntityType, MappedEntityType],
    IMapperBackward[MappableEntityType, MappedEntityType],
    metaclass=ABCMeta,
):
    """Alias for a simple forward-backward mapper interface without extra parameters"""


MapperClassT = TypeVar(
    "MapperClassT",
    bound=type[IMapperForward]
    | type[IMapperDatasetStorageForward]
    | type[IMapperModelStorageForward]
    | type[IMapperParametricForward]
    | type[IMapperBackward]
    | type[IMapperProjectBackward]
    | type[IMapperProjectIdentifierBackward]
    | type[IMapperDatasetStorageBackward]
    | type[IMapperDatasetStorageIdentifierBackward]
    | type[IMapperModelStorageBackward]
    | type[IMapperModelStorageIdentifierBackward]
    | type[IMapperParametricBackward],
)


class MappingError(RuntimeError):
    """
    This class represents an error encountered in the MongoDB mapping
    """
