# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Tests for the type registry system."""

import sys
from typing import Optional, Union

import numpy as np
import pytest

from getidata.type_registry import from_polars_data, register_from_polars_converter, to_numpy


def test_basic_type_conversion():
    """Test basic type conversion for registered types."""
    # Test int conversion
    result = from_polars_data(42, int)
    assert result == 42
    assert isinstance(result, int)

    # Test float conversion
    result = from_polars_data(3.14, float)
    assert result == 3.14
    assert isinstance(result, float)

    # Test str conversion
    result = from_polars_data("hello", str)
    assert result == "hello"
    assert isinstance(result, str)

    # Test numpy array conversion
    data = [1, 2, 3]
    result = from_polars_data(data, np.ndarray)
    assert isinstance(result, np.ndarray)
    np.testing.assert_array_equal(result, np.array([1, 2, 3]))


def test_union_type_conversion():
    """Test Union type conversion with both syntax styles."""
    try:
        import torch
    except ImportError:
        pytest.skip("PyTorch not available")

    data = [1.0, 2.0, 3.0]

    # Test typing.Union syntax
    union_type = Union[torch.Tensor, np.ndarray]
    result = from_polars_data(data, union_type)
    assert isinstance(result, torch.Tensor)
    assert result.tolist() == [1.0, 2.0, 3.0]

    # Test modern syntax (Python 3.10+)
    if sys.version_info >= (3, 10):
        modern_union = torch.Tensor | np.ndarray
        result = from_polars_data(data, modern_union)
        assert isinstance(result, torch.Tensor)
        assert result.tolist() == [1.0, 2.0, 3.0]


def test_union_type_fallback_behavior():
    """Test that Union types fall back to subsequent types when first conversion fails."""

    # Create custom types for testing fallback
    class FailingConverter:
        def __init__(self, data):
            raise KeyError("This converter always fails")

    class WorkingConverter:
        def __init__(self, data):
            self.data = data

    # Register converters
    register_from_polars_converter(FailingConverter, lambda x: FailingConverter(x))
    register_from_polars_converter(WorkingConverter, lambda x: WorkingConverter(x))

    # Test that union falls back to the working converter
    union_type = Union[FailingConverter, WorkingConverter]
    data = [1, 2, 3]

    result = from_polars_data(data, union_type)
    assert isinstance(result, WorkingConverter)
    assert result.data == [1, 2, 3]


def test_union_type_errors():
    """Test Union type error handling when no converters work."""

    class UnregisteredType1:
        pass

    class UnregisteredType2:
        pass

    union_type = Union[UnregisteredType1, UnregisteredType2]
    data = [1, 2, 3]

    with pytest.raises(TypeError, match="No converter registered for type"):
        from_polars_data(data, union_type)


def test_union_type_ordering():
    """Test Union type behavior with multiple working converters - first wins."""

    # Register multiple working converters
    class TypeA:
        def __init__(self, data):
            self.data = f"A:{data}"

    class TypeB:
        def __init__(self, data):
            self.data = f"B:{data}"

    register_from_polars_converter(TypeA, lambda x: TypeA(x))
    register_from_polars_converter(TypeB, lambda x: TypeB(x))

    # Should pick the first available type in the union
    union_type = Union[TypeA, TypeB]
    data = [1, 2, 3]

    result = from_polars_data(data, union_type)
    assert isinstance(result, TypeA)
    assert result.data == "A:[1, 2, 3]"

    # Change order - should pick TypeB first now
    union_type_reordered = Union[TypeB, TypeA]
    result = from_polars_data(data, union_type_reordered)
    assert isinstance(result, TypeB)
    assert result.data == "B:[1, 2, 3]"


def test_torch_converter_functionality():
    """Test PyTorch tensor converter registration and functionality."""
    try:
        import torch
    except ImportError:
        pytest.skip("PyTorch not available")

    # Test torch tensor to numpy conversion
    tensor_data = torch.tensor([1.0, 2.0, 3.0])
    numpy_result = to_numpy(tensor_data)
    assert isinstance(numpy_result, np.ndarray)
    np.testing.assert_array_almost_equal(numpy_result, np.array([1.0, 2.0, 3.0]))

    # Test polars data to torch conversion
    polars_data = [1.0, 2.0, 3.0]
    torch_result = from_polars_data(polars_data, torch.Tensor)
    assert isinstance(torch_result, torch.Tensor)
    assert torch_result.tolist() == [1.0, 2.0, 3.0]


