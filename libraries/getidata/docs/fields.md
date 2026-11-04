# Field Types

The module provides a rich set of field types for common ML data. Fields are type descriptors that define how data is stored in Polars DataFrames and converted between representations.

## Image Fields

| Field                | Description                    | Factory Function                             |
| -------------------- | ------------------------------ | -------------------------------------------- |
| `ImageField`         | In-memory image tensor         | `image_field(dtype, format, channels_first)` |
| `ImagePathField`     | Path to image file on disk     | `image_path_field()`                         |
| `ImageCallableField` | Lazy-loaded image via callable | `image_callable_field()`                     |
| `ImageBytesField`    | Raw image bytes                | `image_bytes_field()`                        |
| `TensorField`        | Generic n-dimensional tensor   | `tensor_field(dtype, semantic)`              |
| `ImageInfoField`     | Image metadata (width, height) | `image_info_field(semantic)`                 |

```python
import numpy as np
import polars as pl
from getidata import Dataset, Sample, LazyImage
from getidata.fields import (
    ImageInfo, image_field, image_path_field, image_info_field, tensor_field,
)

# In-memory image
class InMemorySample(Sample):
    image: np.ndarray = image_field(dtype=pl.UInt8(), format="RGB")
    image_info: ImageInfo = image_info_field()

sample = InMemorySample(
    image=np.zeros((480, 640, 3), dtype=np.uint8),
    image_info=ImageInfo(width=640, height=480),
)

# Path-based lazy loading (see Media Handling docs for details)
class PathSample(Sample):
    image: LazyImage = image_path_field()

sample = PathSample(image="/path/to/image.jpg")
print(sample.image.path)   # "/path/to/image.jpg"
# sample.image.data        # loads from disk on first access

# Generic tensor (e.g. depth map, feature vector)
class DepthSample(Sample):
    depth: np.ndarray = tensor_field(dtype=pl.Float32(), semantic="depth")

sample = DepthSample(depth=np.ones((480, 640), dtype=np.float32))
```

## Annotation Fields

| Field              | Description            | Factory Function                           |
| ------------------ | ---------------------- | ------------------------------------------ |
| `BBoxField`        | Bounding boxes         | `bbox_field(dtype, format, normalize)`     |
| `RotatedBBoxField` | Rotated bounding boxes | `rotated_bbox_field(dtype, format)`        |
| `PolygonField`     | Polygon annotations    | `polygon_field(dtype)`                     |
| `LabelField`       | Class labels           | `label_field(dtype, multi_label, is_list)` |
| `KeypointsField`   | Keypoint annotations   | `keypoints_field(dtype)`                   |
| `CaptionField`     | Text captions          | `caption_field(is_list)`                   |
| `EllipseField`     | Ellipse annotations    | `ellipse_field(dtype)`                     |

```python
from getidata.fields import (
    bbox_field, label_field, polygon_field, keypoints_field,
    caption_field, ellipse_field, rotated_bbox_field,
)

class DetectionSample(Sample):
    # Bounding boxes: each row is [x1, y1, x2, y2]
    bboxes: np.ndarray = bbox_field(dtype=pl.Float32(), format="x1y1x2y2")
    # One label index per bbox
    labels: np.ndarray = label_field(dtype=pl.UInt8(), is_list=True)

sample = DetectionSample(
    bboxes=np.array([[10, 20, 100, 150], [50, 60, 200, 250]], dtype=np.float32),
    labels=np.array([0, 1], dtype=np.uint8),
)

class CaptionSample(Sample):
    # Single caption per image
    caption: str = caption_field()

class MultiCaptionSample(Sample):
    # Multiple captions per image
    captions: list[str] = caption_field(is_list=True)

sample = MultiCaptionSample(captions=["a cat on a mat", "a feline sitting"])

class KeypointSample(Sample):
    # Keypoints: each row is [x, y, visibility] where visibility: 0=absent, 1=hidden, 2=visible
    keypoints: np.ndarray = keypoints_field(dtype=pl.Float32())

sample = KeypointSample(
    keypoints=np.array([[100, 200, 2], [150, 250, 2], [120, 300, 1]], dtype=np.float32),
)
```

## Mask Fields

