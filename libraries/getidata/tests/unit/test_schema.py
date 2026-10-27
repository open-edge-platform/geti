"""
Unit tests for schema and field system.
"""

from typing import Any, cast

import numpy as np
import polars as pl
import pytest

from getidata.categories import LabelCategories, MaskCategories
from getidata.dataset import Sample
from getidata.fields import (
    BBoxField,
    ImageBytesField,
    ImageCallableField,
    ImageField,
    ImageInfo,
    ImageInfoField,
    ImagePathField,
    InstanceMaskCallableField,
    InstanceMaskField,
    MaskCallableField,
    MaskField,
    PolygonField,
    RotatedBBoxField,
    Subset,
    SubsetField,
    TensorField,
    bbox_field,
    image_bytes_field,
    image_callable_field,
    image_field,
    image_info_field,
    image_path_field,
    instance_mask_callable_field,
    instance_mask_field,
    mask_callable_field,
    mask_field,
    polygon_field,
    rotated_bbox_field,
    subset_field,
    tensor_field,
)
from getidata.fields.annotations import LabelField, label_field
from getidata.schema import AttributeInfo, Schema


def test_get_fields_with_valid_categories():
    lbl_field = label_field()
    lbl_categories = LabelCategories(labels=("a", "b"))
    lbl_attribute_info = AttributeInfo(type=LabelField, field=lbl_field, categories=lbl_categories)

    img_field = image_info_field()
    img_attribute_info = AttributeInfo(type=ImageInfoField, field=img_field)

    schema = Schema(attributes={"label_attribute": lbl_attribute_info, "image_attribute": img_attribute_info})

    result = schema.get_fields_with_required_categories()

    assert result == {"label_attribute": lbl_categories}


def test_get_fields_with_wrong_categories():
    lbl_field = label_field()
    lbl_categories = MaskCategories()
    lbl_attribute_info = AttributeInfo(type=LabelField, field=lbl_field, categories=lbl_categories)

    schema = Schema(attributes={"label_attribute": lbl_attribute_info})

    with pytest.raises(ValueError):
        schema.get_fields_with_required_categories()


def test_get_fields_with_none_categories():
    lbl_field = label_field()
    lbl_attribute_info = AttributeInfo(type=LabelField, field=lbl_field)

    schema = Schema(attributes={"label_attribute": lbl_attribute_info})

    with pytest.raises(ValueError):
        schema.get_fields_with_required_categories()


def test_tensor_field_creation():
    """Test TensorField creation and properties."""
    field = tensor_field(dtype=pl.Float32())

    assert isinstance(field, TensorField)
    assert field.dtype == pl.Float32
    assert field.semantic == "default"


def test_tensor_field_polars_schema():
    """Test TensorField Polars schema generation."""
    field = tensor_field(dtype=pl.Float32())
    schema = field.to_polars_schema("test_tensor")

    expected = {
        "test_tensor": pl.List(pl.Float32()),
        "test_tensor_shape": pl.List(pl.Int32()),
    }
    assert schema == expected


def test_tensor_field_polars_conversion():
    """Test TensorField to/from Polars conversion."""
    field = cast("TensorField", tensor_field(dtype=pl.Float32()))
    test_tensor = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)

    # Test to_polars
    polars_data = field.to_polars("test_tensor", test_tensor)
    assert "test_tensor" in polars_data
    assert isinstance(polars_data["test_tensor"], pl.Series)

    # Create DataFrame and test from_polars
    df = pl.DataFrame(polars_data)
    reconstructed = cast("np.ndarray[Any, Any]", field.from_polars("test_tensor", 0, df, np.ndarray))

    assert isinstance(reconstructed, np.ndarray)
    assert np.allclose(reconstructed, test_tensor)


def test_tensor_field_3d_tensor_roundtrip():
    """Test TensorField preserves a generic 3D tensor through a round-trip."""
    field = TensorField(dtype=pl.UInt8())
    test_tensor = np.random.randint(0, 255, (3, 720, 1280), dtype=np.uint8)

    polars_data = field.to_polars("img", test_tensor)
    df = pl.DataFrame(polars_data)

    # Stored shape matches input exactly
    stored_shape = df["img_shape"][0].to_list()
    assert stored_shape == [3, 720, 1280]

    # Returned data matches input exactly
    reconstructed = cast("np.ndarray[Any, Any]", field.from_polars("img", 0, df, np.ndarray))
    assert reconstructed.shape == (3, 720, 1280)
    assert np.array_equal(reconstructed, test_tensor)


def test_image_field_channels_first_roundtrip():
    """Test ImageField channels_first: user provides CHW, stored as HWC internally, returned as CHW."""
    img_field = ImageField(dtype=pl.UInt8(), channels_first=True)
    # User provides CHW
    test_image = np.random.randint(0, 255, (3, 720, 1280), dtype=np.uint8)

    polars_data = img_field.to_polars("img", test_image)
    df = pl.DataFrame(polars_data)

    # Internally stored as HWC
    stored_shape = df["img_shape"][0].to_list()
    assert stored_shape == [720, 1280, 3]

    # Returned to user as CHW
    reconstructed = cast("np.ndarray[Any, Any]", img_field.from_polars("img", 0, df, np.ndarray))
    assert reconstructed.shape == (3, 720, 1280)
    assert np.array_equal(reconstructed, test_image)


def test_image_field_creation():
    """Test ImageField creation and properties."""
    field = image_field(dtype=pl.UInt8(), format="RGB", semantic="left")

    assert isinstance(field, ImageField)
    assert field.dtype == pl.UInt8
    assert field.format == "RGB"
    assert field.semantic == "left"


def test_image_field_polars_schema():
    """Test ImageField Polars schema generation."""
    field = image_field(dtype=pl.UInt8(), format="RGB")
    schema = field.to_polars_schema("image")

    expected = {"image": pl.List(pl.UInt8()), "image_shape": pl.List(pl.Int32())}
    assert schema == expected


def test_image_bytes_field_creation():
    """Test ImageBytesField creation and properties."""
    field = image_bytes_field(semantic="bbox")

    assert isinstance(field, ImageBytesField)
    assert field.semantic == "bbox"


def test_image_bytes_field_polars_schema():
    """Test ImageBytesField Polars schema generation."""
    field = image_bytes_field()
    schema = field.to_polars_schema("image_bytes")

    expected = {"image_bytes": pl.Binary()}
    assert schema == expected


