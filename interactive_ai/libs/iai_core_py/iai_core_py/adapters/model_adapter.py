# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the ModelAdapterInterface"""

import abc
from typing import TYPE_CHECKING

from iai_core_py.adapters.binary_interpreters import RAWBinaryInterpreter

if TYPE_CHECKING:
    from iai_core_py.repos import BinaryRepo


class DataSource:
    """
    Class that holds a combination of both a repo and a filename which can be used to fetch data
    """

    def __init__(self, repository: "BinaryRepo", binary_filename: str) -> None:
        self.repo_adapter = repository
        self._binary_filename = binary_filename

    @property
    def data(self) -> bytes:
        """Returns the data of the source"""
        return self.repo_adapter.get_by_filename(  # type: ignore[return-value]
            filename=self.binary_filename, binary_interpreter=RAWBinaryInterpreter()
        )

    @property
    def size(self) -> int:
        """Returns the size in bytes."""
        return self.repo_adapter.get_object_size(filename=self.binary_filename)

    @property
    def binary_filename(self) -> str:
        """Return binary filename of datasource"""
        return self._binary_filename

    @binary_filename.setter
    def binary_filename(self, value: str) -> None:
        """Set binary filename of datasource"""
        self._binary_filename = value


class ModelAdapter(metaclass=abc.ABCMeta):
    """The ModelAdapter is an adapter is intended to lazily fetch its binary data from a given data source."""

    def __init__(self, data_source: DataSource | bytes):
        self.__data_source = data_source

    @property
    def data_source(self) -> DataSource | bytes:
        """Returns the data source of the adapter."""
        return self.__data_source

    @data_source.setter
    def data_source(self, value: DataSource | bytes) -> None:
        self.__data_source = value

    @property
    def data(self) -> bytes:
        """Returns the data of the Model."""
        if isinstance(self.__data_source, DataSource):
            return self.__data_source.data
        if isinstance(self.__data_source, bytes):
            return self.__data_source
        raise ValueError("This model adapter is not properly initialized with a source of data")

    @property
    def from_file_storage(self) -> bool:
        """Returns if the ModelAdapters data comes from the file storage or not.

        This is used in the model repo to know if the data of the model should be saved or not.
        """
        return not isinstance(self.data_source, bytes)


class ExportableCodeAdapter(ModelAdapter):
    """Adapter intended to lazily fetch raw exportable code data from a given data source."""