def test_numpy_converter_functionality():
    """Test the numpy converter registration and usage."""
    # Test basic numpy conversion
    data = [[1, 2], [3, 4]]
    result = to_numpy(np.array(data))
    assert isinstance(result, np.ndarray)
    np.testing.assert_array_equal(result, np.array(data))


def test_optional_type_with_none():
    """Test Optional type conversion when polars_data is None."""
    # Test Optional[int] with None
    result = from_polars_data(None, Optional[int])
    assert result is None

    # Test Optional[str] with None
    result = from_polars_data(None, Optional[str])
    assert result is None

    # Test Optional[float] with None
    result = from_polars_data(None, Optional[float])
    assert result is None


def test_optional_type_with_data():
    """Test Optional type conversion when polars_data has actual data."""
    # Test Optional[int] with actual int data
    result = from_polars_data(42, Optional[int])
    assert result == 42
    assert isinstance(result, int)

    # Test Optional[str] with actual string data
    result = from_polars_data("hello", Optional[str])
    assert result == "hello"
    assert isinstance(result, str)

    # Test Optional[float] with actual float data
    result = from_polars_data(3.14, Optional[float])
    assert result == 3.14
    assert isinstance(result, float)


def test_union_with_none_explicit():
    """Test explicit Union[Type, None] conversion."""
    # Test Union[int, None] with None
    result = from_polars_data(None, Union[int, None])
    assert result is None

    # Test Union[int, None] with actual data
    result = from_polars_data(123, Union[int, None])
    assert result == 123
    assert isinstance(result, int)

    # Test Union[None, str] (reverse order) with None
    result = from_polars_data(None, Union[None, str])
    assert result is None

    # Test Union[None, str] with actual data
    result = from_polars_data("test", Union[None, str])
    assert result == "test"
    assert isinstance(result, str)


@pytest.mark.skipif(sys.version_info < (3, 10), reason="Requires Python 3.10+ union syntax")
def test_modern_union_with_none():
    """Test Python 3.10+ Union syntax (A | None) conversion."""
    # Test int | None with None
    union_type = eval("int | None")
    result = from_polars_data(None, union_type)
    assert result is None

    # Test int | None with actual data
    result = from_polars_data(456, union_type)
    assert result == 456
    assert isinstance(result, int)

    # Test None | str (reverse order) with None
    union_type = eval("None | str")
    result = from_polars_data(None, union_type)
    assert result is None

    # Test None | str with actual data
    result = from_polars_data("modern", union_type)
    assert result == "modern"
    assert isinstance(result, str)


def test_optional_vs_regular_union():
    """Test that Optional types behave differently from regular Union types."""

    # Create custom types for testing
    class TypeA:
        def __init__(self, data):
            self.data = f"A:{data}"

    class TypeB:
        def __init__(self, data):
            self.data = f"B:{data}"

    register_from_polars_converter(TypeA, lambda x: TypeA(x))
    register_from_polars_converter(TypeB, lambda x: TypeB(x))

    # Regular Union[TypeA, TypeB] should convert to first available type
    data = "test"
    result = from_polars_data(data, Union[TypeA, TypeB])
    assert isinstance(result, TypeA)
    assert result.data == "A:test"

    # Optional Union[TypeA, None] should return None when data is None
    result = from_polars_data(None, Union[TypeA, None])
    assert result is None

    # Optional Union[TypeA, None] should convert to TypeA when data is not None
    result = from_polars_data(data, Union[TypeA, None])
    assert isinstance(result, TypeA)
    assert result.data == "A:test"


def test_optional_with_numpy_arrays():
    """Test Optional type conversion with numpy arrays."""
    # Test Optional[np.ndarray] with None
    result = from_polars_data(None, Optional[np.ndarray])
    assert result is None

    # Test Optional[np.ndarray] with actual data
    data = [1, 2, 3]
    result = from_polars_data(data, Optional[np.ndarray])
    assert isinstance(result, np.ndarray)
    np.testing.assert_array_equal(result, np.array([1, 2, 3]))


def test_nested_optional_error_handling():
    """Test error handling for unsupported nested Optional types."""
    # This should work fine - basic Optional
    result = from_polars_data(None, Optional[int])
    assert result is None

    # Test with unregistered type in Optional
    class UnregisteredType:
        pass

    # Should raise TypeError when trying to convert to unregistered type
    with pytest.raises(TypeError, match="No converter registered for type"):
        from_polars_data("test", Optional[UnregisteredType])