def test_image_bytes_field_polars_conversion_with_numpy():
    """Test ImageBytesField to/from Polars conversion with numpy arrays."""
    field = image_bytes_field()
    image_bytes = np.array(np.random.bytes(30))

    # Test to_polars with numpy array
    polars_data = field.to_polars("image_bytes", image_bytes)
    assert "image_bytes" in polars_data
    assert isinstance(polars_data["image_bytes"][0], bytes)
    assert len(polars_data["image_bytes"][0]) > 0

    # Create DataFrame and test from_polars
    df = pl.DataFrame(polars_data)
    reconstructed = field.from_polars("image_bytes", 0, df, np.ndarray)

    assert isinstance(reconstructed, np.ndarray)
    assert np.all(reconstructed == image_bytes)


def test_image_bytes_field_polars_conversion_with_bytes():
    """Test ImageBytesField to/from Polars conversion with direct bytes."""
    field = image_bytes_field()
    image_bytes = np.array(np.random.bytes(30))

    # Test to_polars with bytes
    polars_data = field.to_polars("image_bytes", image_bytes)
    assert "image_bytes" in polars_data
    assert polars_data["image_bytes"][0] == image_bytes

    # Create DataFrame and test from_polars
    df = pl.DataFrame(polars_data)
    reconstructed = field.from_polars("image_bytes", 0, df, bytes)

    assert isinstance(reconstructed, bytes)
    assert reconstructed == image_bytes


def test_bbox_field_creation():
    """Test BBoxField creation and properties."""
    field = bbox_field(dtype=pl.Float32(), format="x1y1x2y2", normalize=True)

    assert isinstance(field, BBoxField)
    assert field.dtype == pl.Float32
    assert field.format == "x1y1x2y2"
    assert field.normalize is True
    assert field.semantic == "default"


def test_bbox_field_polars_schema():
    """Test BBoxField Polars schema generation."""
    field = bbox_field(dtype=pl.Float32())
    schema = field.to_polars_schema("bbox")

    expected = {
        "bbox": pl.List(pl.Array(pl.Float32, 4)),
    }
    assert schema == expected


def test_instance_mask_field_creation():
    """Test InstanceMaskField creation and properties."""
    field = instance_mask_field(dtype=pl.Boolean())

    assert isinstance(field, InstanceMaskField)
    assert field.dtype == pl.Boolean
    assert field.semantic == "default"


def test_instance_mask_field_polars_schema():
    """Test InstanceMaskField Polars schema generation."""
    field = instance_mask_field(dtype=pl.Boolean())
    schema = field.to_polars_schema("instance_mask")

    expected = {
        "instance_mask": pl.List(pl.Boolean()),
        "instance_mask_shape": pl.List(pl.Int32()),
    }
    assert schema == expected


def test_instance_mask_field_polars_conversion():
    """Test InstanceMaskField to/from Polars conversion."""
    field = cast("InstanceMaskField", instance_mask_field(dtype=pl.Boolean()))
    test_mask = np.array([[[True, False], [False, True]], [[False, True], [True, False]]], dtype=bool)  # (2,2,2)

    # Test to_polars
    polars_data = field.to_polars("instance_mask", test_mask)
    assert "instance_mask" in polars_data
    assert isinstance(polars_data["instance_mask"], pl.Series)

    # Create DataFrame and test from_polars
    df = pl.DataFrame(polars_data)
    reconstructed = cast("np.ndarray[Any, Any]", field.from_polars("instance_mask", 0, df, np.ndarray))

    assert isinstance(reconstructed, np.ndarray)
    assert np.array_equal(reconstructed, test_mask)


def test_instance_mask_callable_field_creation():
    """Test InstanceMaskCallableField creation and properties."""
    field = instance_mask_callable_field(dtype=pl.Boolean())

    assert isinstance(field, InstanceMaskCallableField)
    assert field.dtype == pl.Boolean
    assert field.semantic == "default"


def test_instance_mask_callable_field_polars_schema():
    """Test InstanceMaskCallableField Polars schema generation."""
    field = instance_mask_callable_field(dtype=pl.Boolean())
    schema = field.to_polars_schema("instance_mask_callable")

    expected = {
        "instance_mask_callable": pl.Object(),
    }
    assert schema == expected


def test_instance_mask_callable_field_polars_conversion():
    """Test InstanceMaskCallableField to/from Polars conversion."""
    field = cast(
        "InstanceMaskCallableField",
        instance_mask_callable_field(dtype=pl.Boolean()),
    )

    def get_instance_masks():
        # Return a (2,2,2) array of boolean masks
        return np.array([[[True, False], [False, True]], [[False, True], [True, False]]], dtype=bool)

    # Test to_polars
    polars_data = field.to_polars("instance_mask_callable", get_instance_masks)
    assert "instance_mask_callable" in polars_data
    assert callable(polars_data["instance_mask_callable"][0])

    # Create DataFrame and test from_polars
    df = pl.DataFrame(polars_data)
    reconstructed = field.from_polars("instance_mask_callable", 0, df, callable)

    assert callable(reconstructed)
    assert np.array_equal(reconstructed(), get_instance_masks())


def test_mask_callable_field_creation():
    """Test MaskCallableField creation and properties."""
    field = mask_callable_field(dtype=pl.UInt8())

    assert isinstance(field, MaskCallableField)
    assert field.dtype == pl.UInt8
    assert field.semantic == "default"


def test_mask_callable_field_polars_schema():
    """Test MaskCallableField Polars schema generation."""
    field = mask_callable_field(dtype=pl.UInt8())
    schema = field.to_polars_schema("mask_callable")

    expected = {
        "mask_callable": pl.Object(),
    }
    assert schema == expected


def test_mask_callable_field_polars_conversion():
    """Test MaskCallableField to/from Polars conversion."""
    field = cast(
        "MaskCallableField",
        mask_callable_field(dtype=pl.UInt8()),
    )

    def get_mask():
        # Return a (2,2) array of uint8 mask with category IDs
        return np.array([[1, 2], [2, 1]], dtype=np.uint8)

    # Test to_polars
    polars_data = field.to_polars("mask_callable", get_mask)
    assert "mask_callable" in polars_data
    assert callable(polars_data["mask_callable"][0])


