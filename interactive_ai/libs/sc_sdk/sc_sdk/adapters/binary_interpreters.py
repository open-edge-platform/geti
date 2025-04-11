"""
This module contains the definition of IBinaryInterpreter and the implementation of the interface
"""

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

import abc
import os
from typing import BinaryIO, Generic, TypeVar

import cv2
import numpy as np

SUPPORTED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".jfif", ".webp"]


T = TypeVar("T")


class IBinaryInterpreter(Generic[T], metaclass=abc.ABCMeta):
    """
    This interface is for all binary interpreters.
    Binary interpreters are able to translate file-like objects, such as open, BytesIO, etc.
    into usable entities, such as numpy arrays, strings or Python dictionaries.
    """

    @abc.abstractmethod
    def interpret(self, data: BinaryIO, filename: str) -> T:
        """
        This function translates binary data to the expected output.

        :param data: The binary input data
        :param filename: Name of the file to be interpreted
        """
        raise NotImplementedError


class RAWBinaryInterpreter(IBinaryInterpreter[bytes]):
    """
    This binary interpreter translates the data from a file-like object into a bytes array.
    """

    def interpret(self, data: BinaryIO, filename: str) -> bytes:  # noqa: ARG002
        data_bytes = data.read()
        if not data.closed:
            data.close()

        return data_bytes


class StreamBinaryInterpreter(IBinaryInterpreter[BinaryIO]):
    """
    This binary interpreter translates the data from a file-like object using BinaryIO.
    """

    def interpret(self, data: BinaryIO, filename: str) -> BinaryIO:  # noqa: ARG002
        return data


class NumpyBinaryInterpreter(IBinaryInterpreter[np.ndarray]):
    """
    This binary interpreter translates binary data from a file-like object into a Numpy array.
    The binary data needs to in numpy binary formats, as described in the .npy, or .npz file-format.
    """

    def interpret(self, data: BinaryIO, filename: str) -> np.ndarray:
        extension = str(os.path.splitext(filename)[1]).lower()

        if extension in SUPPORTED_IMAGE_EXTENSIONS:
            ret = self.read_image_from_bytes(extension=extension, data=data.read())
        elif extension in [".npy", ".npz"]:
            array = np.load(data)
            # If compressed as npz, fetch stored array
            if isinstance(array, np.lib.npyio.NpzFile):
                array = array["array"]
            ret = array
        else:
            raise NotImplementedError(f"Unsupported extension `{extension}` (from filename '{filename}')")

        if not data.closed:
            data.close()
        return ret

    @staticmethod
    def read_image_from_bytes(data: bytes, extension: str = ".png") -> np.ndarray:
        """
        Reads an image from bytes and returns it as a numpy array.

        :param extension: The extension that represents the format of the image
        :param data: The image data in bytes
        :return: The image as a numpy array
        """
        if extension not in SUPPORTED_IMAGE_EXTENSIONS:
            raise NotImplementedError(f"Unsupported extension `{extension}`")

        if data == b"":
            # cv2.imdecode will throw an error if the data is empty, so we return an empty array
            return np.empty((0, 0, 3), np.uint8)
        npd = np.frombuffer(data, np.uint8)
        bgr_image = cv2.imdecode(npd, -1)
        ret = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        del npd
        del bgr_image
        return ret

    @staticmethod
    def get_bytes_from_numpy(image_numpy: np.ndarray, extension: str = ".png") -> bytes:
        """
        Reads a numpy array and converts it to an image bytes.

        :param extension: The extension that represents the format of the image
        :param image_numpy: The numpy array (h, w, c) that represents an image
        :return: The image as a bytes data
        """
        if extension not in SUPPORTED_IMAGE_EXTENSIONS:
            raise NotImplementedError(f"Unsupported extension `{extension}`")

        _, data = cv2.imencode(extension, image_numpy)
        return data.tobytes()