def test_list_converter_functionality():
    """Test the list to numpy converter registration and usage."""
    # Test list to numpy conversion
    data = [1, 2, 3, 4]
    result = to_numpy(data)
    assert isinstance(result, np.ndarray)
    np.testing.assert_array_equal(result, np.array([1, 2, 3, 4]))

    # Test nested list conversion
    nested_data = [[1, 2], [3, 4]]
    result = to_numpy(nested_data)
    assert isinstance(result, np.ndarray)
    np.testing.assert_array_equal(result, np.array([[1, 2], [3, 4]]))


def test_typed_numpy_array_basic():
    """Test basic typed numpy array conversion from Polars data."""
    import numpy.typing as npt
    import polars as pl

    # Test Float32 typed array
    NDArrayFloat32 = npt.NDArray[np.float32]
    df = pl.DataFrame({"data": [[0.8, 0.9]]}, schema={"data": pl.List(pl.Float32())})
    result = from_polars_data(df["data"][0], NDArrayFloat32)

    assert isinstance(result, np.ndarray)
    assert result.dtype == np.float32
    np.testing.assert_array_almost_equal(result, np.array([0.8, 0.9], dtype=np.float32))

    # Test Int32 typed array
    NDArrayInt32 = npt.NDArray[np.int32]
    df = pl.DataFrame({"data": [[1, 2, 3]]}, schema={"data": pl.List(pl.Int32())})
    result = from_polars_data(df["data"][0], NDArrayInt32)

    assert isinstance(result, np.ndarray)
    assert result.dtype == np.int32
    np.testing.assert_array_equal(result, np.array([1, 2, 3], dtype=np.int32))

    # Test Float64 typed array
    NDArrayFloat64 = npt.NDArray[np.float64]
    df = pl.DataFrame({"data": [[1.5, 2.5]]}, schema={"data": pl.List(pl.Float64())})
    result = from_polars_data(df["data"][0], NDArrayFloat64)

    assert isinstance(result, np.ndarray)
    assert result.dtype == np.float64
    np.testing.assert_array_almost_equal(result, np.array([1.5, 2.5], dtype=np.float64))


def test_typed_numpy_array_dtype_conversion():
    """Test that typed numpy arrays trigger dtype conversion when needed."""
    import numpy.typing as npt
    import polars as pl

    # Test conversion from float64 to float32
    NDArrayFloat32 = npt.NDArray[np.float32]
    df = pl.DataFrame({"data": [[1.0, 2.0]]}, schema={"data": pl.List(pl.Float64())})
    result = from_polars_data(df["data"][0], NDArrayFloat32)

    assert result.dtype == np.float32, f"Expected float32 but got {result.dtype}"
    np.testing.assert_array_almost_equal(result, np.array([1.0, 2.0], dtype=np.float32))

    # Test conversion from int64 to int32
    NDArrayInt32 = npt.NDArray[np.int32]
    df = pl.DataFrame({"data": [[10, 20]]}, schema={"data": pl.List(pl.Int64())})
    result = from_polars_data(df["data"][0], NDArrayInt32)

    assert result.dtype == np.int32, f"Expected int32 but got {result.dtype}"
    np.testing.assert_array_equal(result, np.array([10, 20], dtype=np.int32))


def test_typed_numpy_array_optional():
    """Test optional typed numpy arrays (Type | None)."""
    import numpy.typing as npt
    import polars as pl

    NDArrayFloat32 = npt.NDArray[np.float32]
    OptionalFloat32 = NDArrayFloat32 | None if sys.version_info >= (3, 10) else Optional[NDArrayFloat32]

    # Test with None
    result = from_polars_data(None, OptionalFloat32)
    assert result is None

    # Test with actual data
    df = pl.DataFrame({"data": [[0.8, 0.9]]}, schema={"data": pl.List(pl.Float32())})
    result = from_polars_data(df["data"][0], OptionalFloat32)

    assert isinstance(result, np.ndarray)
    assert result.dtype == np.float32
    np.testing.assert_array_almost_equal(result, np.array([0.8, 0.9], dtype=np.float32))


def test_typed_numpy_array_preserves_dtype():
    """Test that typed numpy arrays preserve dtype from Polars when types match."""
    import numpy.typing as npt
    import polars as pl

    # When Polars dtype matches the type annotation, no conversion should occur
    NDArrayFloat32 = npt.NDArray[np.float32]
    df = pl.DataFrame({"data": [[0.5, 0.7]]}, schema={"data": pl.List(pl.Float32())})
    result = from_polars_data(df["data"][0], NDArrayFloat32)

    assert result.dtype == np.float32
    # Values should be exact (no float precision loss)
    np.testing.assert_array_equal(result, np.array([0.5, 0.7], dtype=np.float32))