def test_bbox_field_polars_conversion():
    """Test BBoxField to/from Polars conversion."""
    field = cast("BBoxField", bbox_field(dtype=pl.Float32(), normalize=False))
    test_bbox = np.array([[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]], dtype=np.float32)

    # Test to_polars
    polars_data = field.to_polars("bbox", test_bbox)
    assert "bbox" in polars_data
    assert isinstance(polars_data["bbox"], pl.Series)

    # Create DataFrame and test from_polars
    df = pl.DataFrame(polars_data)
    reconstructed = cast("np.ndarray[Any, Any]", field.from_polars("bbox", 0, df, np.ndarray))

    assert isinstance(reconstructed, np.ndarray)
    assert np.allclose(reconstructed, test_bbox)


def test_bbox_field_tv_tensors_bounding_boxes():
    """Test BBoxField with tv_tensors.BoundingBoxes input and output."""
    torch = pytest.importorskip("torch")
    tv_tensors = pytest.importorskip("torchvision.tv_tensors")

    field = cast("BBoxField", bbox_field(dtype=pl.Float32(), format="x1y1x2y2"))

    # Create tv_tensors.BoundingBoxes
    boxes_data = torch.tensor([[10.0, 20.0, 50.0, 60.0], [30.0, 40.0, 80.0, 90.0]])
    canvas_size = (100, 100)  # (height, width)
    test_bboxes = tv_tensors.BoundingBoxes(
        boxes_data,
        format=tv_tensors.BoundingBoxFormat.XYXY,
        canvas_size=canvas_size,
    )

    # Test to_polars - should store both bbox data and canvas_size
    polars_data = field.to_polars("bbox", test_bboxes)
    assert "bbox" in polars_data
    assert "bbox_canvas_size" in polars_data
    assert isinstance(polars_data["bbox"], pl.Series)
    assert isinstance(polars_data["bbox_canvas_size"], pl.Series)

    # Verify canvas_size is stored correctly
    stored_canvas_size = polars_data["bbox_canvas_size"][0].to_list()
    assert stored_canvas_size == list(canvas_size)

    # Create DataFrame and test from_polars with tv_tensors.BoundingBoxes target type
    df = pl.DataFrame(polars_data)
    reconstructed = field.from_polars("bbox", 0, df, tv_tensors.BoundingBoxes)

    # Verify the reconstructed object is a tv_tensors.BoundingBoxes
    assert isinstance(reconstructed, tv_tensors.BoundingBoxes)
    assert reconstructed.format == tv_tensors.BoundingBoxFormat.XYXY
    assert reconstructed.canvas_size == canvas_size

    # Verify the bbox data matches
    assert torch.allclose(reconstructed, boxes_data)


def test_bbox_field_tv_tensors_to_numpy():
    """Test BBoxField with tv_tensors.BoundingBoxes input but numpy output."""
    torch = pytest.importorskip("torch")
    tv_tensors = pytest.importorskip("torchvision.tv_tensors")

    field = cast("BBoxField", bbox_field(dtype=pl.Float32(), format="x1y1x2y2"))

    # Create tv_tensors.BoundingBoxes
    boxes_data = torch.tensor([[10.0, 20.0, 50.0, 60.0]])
    test_bboxes = tv_tensors.BoundingBoxes(
        boxes_data,
        format=tv_tensors.BoundingBoxFormat.XYXY,
        canvas_size=(100, 100),
    )

    # Store as tv_tensors.BoundingBoxes
    polars_data = field.to_polars("bbox", test_bboxes)
    df = pl.DataFrame(polars_data)

    # Retrieve as numpy array (should work even though stored with canvas_size)
    reconstructed = field.from_polars("bbox", 0, df, np.ndarray)

    assert isinstance(reconstructed, np.ndarray)
    assert np.allclose(reconstructed, boxes_data.numpy())


def test_rotated_bbox_field_creation():
    """Test RotatedBBoxField creation and properties."""
    field = rotated_bbox_field(dtype=pl.Float32(), format="cxcywhr", normalize=True)

    assert isinstance(field, RotatedBBoxField)
    assert field.dtype == pl.Float32
    assert field.format == "cxcywhr"
    assert field.normalize is True
    assert field.semantic == "default"


def test_rotated_bbox_field_creation_defaults():
    """Test RotatedBBoxField creation with default values."""
    field = rotated_bbox_field(dtype=pl.Float32())

    assert isinstance(field, RotatedBBoxField)
    assert field.dtype == pl.Float32
    assert field.format == "cxcywhr"  # Default format
    assert field.normalize is False  # Default normalization
    assert field.semantic == "default"  # Default semantic


def test_rotated_bbox_field_polars_schema():
    """Test RotatedBBoxField Polars schema generation."""
    field = rotated_bbox_field(dtype=pl.Float32())
    schema = field.to_polars_schema("rotated_bbox")

    expected = {"rotated_bbox": pl.List(pl.Array(pl.Float32, 5))}
    assert schema == expected


def test_rotated_bbox_field_polars_conversion():
    """Test RotatedBBoxField to/from Polars conversion."""
    field = cast("RotatedBBoxField", rotated_bbox_field(dtype=pl.Float32(), normalize=False))
    # Test with rotated bboxes: [cx, cy, w, h, r]
    test_rotated_bbox = np.array([[50.0, 60.0, 30.0, 20.0, 0.785], [100.0, 120.0, 40.0, 25.0, 1.57]], dtype=np.float32)

    # Test to_polars
    polars_data = field.to_polars("rotated_bbox", test_rotated_bbox)
    assert "rotated_bbox" in polars_data
    assert isinstance(polars_data["rotated_bbox"], pl.Series)

    # Create DataFrame and test from_polars
    df = pl.DataFrame(polars_data)
    reconstructed = cast("np.ndarray[Any, Any]", field.from_polars("rotated_bbox", 0, df, np.ndarray))

    assert isinstance(reconstructed, np.ndarray)
    assert np.allclose(reconstructed, test_rotated_bbox)


def test_image_info_creation():
    """Test ImageInfo creation."""
    info = ImageInfo(width=640, height=480)

    assert info.width == 640
    assert info.height == 480


def test_image_info_field_creation():
    """Test ImageInfoField creation."""
    field = image_info_field(semantic="bbox")

    assert isinstance(field, ImageInfoField)
    assert field.semantic == "bbox"


def test_image_info_field_polars_schema():
    """Test ImageInfoField Polars schema generation."""
    field = image_info_field()
    schema = field.to_polars_schema("image_info")

    expected = {
        "image_info": pl.Struct(
            [
                pl.Field("width", pl.Int32()),
                pl.Field("height", pl.Int32()),
            ]
        )
    }
    assert schema == expected


