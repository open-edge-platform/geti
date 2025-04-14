"""This module implements the TensorAdapterInterface"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import abc

import numpy as np


class TensorAdapterInterface(metaclass=abc.ABCMeta):
    """
    This interface describes how the Adapter looks like that allows an entity,
    such as a Tensor entity to fetch its data and shape lazily.
    """

    def __init__(self, repo_adapter, binary_filename: str) -> None:  # noqa: ANN001
        self.repo_adapter = repo_adapter
        self.binary_filename = binary_filename

    @property
    @abc.abstractmethod
    def shape(self) -> tuple[int, ...]:
        """Returns the shape of the Tensor"""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def numpy(self) -> np.ndarray:
        """Returns the numpy representation of the Tensor"""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def size_on_storage(self) -> int:
        """Returns the size of the Tensor on the filesystem"""
        raise NotImplementedError
