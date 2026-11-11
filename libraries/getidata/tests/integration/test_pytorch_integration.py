"""
Unit tests for PyTorch integration with schema, field system, and Sample class.
"""

import numpy as np
import polars as pl
import pytest

from getidata.dataset import Dataset, Sample
from getidata.fields import ImageInfo, bbox_field, image_field, image_info_field, tensor_field
from getidata.schema import AttributeInfo, Schema

try:
    import torch

    torch_available = True
except ImportError:
    torch_available = False


@pytest.mark.skipif(not torch_available, reason="PyTorch is not available")
def test_pytorch_tensor_field_polars_conversion():
    """Test TensorField to/from Polars conversion with PyTorch tensors."""
    field = tensor_field(dtype=pl.Float32())
    test_tensor = torch.tensor([[1.0, 2.0], [3.0, 4.0]], dtype=torch.float32)

    # Test to_polars
    polars_data = field.to_polars("test_tensor", test_tensor)
    assert "test_tensor" in polars_data
    assert isinstance(polars_data["test_tensor"], pl.Series)

    # Create DataFrame and test from_polars
    df = pl.DataFrame(polars_data)
    reconstructed = field.from_polars("test_tensor", 0, df, torch.Tensor)

    assert isinstance(reconstructed, torch.Tensor)
    assert torch.allclose(reconstructed, test_tensor)


@pytest.mark.skipif(not torch_available, reason="PyTorch is not available")
def test_pytorch_bbox_field_polars_conversion():
    """Test BBoxField to/from Polars conversion with PyTorch tensors."""
    field = bbox_field(dtype=pl.Float32(), normalize=False)
    test_bbox = torch.tensor([[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]], dtype=torch.float32)

    # Test to_polars
    polars_data = field.to_polars("bbox", test_bbox)
    assert "bbox" in polars_data
    assert isinstance(polars_data["bbox"], pl.Series)

    # Create DataFrame and test from_polars
    df = pl.DataFrame(polars_data)
    reconstructed = field.from_polars("bbox", 0, df, torch.Tensor)

    assert isinstance(reconstructed, torch.Tensor)
    assert torch.allclose(reconstructed, test_bbox)


@pytest.mark.skipif(not torch_available, reason="PyTorch is not available")
def test_pytorch_attribute_info_creation():
    """Test AttributeInfo creation with PyTorch tensor type."""
    field = tensor_field(dtype=pl.Float32())
    attr_info = AttributeInfo(type=torch.Tensor, field=field)

    assert attr_info.type == torch.Tensor
    assert attr_info.field == field


@pytest.mark.skipif(not torch_available, reason="PyTorch is not available")
def test_pytorch_schema_creation():
    """Test Schema creation with PyTorch tensor types."""
    attributes = {
        "image": AttributeInfo(type=torch.Tensor, field=image_field(dtype=pl.UInt8(), format="RGB")),
        "bbox": AttributeInfo(type=torch.Tensor, field=bbox_field(dtype=pl.Float32(), normalize=False)),
    }

    schema = Schema(attributes=attributes)

    assert len(schema.attributes) == 2
    assert "image" in schema.attributes
    assert "bbox" in schema.attributes
    assert schema.attributes["image"].type == torch.Tensor
    assert schema.attributes["bbox"].type == torch.Tensor


@pytest.mark.skipif(not torch_available, reason="PyTorch is not available")
def test_pytorch_schema_duplicate_field_type_assertion():
    """Test that schema creation fails with assertion when two fields have the same field type - PyTorch version."""

    # This should fail because we have two ImageFields with the same semantic context
    with pytest.raises(ValueError):

        class InvalidSample(Sample):
            image1: torch.Tensor = image_field(dtype=pl.UInt8(), format="RGB")
            image2: torch.Tensor = image_field(dtype=pl.UInt8(), format="RGB")

        # This should trigger the assertion error when schema is inferred
        InvalidSample.infer_schema()

    # This should work because the fields have different semantic contexts
    class ValidSample(Sample):
        left_image: torch.Tensor = image_field(dtype=pl.UInt8(), format="RGB", semantic="left")
        right_image: torch.Tensor = image_field(dtype=pl.UInt8(), format="RGB", semantic="right")

    # This should not raise an assertion error
    schema = ValidSample.infer_schema()
    assert len(schema.attributes) == 2
    assert "left_image" in schema.attributes
    assert "right_image" in schema.attributes


