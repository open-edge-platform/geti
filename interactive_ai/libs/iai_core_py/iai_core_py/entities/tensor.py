# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the Tensor entity"""

import numpy as np

from iai_core_py.entities.interfaces.tensor_adapter_interface import TensorAdapterInterface
from iai_core_py.entities.metadata import IMetadata


class Tensor(IMetadata):
    """
    Represents a metadata of type tensor.
    Can be instantiated with either numpy data or a Tensor adapter (For more info, refer to :class:`TensorAdapter`).

    :param name: name of metadata
    :param tensor_adapter: Entity that complies to TensorAdapterInterface. (E.g. TensorAdapter)
    :param numpy: the numpy data of the tensor
    """

    def __init__(
        self,
        name: str,
        tensor_adapter: TensorAdapterInterface | None = None,
        numpy: np.ndarray | None = None,
    ) -> None:
        self.name = name
        if tensor_adapter is not None:
            self._numpy = tensor_adapter.numpy
        elif numpy is not None:
            self._numpy = numpy
        else:
            raise ValueError("Either the tensor adapter must be given or the numpy data must be provided")
        self.tensor_adapter = tensor_adapter

    @property
    def numpy(self) -> np.ndarray:
        """Returns the numpy representation of the Tensor."""
        if self.tensor_adapter is not None:
            return self.tensor_adapter.numpy
        return self._numpy

    @numpy.setter
    def numpy(self, value: np.ndarray):
        if self.tensor_adapter is not None and value is not None:
            raise NotImplementedError("Cannot alter the numpy value of a tensor referencing an adapter")

        self._numpy = value

    @property
    def shape(self) -> tuple[int, ...]:
        """
        Returns the shape of the Tensor. Will first try getting it from numpy, then from the adapter and otherwise
        throw a RuntimeError.
        """
        if self._numpy is not None:
            return self._numpy.shape
        if self.tensor_adapter is not None:
            return self.tensor_adapter.shape
        raise RuntimeError(
            "Tensor is corrupted and does not contain any data. Either data or adapter has to be defined."
        )

    @property
    def data_binary_filename(self) -> str:
        """Returns the filename of the Tensor in the filesystem by fetching it from the adapter."""
        if self.tensor_adapter is not None:
            return self.tensor_adapter.binary_filename
        return ""

    def __eq__(self, other: object):
        if not isinstance(other, Tensor):
            return False
        return np.array_equal(self.numpy, other.numpy)

    def __str__(self) -> str:
        return f"Tensor(`{self.name}`, {self.shape})"

    def __repr__(self):
        """Returns the representation of the tensor."""
        return f"{self.__class__.__name__}(name={self.name})"


class NullTensor(Tensor):
    """Representation of an empty tensor"""

    def __init__(self) -> None:
        super().__init__(name="", numpy=np.array([]).astype(np.uint8))

    def __repr__(self) -> str:
        return "NullTensor()"
