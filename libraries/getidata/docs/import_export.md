# Import and Export

## Native Format (Parquet)

### End-to-end round trip

```python
import numpy as np
import polars as pl
from getidata import Dataset, Sample, export_dataset, import_dataset
from getidata.fields import ImageInfo, bbox_field, image_field, image_info_field, label_field, subset_field, Subset
from getidata.categories import LabelCategories
from getidata.export_import import ExportMode

# 1. Define a sample and create a dataset
class MySample(Sample):
    image: np.ndarray = image_field(dtype=pl.UInt8(), format="RGB")
    bboxes: np.ndarray = bbox_field(dtype=pl.Float32(), format="x1y1x2y2")
    labels: np.ndarray = label_field(dtype=pl.UInt8(), is_list=True)
    image_info: ImageInfo = image_info_field()
    subset: Subset = subset_field()

categories = {"labels": LabelCategories(labels=("cat", "dog"))}
dataset = Dataset(MySample, categories=categories)

dataset.append(MySample(
    image=np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8),
    bboxes=np.array([[10, 20, 50, 80]], dtype=np.float32),
    labels=np.array([0], dtype=np.uint8),
    image_info=ImageInfo(width=100, height=100),
    subset=Subset.TRAINING,
))

# 2. Export to disk
export_dataset(dataset, "/tmp/my_dataset", export_media=ExportMode.COPY)

# 3. Re-import
loaded = import_dataset("/tmp/my_dataset", dtype=MySample)
print(len(loaded))          # 1
print(loaded[0].labels)     # [0]
print(loaded[0].subset)     # Subset.TRAINING
```

### Export options

```python
from getidata import export_dataset, import_dataset
from getidata.export_import import ExportMode

# Export to directory (copies images and videos to output)
export_dataset(dataset, "/path/to/output", export_media=ExportMode.COPY)

# Export as ZIP archive
export_dataset(dataset, "/path/to/output.zip", export_media=ExportMode.COPY, as_zip=True)

# Export with references only (faster, but not portable)
export_dataset(dataset, "/path/to/output", export_media=ExportMode.REFERENCE)

# Skip media export entirely
export_dataset(dataset, "/path/to/output", export_media=ExportMode.SKIP)

# Import dataset
loaded_dataset = import_dataset("/path/to/output")

# Import with specific Sample type (for type hints)
loaded_dataset = import_dataset("/path/to/output", dtype=DetectionSample)
```

The export format includes:

- `data.parquet`: DataFrame with all serializable data
- `metadata.json`: Schema, categories, and version info
- `images/`: Exported images (when using `ExportMode.COPY`)
- `videos/`: Exported videos (when using `ExportMode.COPY`)

### ExportMode

| Mode                   | Description                                                        |
| ---------------------- | ------------------------------------------------------------------ |
| `ExportMode.SKIP`      | Don't export media files                                           |
| `ExportMode.REFERENCE` | Keep original absolute paths (not portable, but faster)            |
| `ExportMode.COPY`      | Copy files to output directory (portable, recommended for sharing) |

### Registering Custom Sample Types

For automatic dtype detection during import, register your custom Sample classes:

```python
from getidata import register_sample, Sample

@register_sample
class MySample(Sample):
    image: LazyImage = image_path_field()
    labels: np.ndarray = label_field(dtype=pl.Int32(), is_list=True)

# Now import_dataset can automatically detect MySample
dataset = import_dataset("/path/to/my_dataset")  # dtype inferred
```

---

## Data Formats

Load and save datasets in common formats using `import_dataset` and `export_dataset` with the `data_format` parameter, or use the format-specific APIs directly.

### COCO Format

The COCO loader supports both simple and split layouts:

```python
from getidata.data_formats.coco.io import load_coco_dataset, save_coco_dataset
from getidata.data_formats.coco.sample import CocoSample

# Simple layout: single folder
dataset = load_coco_dataset(
    images_dir_path="/path/to/images",
    annotations_path="/path/to/annotations.json",
)

# Split layout: multiple subsets
dataset = load_coco_dataset(
    images_dir_path={
        "train": "/path/to/train2017",
        "val": "/path/to/val2017",
    },
    annotations_path={
        "train": "/path/to/instances_train2017.json",
        "val": "/path/to/instances_val2017.json",
    },
)

# Load multiple annotation types at once
dataset = load_coco_dataset(
    images_dir_path="/path/to/images",
    annotations_path=[
        "/path/to/instances.json",
        "/path/to/captions.json",
        "/path/to/keypoints.json",
    ],
)

# Work with CocoSample attributes
for sample in dataset:
    print(sample.image)       # LazyImage (path-based)
    print(sample.bboxes)      # Bounding boxes (xywh format)
    print(sample.labels)      # Class labels
    print(sample.polygons)    # Polygon annotations
    print(sample.keypoints)   # Keypoint annotations
    print(sample.captions)    # Image captions
    print(sample.areas)       # Annotation areas
    print(sample.iscrowd)     # Crowd flags
    print(sample.subset)      # train/val/test
    print(sample.image_id)    # COCO image ID

# Save dataset
save_coco_dataset(
    dataset,
    images_dir_path="/path/to/output/images",
    annotations_path="/path/to/output/annotations.json",
)
```

### VOC Format

```python
from getidata.data_formats.voc.io import load_voc_dataset, save_voc_dataset

# Load from standard VOC layout
dataset = load_voc_dataset(root_dir="/path/to/VOC2012")

# Or specify paths directly
dataset = load_voc_dataset(
    images_dir_path="/path/to/JPEGImages",
    annotations_dir_path="/path/to/Annotations",
)

# Save as VOC format
save_voc_dataset(dataset, root_dir="/path/to/output")
```

### YOLO Format

```python
from getidata.data_formats.yolo.io import load_yolo_dataset, save_yolo_dataset
from getidata.data_formats.base import DataFormat

# Load YOLO dataset (auto-detect format)
dataset = load_yolo_dataset(root_dir="/path/to/yolo_dataset")

# Load Ultralytics YOLO format specifically
dataset = load_yolo_dataset(root_dir="/path/to/yolo_dataset", format="ultralytics")

# Save as YOLO format
save_yolo_dataset(dataset, root_dir="/path/to/output", format=DataFormat.YOLO)
```

### Generic Format API

Use the generic `import_dataset` / `export_dataset` functions with the `data_format`
parameter for format-agnostic code:

```python
from getidata import import_dataset, export_dataset
from getidata.data_formats.base import DataFormat

# Load COCO
dataset = import_dataset(
    "/path/to/coco",
    data_format=DataFormat.COCO,
    images_dir_path="/path/to/images",
    annotations_path="/path/to/annotations.json",
)

# Load VOC
dataset = import_dataset(
    "/path/to/voc",
    data_format=DataFormat.VOC,
    root_dir="/path/to/VOC2012",
)

# Load YOLO
dataset = import_dataset(
    "/path/to/yolo",
    data_format=DataFormat.YOLO,
    root_dir="/path/to/yolo_dataset",
)

# Save to any format
export_dataset(dataset, "/path/to/output", data_format=DataFormat.COCO)
export_dataset(dataset, "/path/to/output", data_format=DataFormat.VOC)
export_dataset(dataset, "/path/to/output", data_format=DataFormat.YOLO)

# Save as ZIP archive
export_dataset(dataset, "/path/to/output.zip", data_format=DataFormat.COCO, as_zip=True)
```
