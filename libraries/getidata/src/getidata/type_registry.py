# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
Type conversion registry for extensible tensor/array type support.

This module provides a runtime-extensible registry system for converting between
different tensor libraries (PyTorch, NumPy, JAX, TensorFlow, etc.) and Polars
DataFrames. New types can be registered at runtime without modifying core code.
"""

import logging
import types
from collections.abc import Callable
from typing import Any, Union, get_args, get_origin

import numpy as np
import polars as pl

from getidata.errors import ArrayStructureError

logger = logging.getLogger(__name__)


POLAR_TO_NUMPY_DTYPE_MAPPING = {
    pl.Float32: np.dtype(np.float32),
    pl.Float64: np.dtype(np.float64),
    pl.Int8: np.dtype(np.int8),
    pl.Int16: np.dtype(np.int16),
    pl.Int32: np.dtype(np.int32),
    pl.Int64: np.dtype(np.int64),
    pl.UInt8: np.dtype(np.uint8),
    pl.UInt16: np.dtype(np.uint16),
    pl.UInt32: np.dtype(np.uint32),
    pl.UInt64: np.dtype(np.uint64),
    pl.Boolean: np.dtype(np.bool_),
    pl.Binary: np.dtype(np.bytes_),
}


def polars_to_numpy_dtype(polars_dtype: pl.DataType) -> np.dtype[Any]:
    """Convert a Polars dtype to the corresponding NumPy dtype.

    Args:
        polars_dtype: Polars data type to convert

    Returns:
        Corresponding NumPy dtype

    Raises:
        TypeError: If no mapping exists for the given Polars dtype

    Example:
        >>> numpy_dtype = polars_to_numpy_dtype(pl.Float32())
        >>> numpy_dtype == np.float32
        True
    """
    if polars_dtype in POLAR_TO_NUMPY_DTYPE_MAPPING:
        return POLAR_TO_NUMPY_DTYPE_MAPPING[polars_dtype]
    raise TypeError(f"No NumPy dtype mapping exists for Polars dtype: {polars_dtype}")


def is_type_optional(type_annotation: type) -> bool:
    """
    Check if a type annotation is optional (Union with None).

    Args:
        type_annotation: The type annotation to check

    Returns:
        True if the type is optional (i.e., allows None), False otherwise
    """
    origin = get_origin(type_annotation)
    if origin in {Union, types.UnionType}:
        args = get_args(type_annotation)
        return type(None) in args
    return False


# Type conversion registry - extensible at runtime
_to_numpy_converters: dict[type, Callable[[Any], np.ndarray[Any, Any] | None]] = {
    np.ndarray: lambda x: x,
    bytes: lambda x: np.array(x),
    types.NoneType: lambda _: None,
    list: lambda x: np.array(x),
}

_from_polars_converters: dict[type, Callable[[Any], Any]] = {
    np.ndarray: lambda x: np.array(x),
    int: lambda x: int(x),
    float: lambda x: float(x),
    str: lambda x: str(x),
    bytes: lambda x: bytes(x),
    bool: lambda x: bool(x),
}


def register_numpy_converter(source_type: type, converter_func: Callable[[Any], np.ndarray[Any, Any]]) -> None:
    """Register a converter function to convert from source_type to numpy array.

    Args:
        source_type: The source type to convert from
        converter_func: Function that takes a value of source_type and returns np.ndarray

    Example:
        >>> import jax.numpy as jnp
        >>> register_numpy_converter(jnp.ndarray, lambda x: np.array(x))
    """
    _to_numpy_converters[source_type] = converter_func


def register_from_polars_converter(target_type: type, converter_func: Callable[[Any], Any]) -> None:
    """Register a converter function to convert from polars data to target_type.

    Args:
        target_type: The target type to convert to
        converter_func: Function that takes polars data and returns target_type

    Example:
        >>> import jax.numpy as jnp
        >>> register_from_polars_converter(jnp.ndarray, lambda x: jnp.array(x))
    """
    _from_polars_converters[target_type] = converter_func


def to_numpy(value: Any, dtype: Any = None) -> np.ndarray[Any, Any] | None:
    """Convert any registered type to numpy array with optional dtype conversion.

    Args:
        value: Value to convert to numpy array
        dtype: Optional Polars dtype to ensure numpy array has correct dtype

    Returns:
        numpy array representation of the value with correct dtype

    Raises:
        TypeError: If the value type is not registered for conversion

    Example:
        >>> import torch
        >>> tensor = torch.tensor([1, 2, 3])
        >>> numpy_array = to_numpy(tensor)
        >>> isinstance(numpy_array, np.ndarray)
        True
    """
    value_type = type(value)  # type: ignore

    if value_type not in _to_numpy_converters and value_type not in (int, float, str, bool):
        _register_converters_if_needed()

    if value_type in _to_numpy_converters:
        numpy_value = _to_numpy_converters[value_type](value)

        # Apply dtype conversion if specified
        if dtype is not None:
            if numpy_value is None:
                return None

            if numpy_value.dtype == object:
                try:
                    nested_func = np.vectorize(lambda x: to_numpy(x, dtype), otypes=numpy_value.dtype.char)
                    numpy_value = nested_func(numpy_value)
                except ArrayStructureError as e:
                    # Re-raise with additional context about the outer array
                    raise ArrayStructureError(
                        f"{e}\n\nOuter array has shape {numpy_value.shape} and dtype {numpy_value.dtype}",
                        include_guidance=False,
                    ) from e.__cause__
            else:
                target_numpy_dtype = polars_to_numpy_dtype(dtype)
                numpy_value = numpy_value.astype(target_numpy_dtype)

        return numpy_value

    if value_type in (int, float, str, bool):
        raise ArrayStructureError(
            f"Encountered a scalar value of type '{value_type.__name__}' during array conversion."
        )

    supported_types = [t.__name__ for t in _to_numpy_converters if hasattr(t, "__name__")]
    raise TypeError(
        f"No converter registered for type {value_type.__name__}.\n"
        f"Supported types for conversion: {', '.join(supported_types)}"
    )


def _apply_numpy_dtype_from_type_annotation(array: np.ndarray, target_type: type) -> np.ndarray:
    """Apply dtype conversion to numpy array based on type annotation.

    Args:
        array: Numpy array to convert
        target_type: Type annotation containing dtype information (e.g., npt.NDArray[np.float32])

    Returns:
        Array with the correct dtype applied

    Example:
        >>> import numpy.typing as npt
        >>> arr = np.array([1.0, 2.0], dtype=np.float64)
        >>> NDArrayFloat32 = npt.NDArray[np.float32]
        >>> result = _apply_numpy_dtype_from_type_annotation(arr, NDArrayFloat32)
        >>> result.dtype == np.float32
        True
    """
    type_args = get_args(target_type)
    # type_args for np.ndarray are typically (shape, dtype)
    if len(type_args) >= 2:
        # Extract the dtype from numpy.dtype[T]
        dtype_generic = type_args[1]
        # Check if this is a numpy.dtype generic type
        if get_origin(dtype_generic) is np.dtype:
            dtype_args = get_args(dtype_generic)
            if dtype_args:
                try:
                    target_dtype = dtype_args[0]
                    # Only convert if the dtype is different
                    if array.dtype != np.dtype(target_dtype):
                        return array.astype(target_dtype)
                except (AttributeError, TypeError, ValueError):
                    # If we can't extract or apply dtype, just return the array as-is
                    pass
    return array


def from_polars_data(polars_data: Any, target_type: type) -> Any:
    """Convert polars data to target type.

    Args:
        polars_data: Data from polars DataFrame
        target_type: Target type to convert to

    Returns:
        Value converted to target_type, or None if polars_data is None

    Raises:
        TypeError: If polars_data is not None and target_type is not registered
            for conversion

    Example:
        >>> import torch
        >>> polars_data = [1, 2, 3]
        >>> tensor = from_polars_data(polars_data, torch.Tensor)
        >>> isinstance(tensor, torch.Tensor)
        True
    """
    # Null polars data should always map to None regardless of target type
    if polars_data is None:
        return None

    origin_type = get_origin(target_type)
    if target_type not in _from_polars_converters and origin_type not in _from_polars_converters:
        _register_converters_if_needed()

    # Handle direct type matches first
    if target_type in _from_polars_converters:
        return _from_polars_converters[target_type](polars_data)

    # Check if target_type is a generic type (e.g., np.ndarray[Any, np.dtype[np.float32]])
    if origin_type is not None and origin_type in _from_polars_converters:
        # Handle typed numpy arrays and other generic types
        result = _from_polars_converters[origin_type](polars_data)

        # For typed numpy arrays, apply the dtype if specified in the type annotation
        if origin_type is np.ndarray and result is not None:
            result = _apply_numpy_dtype_from_type_annotation(result, target_type)

        return result

    # Handle Union types (e.g., torch.Tensor | np.ndarray)
    # Check if target_type is a Union type (Python 3.10+ style or typing.Union)
    is_union = False
    union_args = None

    # Check for types.UnionType (Python 3.10+ syntax: A | B)
    if isinstance(target_type, types.UnionType):
        is_union = True
        union_args = target_type.__args__

    # Check for typing.Union (older syntax: Union[A, B])
    if get_origin(target_type) is Union:
        is_union = True
        union_args = get_args(target_type)

    if is_union and union_args:
        return _convert_union_types(union_args=union_args, polars_data=polars_data, target_type=target_type)
    raise TypeError(f"No converter registered for type {target_type}")


def _convert_union_types(union_args: tuple[type], polars_data: Any, target_type: type) -> Any:
    non_none_args = tuple(arg for arg in union_args if arg is not types.NoneType)

    # Try each type in the union until one succeeds
    for union_type in non_none_args:
        # Try to convert using the union type (which might be generic)
        try:
            return from_polars_data(polars_data, union_type)
        except (KeyError, TypeError):
            # If conversion fails, try the next type in the union
            continue

    # If all conversions failed, raise TypeError
    raise TypeError(f"No converter registered for type {target_type}")


def _register_torch_converters() -> None:
    if getattr(_register_torch_converters, "_done", False):
        return
    # Register PyTorch converters if available
    try:
        import torch  # pyright: ignore[reportMissingImports]

        register_numpy_converter(torch.Tensor, lambda x: x.detach().cpu().numpy())  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        register_from_polars_converter(torch.Tensor, lambda x: torch.tensor(x))  # pyright: ignore[reportUnknownMemberType, reportUnknownLambdaType, reportUnknownArgumentType]
    except ImportError:
        pass
    finally:
        _register_torch_converters._done = True  # type: ignore[attr-defined]


def _register_torchvision_converters() -> None:
    if getattr(_register_torchvision_converters, "_done", False):
        return
    # Register torchvision converters if available
    try:
        from torchvision import tv_tensors  # pyright: ignore[reportMissingImports]

        register_numpy_converter(tv_tensors.Image, lambda x: x.detach().cpu().numpy())  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]

        register_numpy_converter(tv_tensors.BoundingBoxes, lambda x: x.detach().cpu().numpy())  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]

        register_numpy_converter(tv_tensors.Mask, lambda x: x.detach().cpu().numpy())  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]

        # Conversion from Polars to tv_tensors BoundingBoxes and Keypoints are not supported
        # because tv_tensors BoundingBoxes and Keypoints require the image size which is not available during
        # conversion.
        register_from_polars_converter(tv_tensors.Image, lambda x: tv_tensors.Image(x))  # pyright: ignore[reportUnknownMemberType, reportUnknownLambdaType, reportUnknownArgumentType]

        register_from_polars_converter(tv_tensors.Mask, lambda x: tv_tensors.Mask(x))  # pyright: ignore[reportUnknownMemberType, reportUnknownLambdaType, reportUnknownArgumentType]
    except ImportError:
        pass
    finally:
        _register_torchvision_converters._done = True  # type: ignore[attr-defined]


def _register_converters_if_needed() -> None:
    _register_torch_converters()
    _register_torchvision_converters()


def is_tv_tensors_bounding_boxes(value: Any) -> bool:
    """Check if value is a tv_tensors.BoundingBoxes instance.

    Args:
        value: The value to check

    Returns:
        True if value is a tv_tensors.BoundingBoxes instance, False otherwise
    """
    try:
        from torchvision import tv_tensors  # pyright: ignore[reportMissingImports]

        return isinstance(value, tv_tensors.BoundingBoxes)
    except ImportError:
        return False


def get_tv_tensors_canvas_size(value: Any) -> tuple[int, int] | None:
    """Extract canvas_size from tv_tensors.BoundingBoxes.

    Args:
        value: A tv_tensors.BoundingBoxes instance

    Returns:
        The canvas_size tuple (height, width) or None if not a BoundingBoxes
    """
    if is_tv_tensors_bounding_boxes(value):
        return value.canvas_size  # type: ignore
    return None


def create_tv_tensors_bounding_boxes(data: Any, canvas_size: tuple[int, int], bbox_format: str) -> Any:
    """Create tv_tensors.BoundingBoxes from numpy data.

    Args:
        data: The bounding box data (numpy array or list)
        canvas_size: The canvas size as (height, width)
        bbox_format: The bounding box format string (e.g., "x1y1x2y2", "xywh")

    Returns:
        A tv_tensors.BoundingBoxes instance, or the original data if torchvision is not available
    """
    try:
        import torch  # pyright: ignore[reportMissingImports]
        from torchvision import tv_tensors  # pyright: ignore[reportMissingImports]

        # Map format string to BoundingBoxFormat enum
        format_map = {
            "x1y1x2y2": tv_tensors.BoundingBoxFormat.XYXY,
            "xyxy": tv_tensors.BoundingBoxFormat.XYXY,
            "xywh": tv_tensors.BoundingBoxFormat.XYWH,
            "cxcywh": tv_tensors.BoundingBoxFormat.CXCYWH,
        }
        tv_format = format_map.get(bbox_format.lower(), tv_tensors.BoundingBoxFormat.XYXY)

        # Normalize data to a format torch.tensor can handle
        if hasattr(data, "to_numpy"):
            # Polars Series or similar
            normalized = np.array(data.to_numpy())
        elif hasattr(data, "to_list"):
            normalized = data.to_list()
        else:
            normalized = data

        tensor_data = torch.as_tensor(np.array(normalized)).reshape(-1, 4)

        return tv_tensors.BoundingBoxes(
            tensor_data,
            format=tv_format,
            canvas_size=canvas_size,
        )
    except ImportError:
        return data


# Register PIL Image converters if available
try:
    from PIL import Image

    register_numpy_converter(Image.Image, lambda x: np.array(x))
    register_from_polars_converter(Image.Image, lambda x: Image.fromarray(np.array(x)))
except ImportError:
    pass


def convert_image_type(image: Any, target_type: type) -> Any:
    """
    Convert an image between different types (numpy, PIL, torch).
    This function provides direct conversion between image types using
    the registered converters in the type registry.
    Args:
        image: Source image (numpy.ndarray, PIL.Image.Image, or torch.Tensor)
        target_type: Target type to convert to
    Returns:
        Image converted to the target type
    Raises:
        TypeError: If source or target type is not supported
    Example:
        >>> import numpy as np
        >>> from PIL import Image
        >>> import torch
        >>>
        >>> # Convert numpy array to PIL Image
        >>> np_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        >>> pil_image = convert_image_type(np_image, Image.Image)
        >>>
        >>> # Convert PIL Image to torch tensor
        >>> torch_image = convert_image_type(pil_image, torch.Tensor)
    """
    current_type = type(image)

    # Define supported image types - only numpy, PIL Image, and torch Tensor
    supported_image_types = get_supported_image_types()

    # Validate that target_type is a supported image type
    if target_type not in supported_image_types:
        supported_names = [t.__name__ for t in supported_image_types]
        raise TypeError(f"Target type {target_type.__name__} not supported. Supported image types: {supported_names}")

    # If already the target type, return as-is
    if current_type == target_type:
        return image

    # Convert via numpy as intermediate format
    try:
        # First convert to numpy if not already
        if current_type == np.ndarray:
            numpy_image = image
        else:
            numpy_image = to_numpy(image)

        # Then convert from numpy to target type
        if target_type == np.ndarray:
            return numpy_image

        if target_type not in _from_polars_converters:
            _register_torch_converters()
        # Convert numpy to target via polars-style conversion
        return _from_polars_converters[target_type](numpy_image)

    except Exception as e:
        raise TypeError(f"Cannot convert from {current_type} to {target_type}: {e}")


def get_supported_image_types() -> list[type]:
    """
    Get a list of all supported image types for conversion.
    Returns:
        List of supported image types
    """
    _register_converters_if_needed()
    supported_types = [np.ndarray]  # numpy is always supported

    # Add conditionally available types
    try:
        from PIL import Image

        if Image.Image in _from_polars_converters:
            supported_types.append(Image.Image)
    except ImportError:
        pass

    # Check for torch
    try:
        import torch

        if torch.Tensor in _from_polars_converters:
            supported_types.append(torch.Tensor)
    except ImportError:
        pass

    return supported_types