@pytest.mark.skipif(not torch_available, reason="PyTorch is not available")
def test_pytorch_sample_integration():
    """Test that Sample works specifically with PyTorch tensors."""

    class PyTorchSample(Sample):
        image: torch.Tensor = image_field(dtype=pl.UInt8(), format="RGB")
        bbox: torch.Tensor = bbox_field(dtype=pl.Float32(), normalize=False)
        label: torch.Tensor = tensor_field(dtype=pl.Int32())

    # Create PyTorch tensors
    image_data = torch.tensor([[[255, 0, 0], [0, 255, 0]], [[0, 0, 255], [255, 255, 0]]], dtype=torch.uint8)
    bbox_data = torch.tensor([0.1, 0.1, 0.9, 0.9], dtype=torch.float32)
    label_data = torch.tensor(1, dtype=torch.int32)

    # Instantiate sample with PyTorch tensors
    sample = PyTorchSample(image=image_data, bbox=bbox_data, label=label_data)

    # Test that we can access PyTorch tensors
    assert isinstance(sample.image, torch.Tensor)
    assert isinstance(sample.bbox, torch.Tensor)
    assert isinstance(sample.label, torch.Tensor)
    assert sample.image.shape == (2, 2, 3)
    assert sample.bbox.shape == (4,)
    assert sample.label.item() == 1

    # Test PyTorch-specific operations
    assert sample.image.dtype == torch.uint8
    assert sample.bbox.dtype == torch.float32
    assert sample.label.dtype == torch.int32

    # Test that we can perform PyTorch operations
    image_mean = sample.image.float().mean()
    assert isinstance(image_mean, torch.Tensor)


@pytest.mark.skipif(not torch_available, reason="PyTorch is not available")
def test_pytorch_sample_tensor_field_conversion():
    """Test PyTorch tensor field conversion to/from Polars via Dataset."""

    class PyTorchSample(Sample):
        data: torch.Tensor = tensor_field(dtype=pl.Float32())

    # Create a PyTorch tensor
    tensor_data = torch.tensor([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=torch.float32)
    sample = PyTorchSample(data=tensor_data)

    # Create dataset and add sample
    dataset = Dataset(PyTorchSample)
    dataset.append(sample)

    # Test that the DataFrame contains expected columns
    assert isinstance(dataset.df, pl.DataFrame)
    assert "data" in dataset.df.columns
    assert "data_shape" in dataset.df.columns
    assert len(dataset.df) == 1

    # Test conversion back from Dataset
    reconstructed_sample = dataset[0]
    assert isinstance(reconstructed_sample.data, torch.Tensor)
    assert torch.allclose(reconstructed_sample.data, tensor_data)


@pytest.mark.skipif(not torch_available, reason="PyTorch is not available")
def test_pytorch_mixed_with_numpy():
    """Test that PyTorch tensors can coexist with other data types."""

    class MixedSample(Sample):
        pytorch_tensor: torch.Tensor = tensor_field(dtype=pl.Float32(), semantic="left")
        numpy_array: np.ndarray = tensor_field(dtype=pl.Int32(), semantic="right")
        image_info: ImageInfo = image_info_field()

    sample = MixedSample(
        pytorch_tensor=torch.tensor([1.0, 2.0, 3.0], dtype=torch.float32),
        numpy_array=np.array([4, 5, 6], dtype=np.int32),
        image_info=ImageInfo(width=100, height=200),
    )

    # Test that both tensor types are preserved
    assert isinstance(sample.pytorch_tensor, torch.Tensor)
    assert isinstance(sample.numpy_array, np.ndarray)
    assert isinstance(sample.image_info, ImageInfo)

    # Test PyTorch-specific operations still work
    assert sample.pytorch_tensor.sum().item() == 6.0
    assert sample.numpy_array.sum() == 15