| Field                       | Description                | Factory Function                 |
| --------------------------- | -------------------------- | -------------------------------- |
| `MaskField`                 | Semantic segmentation mask | `mask_field(dtype)`              |
| `MaskCallableField`         | Lazy-loaded semantic mask  | `mask_callable_field()`          |
| `InstanceMaskField`         | Instance segmentation mask | `instance_mask_field(dtype)`     |
| `InstanceMaskCallableField` | Lazy-loaded instance mask  | `instance_mask_callable_field()` |

```python
from getidata.fields import mask_field, instance_mask_field

class SegmentationSample(Sample):
    image: np.ndarray = image_field(dtype=pl.UInt8(), format="RGB")
    # Semantic mask: 2D array, each pixel is a class index
    mask: np.ndarray = mask_field(dtype=pl.UInt8())
    image_info: ImageInfo = image_info_field()

mask = np.zeros((480, 640), dtype=np.uint8)
mask[100:300, 200:400] = 1  # class 1 region
sample = SegmentationSample(
    image=np.zeros((480, 640, 3), dtype=np.uint8),
    mask=mask,
    image_info=ImageInfo(width=640, height=480),
)

class InstanceSegSample(Sample):
    # Instance masks: 3D array (num_instances, H, W), each is a boolean mask
    instances: np.ndarray = instance_mask_field(dtype=pl.Boolean())
    labels: np.ndarray = label_field(dtype=pl.UInt8(), is_list=True)

instances = np.zeros((2, 480, 640), dtype=bool)
instances[0, 100:200, 100:200] = True  # instance 0
instances[1, 300:400, 300:400] = True  # instance 1
sample = InstanceSegSample(
    instances=instances,
    labels=np.array([0, 1], dtype=np.uint8),
)
```

## Video Fields

| Field                     | Description                          | Factory Function               |
| ------------------------- | ------------------------------------ | ------------------------------ |
| `VideoFramePathField`     | Path to video file + frame index     | `video_frame_path_field()`     |
| `VideoFrameCallableField` | Lazy-loaded video frame              | `video_frame_callable_field()` |
| `MediaPathField`          | Generic media path (image or video)  | `media_path_field()`           |
| `MediaInfoField`          | Generic media metadata               | `media_info_field()`           |
| `VideoInfoField`          | Video metadata (fps, duration, etc.) | `video_info_field()`           |

See the [Media Handling](media.md) page for video examples.

## Other Fields

| Field          | Description                         | Factory Function                          |
| -------------- | ----------------------------------- | ----------------------------------------- |
| `SubsetField`  | Dataset subset (train/val/test)     | `subset_field()`                          |
| `TileField`    | Tile metadata for tiling operations | `tile_field()`                            |
| `NumericField` | Numeric values                      | `numeric_field(semantic, dtype, is_list)` |
| `StringField`  | String values                       | `string_field(semantic, is_list)`         |
| `BoolField`    | Boolean values                      | `bool_field(semantic, is_list)`           |

```python
from getidata.fields import (
    Subset, subset_field, numeric_field, string_field, bool_field,
)

class RichSample(Sample):
    image: np.ndarray = image_field(dtype=pl.UInt8(), format="RGB")
    # Dataset split
    subset: Subset = subset_field()
    # Scalar metadata
    score: float = numeric_field(semantic="confidence", dtype=pl.Float32())
    source: str = string_field(semantic="source_file")
    is_crowd: bool = bool_field(semantic="is_crowd")
    # List metadata (one per annotation)
    areas: list[float] = numeric_field(semantic="area", dtype=pl.Float32(), is_list=True)

sample = RichSample(
    image=np.zeros((100, 100, 3), dtype=np.uint8),
    subset=Subset.TRAINING,
    score=0.95,
    source="camera_1",
    is_crowd=False,
    areas=[1500.0, 320.0],
)
```

## Semantic Tags

When you have multiple fields of the same type (e.g., stereo images), use semantic tags to distinguish them:

```python
class StereoSample(Sample):
    left_image: np.ndarray = image_field(dtype=pl.UInt8(), format="RGB", semantic="left")
    right_image: np.ndarray = image_field(dtype=pl.UInt8(), format="RGB", semantic="right")
    left_info: ImageInfo = image_info_field(semantic="left")
    right_info: ImageInfo = image_info_field(semantic="right")
```

The schema enforces that only one field of each (type, semantic) combination can exist.