def test_image_info_field_polars_conversion():
    """Test ImageInfoField to/from Polars conversion."""
    field = image_info_field()
    test_info = ImageInfo(width=640, height=480)

    # Test to_polars
    polars_data = field.to_polars("image_info", test_info)
    assert "image_info" in polars_data
    assert isinstance(polars_data["image_info"], pl.Series)

    # Create DataFrame and test from_polars
    df = pl.DataFrame(polars_data)
    reconstructed = field.from_polars("image_info", 0, df, ImageInfo)

    assert isinstance(reconstructed, ImageInfo)
    assert reconstructed.width == 640
    assert reconstructed.height == 480


def test_image_path_field_creation():
    """Test ImagePathField creation."""
    field = image_path_field(semantic="default")

    assert isinstance(field, ImagePathField)
    assert field.semantic == "default"


def test_image_path_field_polars_schema():
    """Test ImagePathField Polars schema generation."""
    field = image_path_field()
    schema = field.to_polars_schema("image_path")

    expected = {"image_path": pl.String()}
    assert schema == expected


def test_image_path_field_polars_conversion():
    """Test ImagePathField to/from Polars conversion."""
    field = image_path_field()
    test_path = "/path/to/image.jpg"

    # Test to_polars
    polars_data = field.to_polars("image_path", test_path)
    assert "image_path" in polars_data
    assert isinstance(polars_data["image_path"], pl.Series)

    # Create DataFrame and test from_polars
    df = pl.DataFrame(polars_data)
    reconstructed = field.from_polars("image_path", 0, df, str)

    assert isinstance(reconstructed, str)
    assert reconstructed == test_path


def test_image_callable_field_creation():
    """Test ImageCallableField creation and properties."""
    field = image_callable_field(format="RGB", semantic="default")

    assert isinstance(field, ImageCallableField)
    assert field.format == "RGB"
    assert field.semantic == "default"

    # Test with different format
    field_bgr = image_callable_field(format="BGR", semantic="bbox")
    assert field_bgr.format == "BGR"
    assert field_bgr.semantic == "bbox"


def test_image_callable_field_polars_schema():
    """Test ImageCallableField Polars schema generation."""
    field = image_callable_field()
    schema = field.to_polars_schema("image_callable")

    expected = {"image_callable": pl.Object}
    assert schema == expected


def test_image_callable_field_polars_conversion():
    """Test ImageCallableField to/from Polars conversion."""
    import numpy as np

    field = image_callable_field()  # Create a test callable

    def test_image_generator():
        return np.array([[[255, 0, 0], [0, 255, 0]], [[0, 0, 255], [255, 255, 0]]], dtype=np.uint8)

    # Test to_polars
    polars_data = field.to_polars("image_callable", test_image_generator)
    assert "image_callable" in polars_data
    assert isinstance(polars_data["image_callable"], pl.Series)

    # Create DataFrame and test from_polars
    df = pl.DataFrame(polars_data)
    reconstructed = field.from_polars("image_callable", 0, df, callable)

    assert callable(reconstructed)
    assert reconstructed == test_image_generator

    # Test that the callable produces the expected output
    result = reconstructed()
    assert isinstance(result, np.ndarray)
    assert result.shape == (2, 2, 3)
    assert result.dtype == np.uint8


def test_image_callable_field_error_handling():
    """Test ImageCallableField error handling."""
    field = image_callable_field()

    # Test with non-callable object
    with pytest.raises(TypeError, match="Expected callable"):
        field.to_polars("image_callable", "not_a_callable")

    # Test with non-callable in from_polars
    df = pl.DataFrame({"image_callable": ["not_a_callable"]})
    with pytest.raises(TypeError, match="Expected callable in column"):
        field.from_polars("image_callable", 0, df, callable)


def test_image_callable_field_complex_callable():
    """Test ImageCallableField with more complex callables."""
    import numpy as np

    field = image_callable_field(format="RGBA")  # Test with lambda
    lambda_callable = lambda: np.zeros((5, 5, 4), dtype=np.uint8)  # noqa: E731

    polars_data = field.to_polars("image_callable", lambda_callable)
    df = pl.DataFrame(polars_data)
    reconstructed = field.from_polars("image_callable", 0, df, callable)

    result = reconstructed()
    assert result.shape == (5, 5, 4)
    assert result.dtype == np.uint8
    assert np.all(result == 0)

    # Test with class method
    class ImageGenerator:
        def __init__(self, size):
            self.size = size

        def generate(self):
            return np.ones((self.size, self.size, 3), dtype=np.uint8) * 128

    generator = ImageGenerator(3)
    polars_data2 = field.to_polars("image_callable", generator.generate)
    df2 = pl.DataFrame(polars_data2)
    reconstructed2 = field.from_polars("image_callable", 0, df2, callable)

    result2 = reconstructed2()
    assert result2.shape == (3, 3, 3)
    assert np.all(result2 == 128)


def test_attribute_info_creation():
    """Test AttributeInfo creation."""
    field = tensor_field(dtype=pl.Float32())
    attr_info = AttributeInfo(type=np.ndarray, field=field)

    assert attr_info.type == np.ndarray
    assert attr_info.field == field


def test_schema_creation():
    """Test Schema creation."""
    attributes = {
        "image": AttributeInfo(type=np.ndarray, field=image_field(dtype=pl.UInt8(), format="RGB")),
        "bbox": AttributeInfo(type=np.ndarray, field=bbox_field(dtype=pl.Float32(), normalize=False)),
    }

    schema = Schema(attributes=attributes)

    assert len(schema.attributes) == 2
    assert "image" in schema.attributes
    assert "bbox" in schema.attributes
    assert schema.attributes["image"].type == np.ndarray
    assert schema.attributes["bbox"].type == np.ndarray


def test_field_equality():
    """Test field equality comparison."""
    field1 = tensor_field(dtype=pl.Float32())
    field2 = tensor_field(dtype=pl.Float32())
    field3 = tensor_field(dtype=pl.Int32())

    # Same configuration should be equal
    assert field1 == field2

    # Different dtype should not be equal
    assert field1 != field3