def test_typed_numpy_array_various_dtypes():
    """Test typed numpy arrays with various numpy dtypes."""
    import numpy.typing as npt
    import polars as pl

    # Test uint8
    NDArrayUInt8 = npt.NDArray[np.uint8]
    df = pl.DataFrame({"data": [[1, 2, 3]]}, schema={"data": pl.List(pl.UInt8())})
    result = from_polars_data(df["data"][0], NDArrayUInt8)
    assert result.dtype == np.uint8

    # Test int64
    NDArrayInt64 = npt.NDArray[np.int64]
    df = pl.DataFrame({"data": [[100, 200]]}, schema={"data": pl.List(pl.Int64())})
    result = from_polars_data(df["data"][0], NDArrayInt64)
    assert result.dtype == np.int64

    # Test uint16
    NDArrayUInt16 = npt.NDArray[np.uint16]
    df = pl.DataFrame({"data": [[1000, 2000]]}, schema={"data": pl.List(pl.UInt16())})
    result = from_polars_data(df["data"][0], NDArrayUInt16)
    assert result.dtype == np.uint16


def test_typed_numpy_array_helper_function():
    """Test the _apply_numpy_dtype_from_type_annotation helper function directly."""
    import numpy.typing as npt

    from getidata.type_registry import _apply_numpy_dtype_from_type_annotation

    # Test dtype conversion
    NDArrayFloat32 = npt.NDArray[np.float32]
    arr = np.array([1.0, 2.0], dtype=np.float64)
    result = _apply_numpy_dtype_from_type_annotation(arr, NDArrayFloat32)
    assert result.dtype == np.float32

    # Test no conversion when dtype already matches
    arr_f32 = np.array([1.0, 2.0], dtype=np.float32)
    result = _apply_numpy_dtype_from_type_annotation(arr_f32, NDArrayFloat32)
    assert result.dtype == np.float32

    # Test with generic np.ndarray (should not convert)
    arr_f64 = np.array([1.0, 2.0], dtype=np.float64)
    result = _apply_numpy_dtype_from_type_annotation(arr_f64, np.ndarray)
    assert result.dtype == np.float64  # Should remain unchanged


def test_typed_numpy_array_round_trip():
    """Test round-trip conversion: numpy -> polars -> typed numpy."""
    import numpy.typing as npt
    import polars as pl

    NDArrayFloat32 = npt.NDArray[np.float32]

    # Original typed array
    original = np.array([0.8, 0.95, 0.87], dtype=np.float32)

    # Convert to polars-compatible format
    from getidata.type_registry import to_numpy

    polars_ready = to_numpy(original, pl.Float32())

    # Create polars series
    series = pl.Series("scores", [polars_ready], dtype=pl.List(pl.Float32()))

    # Extract back from polars
    polars_data = series[0]

    # Convert back to typed numpy array
    result = from_polars_data(polars_data, NDArrayFloat32)

    # Verify dtype and values are preserved
    assert result.dtype == np.float32
    np.testing.assert_array_almost_equal(original, result)


def test_typed_numpy_array_multidimensional():
    """Test typed numpy arrays with multidimensional data."""
    import numpy.typing as npt
    import polars as pl

    NDArrayInt32 = npt.NDArray[np.int32]

    # Test with nested lists (2D array)
    # Note: Polars List type is for 1D arrays, so we test with flattened data
    df = pl.DataFrame({"data": [[10, 15, 30, 35]]}, schema={"data": pl.List(pl.Int32())})
    result = from_polars_data(df["data"][0], NDArrayInt32)

    assert result.dtype == np.int32
    assert result.shape == (4,)
    np.testing.assert_array_equal(result, np.array([10, 15, 30, 35], dtype=np.int32))


def test_from_polars_data_returns_none_not_array_none():
    """Test that from_polars_data returns None (not array(None, dtype=object)) when data is None.

    Regression test: previously, calling from_polars_data(None, np.ndarray) would produce
    np.array(None, dtype=object) instead of None because np.array(None) creates a
    0-dimensional array wrapping None. This verifies the fix for numpy arrays and basic scalar target types.
    """
    # np.ndarray target must return None, not array(None, dtype=object)
    result = from_polars_data(None, np.ndarray)
    assert result is None

    # Scalar target types must also return None
    assert from_polars_data(None, int) is None
    assert from_polars_data(None, float) is None
    assert from_polars_data(None, str) is None
    assert from_polars_data(None, bool) is None
    assert from_polars_data(None, bytes) is None
