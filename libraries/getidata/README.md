# getidata

`getidata` is a library that provides a modern, type-safe framework for working with machine learning datasets. It offers a declarative approach to defining data schemas, automatic type conversion between different representations, and efficient storage using Polars DataFrames.

## Key Concepts

| Concept       | Description                                                                   |
| ------------- | ----------------------------------------------------------------------------- |
| **Sample**    | A dataclass-like definition of a single data point in your dataset            |
| **Dataset**   | A typed container holding multiple samples with a consistent schema           |
| **Schema**    | A formal description of the dataset structure derived from Sample definitions |
| **Field**     | Type descriptors that define how data is stored and converted                 |
| **Converter** | Transformation logic between different field representations                  |
| **Transform** | Lazy operations applied during sample retrieval                               |

## Quick Start

```python
import numpy as np
import polars as pl
from getidata import Dataset, Sample
from getidata.fields import ImageInfo, bbox_field, image_field, image_info_field, label_field
from getidata.categories import LabelCategories

# 1. Define your sample schema
class DetectionSample(Sample):
    image: np.ndarray = image_field(dtype=pl.UInt8(), format="RGB")
    bboxes: np.ndarray = bbox_field(dtype=pl.Float32(), format="x1y1x2y2")
    labels: np.ndarray = label_field(dtype=pl.UInt8(), is_list=True)
    image_info: ImageInfo = image_info_field()

# 2. Create a dataset with categories
categories = {"labels": LabelCategories(labels=("person", "car", "bicycle"))}
dataset = Dataset(DetectionSample, categories=categories)

# 3. Add samples
sample = DetectionSample(
    image=np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8),
    bboxes=np.array([[10, 20, 100, 150]], dtype=np.float32),
    labels=np.array([0], dtype=np.uint8),
    image_info=ImageInfo(width=224, height=224),
)
dataset.append(sample)

# 4. Access samples
for s in dataset:
    print(s.image.shape, s.labels)
```

## Working with Datasets

```python
# Add multiple samples at once
dataset.append_batch(samples)

# Index, iterate, slice
sample = dataset[0]
subset = dataset.slice(offset=10, length=50)

# Mutate
dataset[0] = new_sample
del dataset[0]

# Filter
train = dataset.filter_by_subset(Subset.TRAINING)
cats_and_dogs = dataset.filter_by_labels(["cat", "dog"])

# Merge
dataset1.append_dataset(dataset2)

# Convert schema automatically (A* search for optimal conversion path)
target_dataset = dataset.convert_to_schema(TargetSample)

# Export / Import
from getidata import export_dataset, import_dataset
export_dataset(dataset, "my_dataset.zip", as_zip=True)
loaded = import_dataset("my_dataset.zip")
```

> **Note**: Transformed datasets (after `convert_to_schema()` or `transform()`) are immutable.

## Categories

```python
from getidata.categories import LabelCategories, HierarchicalLabelCategories, MaskCategories

# Simple labels
labels = LabelCategories(labels=("cat", "dog", "bird"))

# Hierarchical labels (parent-child relationships)
hierarchy = HierarchicalLabelCategories(
    labels=("animal", "cat", "dog"),
    parent_map={"cat": "animal", "dog": "animal"},
)

# Mask colormap
mask_cats = MaskCategories(colormap={0: (0,0,0), 1: (255,0,0)})

# Attach to dataset
dataset = Dataset(MySample, categories={"labels": labels})
```

## Detailed Documentation

The full documentation is split into focused pages:

| Page                                                                      | Contents                                                                        |
| ------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| **[Field Types](docs/fields.md)**                                         | All available fields (image, annotation, mask, video, etc.) and semantic tags   |
| **[Converters](docs/converters.md)**                                      | Schema conversion, custom converters, and the full built-in converter reference |
| **[Import & Export](docs/import_export.md)**                              | Native Parquet format, COCO/VOC/YOLO loaders, `ExportMode`, `register_sample`   |
| **[Media Handling](docs/media.md)**                                       | `LazyImage`, `LazyVideoFrame`, image/video caching, and memory management       |
| **[Transforms, Tiling & Filtering](docs/transforms_tiling_filtering.md)** | Lazy transforms, tiling config, available tilers, and filtering APIs            |

## Type Registry

Register custom type converters for Polars serialization:

```python
from getidata import register_numpy_converter, register_from_polars_converter

@register_numpy_converter(MyCustomType)
def custom_to_numpy(value, dtype):
    return np.array(value.data)

@register_from_polars_converter(MyCustomType)
def numpy_to_custom(data, target_type):
    return MyCustomType(data)
```

## API Reference

| Module                   | Description                                      |
| ------------------------ | ------------------------------------------------ |
| `getidata.dataset`       | `Dataset` and `Sample` classes                   |
| `getidata.schema`        | `Schema` and `AttributeInfo`                     |
| `getidata.fields`        | Field type definitions                           |
| `getidata.converters`    | Converter system                                 |
| `getidata.categories`    | Category definitions                             |
| `getidata.export_import` | Import/export functions                          |
| `getidata.transform`     | Transform base classes                           |
| `getidata.media`         | Media handling (images and videos)               |
| `getidata.filtering`     | Filtering utilities                              |
| `getidata.tiling`        | Tiling utilities                                 |
| `getidata.data_formats`  | Format-specific loaders/savers (COCO, VOC, YOLO) |