def test_field_semantic_variations():
    """Test fields with different semantic values."""
    left_field = image_field(dtype=pl.UInt8(), format="RGB", semantic="left")
    right_field = image_field(dtype=pl.UInt8(), format="RGB", semantic="right")
    default_field = image_field(dtype=pl.UInt8(), format="RGB")

    assert left_field != right_field
    assert left_field != default_field
    assert right_field != default_field

    assert left_field.semantic == "left"
    assert right_field.semantic == "right"
    assert default_field.semantic == "default"


def test_schema_duplicate_field_type_assertion():
    """Test that schema creation fails with assertion when two fields have the same field type."""

    # This should fail because we have two ImageFields with the same semantic context
    with pytest.raises(ValueError):

        class InvalidSample(Sample):
            image1: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="RGB")
            image2: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="RGB")

        # This should trigger the assertion error when schema is inferred
        InvalidSample.infer_schema()

    # This should work because the fields have different semantic contexts
    class ValidSample(Sample):
        left_image: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="RGB", semantic="left")
        right_image: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="RGB", semantic="right")

    # This should not raise an assertion error
    schema = ValidSample.infer_schema()
    assert len(schema.attributes) == 2
    assert "left_image" in schema.attributes
    assert "right_image" in schema.attributes


def test_polygon_field_creation():
    """Test PolygonField creation and properties."""
    field = polygon_field(dtype=pl.Float32(), format="xy", normalize=True)

    assert isinstance(field, PolygonField)
    assert field.dtype == pl.Float32
    assert field.format == "xy"
    assert field.normalize is True
    assert field.semantic == "default"


def test_polygon_field_creation_defaults():
    """Test PolygonField creation with default values."""
    field = polygon_field(dtype=pl.Float32())

    assert isinstance(field, PolygonField)
    assert field.dtype == pl.Float32
    assert field.format == "xy"  # Default format
    assert field.normalize is False  # Default normalization
    assert field.semantic == "default"  # Default semantic


def test_polygon_field_polars_schema():
    """Test PolygonField Polars schema generation."""
    field = polygon_field(dtype=pl.Float32())
    schema = field.to_polars_schema("polygon")

    expected = {"polygon": pl.List(pl.List(pl.Array(pl.Float32, 2)))}
    assert schema == expected


def test_polygon_field_polars_conversion():
    """Test PolygonField to/from Polars conversion with simple polygon."""
    field = cast("PolygonField", polygon_field(dtype=pl.Float32(), normalize=False))
    # Triangle: (0,0) -> (10,0) -> (5,10) -> (0,0)
    test_polygon_1 = np.array([[0.0, 0.0], [10.0, 0.0], [5.0, 10.0]], dtype=np.float32)
    test_polygon_2 = np.array([[2.0, 2.0], [10.0, 2.0], [5.0, 10.0], [6.0, 11.0]], dtype=np.float32)
    polygons = np.array([test_polygon_1, test_polygon_2], dtype=object)

    # Test to_polars
    polars_data = field.to_polars("polygon", polygons)
    assert "polygon" in polars_data
    assert isinstance(polars_data["polygon"], pl.Series)

    # Create DataFrame and test from_polars
    df = pl.DataFrame(polars_data)
    reconstructed = cast("np.ndarray[Any, Any]", field.from_polars("polygon", 0, df, np.ndarray))

    assert len(reconstructed) == 2
    assert np.all(reconstructed[0] == test_polygon_1)
    assert np.all(reconstructed[1] == test_polygon_2)


# ==================== Serialization Tests ====================


def test_tensor_field_serialization():
    """Test TensorField to_dict/from_dict serialization."""
    field = TensorField(dtype=pl.Float32(), semantic="bbox")

    # Serialize to dict
    field_dict = field.to_dict()
    assert field_dict["type"] == "TensorField"
    assert field_dict["semantic"] == "bbox"
    assert "Float32" in str(field_dict["dtype"])

    # Deserialize from dict
    from getidata.schema import Field

    reconstructed = Field.from_dict(field_dict)
    assert isinstance(reconstructed, TensorField)

    # Compare with original
    assert reconstructed.semantic == field.semantic
    assert str(reconstructed.dtype) == str(field.dtype)


def test_image_field_serialization():
    """Test ImageField to_dict/from_dict serialization."""
    field = image_field(dtype=pl.UInt8(), format="RGB", semantic="right")

    # Serialize to dict
    field_dict = field.to_dict()
    assert field_dict["type"] == "ImageField"
    assert field_dict["semantic"] == "right"
    assert field_dict["format"] == "RGB"
    assert "UInt8" in str(field_dict["dtype"])

    # Deserialize from dict
    from getidata.schema import Field

    reconstructed = Field.from_dict(field_dict)
    assert isinstance(reconstructed, ImageField)

    # Compare with original
    assert reconstructed.semantic == field.semantic
    assert reconstructed.format == field.format
    assert str(reconstructed.dtype) == str(field.dtype)


def test_bbox_field_serialization():
    """Test BBoxField to_dict/from_dict serialization."""
    field = bbox_field(dtype=pl.Float32(), format="xywh", normalize=True)

    # Serialize to dict
    field_dict = field.to_dict()
    assert field_dict["type"] == "BBoxField"
    assert field_dict["semantic"] == "default"
    assert field_dict["format"] == "xywh"
    assert field_dict["normalize"] is True

    # Deserialize from dict
    from getidata.schema import Field

    reconstructed = Field.from_dict(field_dict)
    assert isinstance(reconstructed, BBoxField)

    # Compare with original
    assert reconstructed.format == field.format
    assert reconstructed.normalize == field.normalize
    assert reconstructed.semantic == field.semantic
    assert str(reconstructed.dtype) == str(field.dtype)


def test_rotated_bbox_field_serialization():
    """Test RotatedBBoxField to_dict/from_dict serialization."""
    field = rotated_bbox_field(dtype=pl.Float32(), format="xywha")

    # Serialize to dict
    field_dict = field.to_dict()
    assert field_dict["type"] == "RotatedBBoxField"
    assert field_dict["format"] == "xywha"

    # Deserialize from dict
    from getidata.schema import Field

    reconstructed = Field.from_dict(field_dict)
    assert isinstance(reconstructed, RotatedBBoxField)

    # Compare with original
    assert reconstructed.format == field.format
    assert reconstructed.semantic == field.semantic
    assert str(reconstructed.dtype) == str(field.dtype)


