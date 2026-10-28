# Schema Conversion & Converters

## Automatic Conversion

One of the most powerful features is automatic schema conversion. The system uses an A\* search algorithm to find the optimal conversion path between two schemas. You define the source and target as `Sample` classes, and the converter system figures out how to get there.

### End-to-end example

```python
import numpy as np
import polars as pl
from getidata import Dataset, Sample
from getidata.fields import ImageInfo, bbox_field, image_field, image_info_field, label_field

# Source schema: RGB UInt8 images with x1y1x2y2 bounding boxes
class SourceSample(Sample):
    image: np.ndarray = image_field(dtype=pl.UInt8(), format="RGB")
    bboxes: np.ndarray = bbox_field(dtype=pl.Float32(), format="x1y1x2y2")
    labels: np.ndarray = label_field(dtype=pl.UInt8(), is_list=True)
    image_info: ImageInfo = image_info_field()

# Target schema: BGR Float32 images with xywh bounding boxes
class TargetSample(Sample):
    image: np.ndarray = image_field(dtype=pl.Float32(), format="BGR")
    bboxes: np.ndarray = bbox_field(dtype=pl.Float32(), format="xywh")
    labels: np.ndarray = label_field(dtype=pl.UInt8(), is_list=True)
    image_info: ImageInfo = image_info_field()

# Build a source dataset
source_dataset = Dataset(SourceSample)
source_dataset.append(SourceSample(
    image=np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8),
    bboxes=np.array([[10, 20, 50, 80]], dtype=np.float32),
    labels=np.array([0], dtype=np.uint8),
    image_info=ImageInfo(width=100, height=100),
))

# Convert — the system automatically chains:
#   RGB -> BGR, UInt8 -> Float32, x1y1x2y2 -> xywh
target_dataset = source_dataset.convert_to_schema(TargetSample)

sample = target_dataset[0]
print(sample.image.dtype)   # float32
print(sample.bboxes)        # [[10, 20, 40, 60]] (xywh format)
```

You can also convert a single sample:

```python
from getidata.dataset import convert_sample_to_schema
converted_sample = convert_sample_to_schema(
    sample=source_sample,
    source_schema=SourceSample.infer_schema(),
    target_dtype_or_schema=TargetSample,
)
```

## How Converters Work

Converters are classes that transform data between field representations:

1. **Input/Output Specifications**: Each converter declares what field types it consumes and produces
2. **Filter Method**: Determines if the converter applies to specific field configurations
3. **Convert Method**: Performs the actual data transformation on a Polars DataFrame

```python
from getidata.converters import Converter, converter
from getidata.schema import AttributeSpec
@converter  # Registers the converter automatically
class MyConverter(Converter):
    # Declare input and output field types
    input_image: AttributeSpec[ImageField]
    output_image: AttributeSpec[ImageField]
    def filter_output_spec(self) -> bool:
        """Return True if this converter can handle the input/output combination."""
        return (
            self.input_image.field.format == "RGB" and
            self.output_image.field.format == "BGR"
        )
    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """Perform the conversion."""
        # Swap R and B channels
        # ... implementation
        return df
```

## Registering Custom Converters

Use the `@converter` decorator to register your converter:

```python
from getidata import converter, Converter
@converter
class CustomConverter(Converter):
    # ... implementation
```

Or register manually:

```python
from getidata import ConverterRegistry
ConverterRegistry.add_converter(CustomConverter)
```

## Built-in Converters

The module includes many pre-registered converters:

### Image Converters

| Converter                       | Description                               |
| ------------------------------- | ----------------------------------------- |
| `RedBlueColorConverter`         | RGB / BGR color format conversion         |
| `ImageDtypeConverter`           | Image dtype conversion with normalization |
| `ChannelsFirstConverter`        | HWC / CHW channel order conversion        |
| `ImagePathToImageConverter`     | Load image from path                      |
| `ImageCallableToImageConverter` | Execute lazy image loader                 |
| `ImageBytesToImageConverter`    | Decode image from bytes                   |
| `ImageToImageInfo`              | Extract image metadata                    |

### Bounding Box Converters

| Converter                 | Description                                   |
| ------------------------- | --------------------------------------------- |
| `BBoxCoordinateConverter` | Bbox format conversion (xywh, x1y1x2y2, etc.) |
| `BBoxDtypeConverter`      | Bbox dtype conversion                         |
| `BBoxFormatConverter`     | Bbox format metadata conversion               |
| `BBoxToPolygonConverter`  | Convert bboxes to polygons                    |

### Rotated Bounding Box Converters

| Converter                        | Description                               |
| -------------------------------- | ----------------------------------------- |
| `RotatedBBoxCoordinateConverter` | Rotated bbox format conversion            |
| `RotatedBBoxDtypeConverter`      | Rotated bbox dtype conversion             |
| `RotatedBBoxToBBoxConverter`     | Convert rotated bbox to axis-aligned bbox |
| `RotatedBBoxToPolygonConverter`  | Convert rotated bbox to polygon           |

### Polygon Converters

| Converter                        | Description                   |
| -------------------------------- | ----------------------------- |
| `PolygonCoordinateConverter`     | Polygon coordinate conversion |
| `PolygonDtypeConverter`          | Polygon dtype conversion      |
| `PolygonToBBoxConverter`         | Generate bboxes from polygons |
| `PolygonToMaskConverter`         | Rasterize polygons to masks   |
| `PolygonToInstanceMaskConverter` | Rasterize to instance masks   |

### Other Annotation Converters

| Converter                      | Description                                                    |
| ------------------------------ | -------------------------------------------------------------- |
| `EllipseCoordinateConverter`   | Ellipse coordinate conversion                                  |
| `EllipseDtypeConverter`        | Ellipse dtype conversion                                       |
| `EllipseToBBoxConverter`       | Convert ellipses to bboxes                                     |
| `KeypointsCoordinateConverter` | Keypoints coordinate conversion                                |
| `KeypointsDtypeConverter`      | Keypoints dtype conversion                                     |
| `KeypointsToBBoxConverter`     | Generate bboxes from keypoints                                 |
| `LabelDtypeConverter`          | Label dtype conversion                                         |
| `LabelShapeConverter`          | Convert between different label shapes (multi_label / is_list) |
| `LabelIndexConverter`          | Convert label names to indices                                 |

### Mask Converters

| Converter                                     | Description                       |
| --------------------------------------------- | --------------------------------- |
| `MaskCallableToMaskConverter`                 | Execute lazy mask loader          |
| `MaskChannelsFirstConverter`                  | Mask HWC / CHW conversion         |
| `InstanceMaskCallableToInstanceMaskConverter` | Execute lazy instance mask loader |

### Video/Media Converters

| Converter                            | Description                         |
| ------------------------------------ | ----------------------------------- |
| `VideoFramePathToImageConverter`     | Load video frame from path          |
| `VideoFrameToImageCallableConverter` | Create lazy loader from video frame |
| `MediaPathToImageConverter`          | Load image from media path          |
| `MediaPathToImageCallableConverter`  | Create lazy loader from media path  |