def test_polygon_field_serialization():
    """Test PolygonField to_dict/from_dict serialization."""
    field = polygon_field(dtype=pl.Float64(), format="xy", normalize=True)

    # Serialize to dict
    field_dict = field.to_dict()
    assert field_dict["type"] == "PolygonField"
    assert field_dict["format"] == "xy"
    assert field_dict["normalize"] is True

    # Deserialize from dict
    from getidata.schema import Field

    reconstructed = Field.from_dict(field_dict)
    assert isinstance(reconstructed, PolygonField)

    # Compare with original
    assert reconstructed.format == field.format
    assert reconstructed.normalize == field.normalize
    assert reconstructed.semantic == field.semantic
    assert str(reconstructed.dtype) == str(field.dtype)


def test_mask_field_serialization():
    """Test MaskField to_dict/from_dict serialization."""
    field = mask_field(dtype=pl.UInt8())

    # Serialize to dict
    field_dict = field.to_dict()
    assert field_dict["type"] == "MaskField"
    assert "UInt8" in str(field_dict["dtype"])

    # Deserialize from dict
    from getidata.schema import Field

    reconstructed = Field.from_dict(field_dict)
    assert isinstance(reconstructed, MaskField)

    # Compare with original
    assert reconstructed.semantic == field.semantic
    assert str(reconstructed.dtype) == str(field.dtype)


def test_instance_mask_field_serialization():
    """Test InstanceMaskField to_dict/from_dict serialization."""
    field = instance_mask_field(dtype=pl.Boolean(), semantic="anomaly")

    # Serialize to dict
    field_dict = field.to_dict()
    assert field_dict["type"] == "InstanceMaskField"
    assert field_dict["semantic"] == "anomaly"

    # Deserialize from dict
    from getidata.schema import Field

    reconstructed = Field.from_dict(field_dict)
    assert isinstance(reconstructed, InstanceMaskField)

    # Compare with original
    assert reconstructed.semantic == field.semantic
    assert str(reconstructed.dtype) == str(field.dtype)


def test_image_path_field_serialization():
    """Test ImagePathField to_dict/from_dict serialization."""
    field = image_path_field(semantic="bbox")

    # Serialize to dict
    field_dict = field.to_dict()
    assert field_dict["type"] == "ImagePathField"
    assert field_dict["semantic"] == "bbox"

    # Deserialize from dict
    from getidata.schema import Field

    reconstructed = Field.from_dict(field_dict)
    assert isinstance(reconstructed, ImagePathField)

    # Compare with original
    assert reconstructed.semantic == field.semantic


def test_image_bytes_field_serialization():
    """Test ImageBytesField to_dict/from_dict serialization."""
    field = image_bytes_field(semantic="polygon")

    # Serialize to dict
    field_dict = field.to_dict()
    assert field_dict["type"] == "ImageBytesField"
    assert field_dict["semantic"] == "polygon"

    # Deserialize from dict
    from getidata.schema import Field

    reconstructed = Field.from_dict(field_dict)
    assert isinstance(reconstructed, ImageBytesField)

    # Compare with original
    assert reconstructed.semantic == field.semantic


def test_image_info_field_serialization():
    """Test ImageInfoField to_dict/from_dict serialization."""
    field = image_info_field(semantic="default")

    # Serialize to dict
    field_dict = field.to_dict()
    assert field_dict["type"] == "ImageInfoField"
    assert field_dict["semantic"] == "default"

    # Deserialize from dict
    from getidata.schema import Field

    reconstructed = Field.from_dict(field_dict)
    assert isinstance(reconstructed, ImageInfoField)

    # Compare with original
    assert reconstructed.semantic == field.semantic


def test_schema_serialization_simple():
    """Test Schema to_dict/from_dict with simple attributes."""
    from getidata.schema import AttributeInfo, Schema

    # Create a simple schema
    schema = Schema(
        attributes={
            "image": AttributeInfo(type=np.ndarray, field=image_field(dtype=pl.UInt8())),
            "bbox": AttributeInfo(type=np.ndarray, field=bbox_field(dtype=pl.Float32())),
        }
    )

    # Serialize to dict
    schema_dict = schema.to_dict()
    assert "attributes" in schema_dict
    assert "categories" in schema_dict
    assert "image" in schema_dict["attributes"]
    assert "bbox" in schema_dict["attributes"]
    assert schema_dict["attributes"]["image"]["field"]["type"] == "ImageField"
    assert schema_dict["attributes"]["bbox"]["field"]["type"] == "BBoxField"

    # Deserialize from dict
    reconstructed = Schema.from_dict(schema_dict)
    assert isinstance(reconstructed, Schema)

    # Compare with original
    assert set(reconstructed.attributes.keys()) == set(schema.attributes.keys())
    assert isinstance(reconstructed.attributes["image"].field, ImageField)
    assert isinstance(reconstructed.attributes["bbox"].field, BBoxField)
    assert type(reconstructed.attributes["image"].type) is type(schema.attributes["image"].type)
    assert type(reconstructed.attributes["bbox"].type) is type(schema.attributes["bbox"].type)


def test_schema_serialization_with_categories():
    """Test Schema to_dict/from_dict with categories."""
    from getidata.categories import LabelCategories
    from getidata.schema import AttributeInfo, Schema

    # Create schema with categories
    label_cats = LabelCategories(labels=("cat", "dog", "bird"))
    schema = Schema(
        attributes={"label": AttributeInfo(type=str, field=tensor_field(dtype=pl.Int32()), categories=label_cats)}
    )

    # Serialize to dict
    schema_dict = schema.to_dict()
    assert "label" in schema_dict["attributes"]
    assert "label" in schema_dict["categories"]
    assert schema_dict["categories"]["label"]["type"] == "LabelCategories"
    assert schema_dict["categories"]["label"]["labels"] == ["cat", "dog", "bird"]

    # Deserialize from dict
    reconstructed = Schema.from_dict(schema_dict)

    # Compare with original
    assert "label" in reconstructed.attributes
    assert reconstructed.attributes["label"].categories is not None
    assert isinstance(reconstructed.attributes["label"].categories, LabelCategories)
    assert reconstructed.attributes["label"].categories.labels == schema.attributes["label"].categories.labels
    assert reconstructed.attributes["label"].categories.labels == ("cat", "dog", "bird")


def test_schema_serialization_builtin_types():
    """Test Schema serialization handles built-in Python types correctly."""
    from getidata.schema import AttributeInfo, Schema

    # Create schema with built-in Python types and different semantics to avoid conflicts
    schema = Schema(
        attributes={
            "score": AttributeInfo(type=float, field=tensor_field(dtype=pl.Float32())),
            "count": AttributeInfo(type=int, field=tensor_field(dtype=pl.Int32(), semantic="left")),
            "name": AttributeInfo(type=str, field=tensor_field(dtype=pl.Utf8(), semantic="right")),
        }
    )

    # Serialize and deserialize
    schema_dict = schema.to_dict()
    reconstructed = Schema.from_dict(schema_dict)

    # Compare with original
    assert set(reconstructed.attributes.keys()) == set(schema.attributes.keys())
    assert "score" in reconstructed.attributes
    assert "count" in reconstructed.attributes
    assert "name" in reconstructed.attributes
    # Verify semantics are preserved
    assert reconstructed.attributes["score"].field.semantic == schema.attributes["score"].field.semantic
    assert reconstructed.attributes["count"].field.semantic == schema.attributes["count"].field.semantic
    assert reconstructed.attributes["name"].field.semantic == schema.attributes["name"].field.semantic


def test_schema_with_categories_method():
    """Test Schema.with_categories method with serialization."""
    from getidata.categories import LabelCategories
    from getidata.schema import AttributeInfo, Schema

    # Create base schema without categories (use different semantics to avoid conflicts)
    schema = Schema(
        attributes={
            "label": AttributeInfo(type=str, field=tensor_field(dtype=pl.Int32())),
            "mask": AttributeInfo(type=np.ndarray, field=mask_field(dtype=pl.UInt8(), semantic="left")),
        }
    )

    # Add categories
    label_cats = LabelCategories(labels=("cat", "dog"))
    schema_with_cats = schema.with_categories({"label": label_cats})

    # Serialize and deserialize
    schema_dict = schema_with_cats.to_dict()
    reconstructed = Schema.from_dict(schema_dict)

    # Compare with original
    assert reconstructed.attributes["label"].categories is not None
    assert isinstance(reconstructed.attributes["label"].categories, LabelCategories)
    assert reconstructed.attributes["label"].categories.labels == schema_with_cats.attributes["label"].categories.labels
    assert reconstructed.attributes["label"].categories.labels == ("cat", "dog")
    assert reconstructed.attributes["mask"].categories is None


def test_subset_field_to_polars_with_none():
    """Test SubsetField conversion to Polars with None value."""
    field = subset_field()
    result = field.to_polars("subset", None)

    assert "subset" in result
    assert result["subset"][0] is None


def test_subset_field_from_polars_with_direct_enum_type():
    """Test SubsetField reconstruction from Polars with direct Subset type."""
    field = subset_field()

    # Create a DataFrame with subset values
    df = pl.DataFrame({"subset": pl.Series(["TRAINING", "TESTING", "VALIDATION"], dtype=pl.Categorical())})

    # Test reconstruction with direct Subset type
    value1 = field.from_polars("subset", 0, df, Subset)
    assert value1 == Subset.TRAINING
    assert isinstance(value1, Subset)

    value2 = field.from_polars("subset", 1, df, Subset)
    assert value2 == Subset.TESTING

    value3 = field.from_polars("subset", 2, df, Subset)
    assert value3 == Subset.VALIDATION


def test_subset_field_roundtrip():
    """Test SubsetField roundtrip conversion (to_polars -> from_polars)."""
    from typing import Union

    field = subset_field()

    # Test with TRAINING
    polars_data = field.to_polars("subset", Subset.TRAINING)
    df = pl.DataFrame(polars_data)
    reconstructed = field.from_polars("subset", 0, df, Union[Subset, None])
    assert reconstructed == Subset.TRAINING

    # Test with TESTING
    polars_data = field.to_polars("subset", Subset.TESTING)
    df = pl.DataFrame(polars_data)
    reconstructed = field.from_polars("subset", 0, df, Union[Subset, None])
    assert reconstructed == Subset.TESTING

    # Test with None
    polars_data = field.to_polars("subset", None)
    df = pl.DataFrame(polars_data)
    reconstructed = field.from_polars("subset", 0, df, Union[Subset, None])
    assert reconstructed is None


def test_schema_serialization_union_types():
    """Test Schema to_dict/from_dict correctly handles Union types (e.g., np.ndarray | None)."""
    schema = Schema(
        attributes={
            "bboxes": AttributeInfo(type=np.ndarray | None, field=bbox_field(dtype=pl.Float32())),
            "image": AttributeInfo(type=np.ndarray, field=image_field(dtype=pl.UInt8())),
        }
    )

    schema_dict = schema.to_dict()

    # Union type should be serialized with __union__ marker and list of component types
    bbox_attr = schema_dict["attributes"]["bboxes"]
    assert bbox_attr["type_module"] == "__union__"
    assert isinstance(bbox_attr["type"], list)
    assert len(bbox_attr["type"]) == 2
    type_names = {comp["name"] for comp in bbox_attr["type"]}
    assert "ndarray" in type_names
    assert "NoneType" in type_names

    # Non-union type should be serialized normally
    image_attr = schema_dict["attributes"]["image"]
    assert image_attr["type"] == "ndarray"
    assert image_attr["type_module"] == "numpy"

    # Deserialize and verify round-trip
    reconstructed = Schema.from_dict(schema_dict)
    assert set(reconstructed.attributes.keys()) == {"bboxes", "image"}

    # The reconstructed union type should work with isinstance-style checks
    import types as _types

    bbox_type = reconstructed.attributes["bboxes"].type
    assert isinstance(bbox_type, _types.UnionType)
    assert type(None) in bbox_type.__args__
    assert np.ndarray in bbox_type.__args__

    # Non-union type should be reconstructed correctly
    assert reconstructed.attributes["image"].type is np.ndarray


def test_schema_serialization_union_builtin_types():
    """Test Schema serialization of Union types with builtin components (e.g., int | None)."""
    schema = Schema(
        attributes={
            "score": AttributeInfo(type=int | None, field=tensor_field(dtype=pl.Int32())),
        }
    )

    schema_dict = schema.to_dict()
    reconstructed = Schema.from_dict(schema_dict)

    import types as _types

    score_type = reconstructed.attributes["score"].type
    assert isinstance(score_type, _types.UnionType)
    assert int in score_type.__args__
    assert type(None) in score_type.__args__


def test_resolve_type_helper():
    """Test _resolve_type helper function."""
    from getidata.schema import _resolve_type

    assert _resolve_type("int", "builtins") is int
    assert _resolve_type("NoneType", None) is type(None)
    assert _resolve_type("ndarray", "numpy") is np.ndarray
    assert _resolve_type("nonexistent", "numpy") is object
    assert _resolve_type("ndarray", "nonexistent_module") is object


def test_resolve_type_from_qualified_name_helper():
    """Test _resolve_type_from_qualified_name helper function."""
    from getidata.schema import _resolve_type_from_qualified_name

    assert _resolve_type_from_qualified_name("numpy.ndarray") is np.ndarray
    assert _resolve_type_from_qualified_name("None") is type(None)
    assert _resolve_type_from_qualified_name("int") is int
    assert _resolve_type_from_qualified_name("  numpy.ndarray  ") is np.ndarray
    assert _resolve_type_from_qualified_name("nonexistent.module.Type") is object


def test_is_allowed_type_module():
    """Test that only trusted top-level packages are allowed for type resolution."""
    from getidata.schema import _is_allowed_type_module

    # Trusted packages, including submodules
    assert _is_allowed_type_module("numpy") is True
    assert _is_allowed_type_module("torch") is True
    assert _is_allowed_type_module("torchvision") is True
    assert _is_allowed_type_module("torchvision.tv_tensors._bounding_boxes") is True
    assert _is_allowed_type_module("getidata") is True
    assert _is_allowed_type_module("getidata.media") is True

    # Untrusted packages, including ones an attacker could pick for RCE
    assert _is_allowed_type_module("subprocess") is False
    assert _is_allowed_type_module("os") is False
    assert _is_allowed_type_module("builtins") is False
    assert _is_allowed_type_module("sys") is False
    # A prefix collision must not be enough to be trusted (e.g. "numpyfake")
    assert _is_allowed_type_module("numpyfake") is False
    assert _is_allowed_type_module("getidataevil") is False


def test_resolve_type_blocks_untrusted_modules():
    """Test that _resolve_type refuses to import modules outside the allowlist."""
    from getidata.schema import _resolve_type

    assert _resolve_type("getoutput", "subprocess") is object
    assert _resolve_type("Popen", "subprocess") is object
    assert _resolve_type("system", "os") is object
    assert _resolve_type("exit", "sys") is object


def test_resolve_type_blocks_non_type_attributes_in_allowed_modules():
    """Test that _resolve_type never returns a callable that isn't an actual class."""
    from getidata.schema import _resolve_type

    # numpy.array is a factory function, not a class - must not be returned as a "type"
    assert _resolve_type("array", "numpy") is object
    # image_field is a factory function in a trusted getidata module, not a class
    assert _resolve_type("image_field", "getidata.fields.images") is object


def test_resolve_type_from_qualified_name_blocks_untrusted_modules():
    """Test that _resolve_type_from_qualified_name refuses modules outside the allowlist."""
    from getidata.schema import _resolve_type_from_qualified_name

    assert _resolve_type_from_qualified_name("subprocess.getoutput") is object
    assert _resolve_type_from_qualified_name("os.system") is object


def test_schema_from_dict_regression_arbitrary_code_execution():
    """Regression test for GHSA/security report: a malicious schema selecting
    subprocess.getoutput as an image-path "type" must not resolve to a callable
    that gets invoked on the path value.
    """
    field = image_path_field()

    # Simulate the exact payload reported: only type/type_module are attacker-controlled.
    malicious_schema_dict = {
        "attributes": {
            "image": {
                "type": "getoutput",
                "type_module": "subprocess",
                "field": field.to_dict(),
            }
        },
        "categories": {},
    }

    schema = Schema.from_dict(malicious_schema_dict)

    # The dangerous callable must never be returned as the resolved type.
    resolved_type = schema.attributes["image"].type
    assert resolved_type is object

    # Simulate the sink: Field.from_polars is called with the resolved type as target_type.
    polars_data = field.to_polars("image", "; touch /tmp/getidata_rce_regression_test ;")
    df = pl.DataFrame(polars_data)

    # Must fail safely (TypeError from calling object() with an argument) instead of
    # executing the attacker-controlled shell command.
    with pytest.raises(TypeError):
        field.from_polars("image", 0, df, resolved_type)

    import os

    assert not os.path.exists("/tmp/getidata_rce_regression_test")


def test_schema_from_dict_still_resolves_legitimate_image_path_type():
    """Test that legitimate LazyImage-typed schemas still resolve correctly after the fix."""
    from getidata.media import LazyImage

    field = image_path_field()
    legit_schema_dict = {
        "attributes": {
            "image": {
                "type": "LazyImage",
                "type_module": "getidata.media",
                "field": field.to_dict(),
            }
        },
        "categories": {},
    }

    schema = Schema.from_dict(legit_schema_dict)
    resolved_type = schema.attributes["image"].type
    assert resolved_type is LazyImage

    polars_data = field.to_polars("image", "/tmp/some_image.jpg")
    df = pl.DataFrame(polars_data)
    result = field.from_polars("image", 0, df, resolved_type)
    assert isinstance(result, LazyImage)
    assert result.path == "/tmp/some_image.jpg"


def test_schema_serialization_torch_tensor_type():
    """Test that torch.Tensor attribute types round-trip through Schema to_dict/from_dict."""
    torch = pytest.importorskip("torch")

    schema = Schema(attributes={"data": AttributeInfo(type=torch.Tensor, field=tensor_field(dtype=pl.Float32()))})

    schema_dict = schema.to_dict()
    assert schema_dict["attributes"]["data"]["type"] == "Tensor"
    assert schema_dict["attributes"]["data"]["type_module"] == "torch"

    reconstructed = Schema.from_dict(schema_dict)
    assert reconstructed.attributes["data"].type is torch.Tensor


def test_subset_field_in_sample_with_union_type():
    """Test SubsetField usage in a Sample class with union type annotation."""

    class TestSample(Sample):
        image: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="RGB")
        subset: Subset | None = subset_field()

    # Test with TRAINING subset
    sample1 = TestSample(image=np.array([[[255, 0, 0]]], dtype=np.uint8), subset=Subset.TRAINING)
    assert sample1.subset == Subset.TRAINING

    # Test with None subset
    sample2 = TestSample(image=np.array([[[0, 255, 0]]], dtype=np.uint8), subset=None)
    assert sample2.subset is None

    # Test schema inference
    schema = TestSample.infer_schema()
    assert "subset" in schema.attributes
    assert isinstance(schema.attributes["subset"].field, SubsetField)
