# Transforms, Tiling & Filtering

## Transforms

Transforms enable lazy, chainable operations on datasets without materializing intermediate results.

### Lazy Evaluation

Many operations (like schema conversion) create transform chains that are only evaluated when samples are accessed:

```python
# This creates a transform chain, not immediate conversion
converted = dataset.convert_to_schema(TargetSample)

# The conversion happens here, when accessing data
sample = converted[0]  # Lazy evaluation triggered
```

### Custom Transforms

Create custom transforms by implementing the `Transform` class:

```python
from getidata.transform import Transform

class MyTransform(Transform):
    def __init__(self, parent: Transform, schema: Schema):
        super().__init__(schema)
        self._parent = parent

    def apply(self, fields: Sequence[str]) -> pl.DataFrame:
        """Apply transformation to the specified fields."""
        df = self._parent.apply(fields)
        # ... modify df
        return df

    def get_lazy_attributes(self) -> set[str]:
        """Return attributes that should be evaluated lazily."""
        return self._parent.get_lazy_attributes()

    def slice(self, offset: int, length: int | None = None) -> Transform:
        """Create a slice of this transform."""
        # ... implementation

    def __len__(self) -> int:
        return len(self._parent)
```

Use transforms via the dataset's `transform()` method:

```python
new_dataset = dataset.transform(
    lambda parent: MyTransform(parent, schema),
    dtype=TargetSample,
)
```

---

## Tiling

The tiling system splits large images into smaller tiles for processing. This is useful for high-resolution imagery and dense object detection.

### End-to-end example

```python
import numpy as np
import polars as pl
from getidata import Dataset, Sample
from getidata.fields import (
    ImageInfo, bbox_field, image_field, image_info_field, label_field,
)
from getidata.tiling.tiler_registry import TilingConfig, create_tiling_transform

# 1. Define a sample schema (must include image_info)
class DetectionSample(Sample):
    image: np.ndarray = image_field(dtype=pl.UInt8())
    bboxes: np.ndarray = bbox_field(dtype=pl.Float32())
    labels: np.ndarray = label_field(dtype=pl.UInt8(), is_list=True)
    image_info: ImageInfo = image_info_field()

# 2. Create a dataset with a large image
dataset = Dataset(DetectionSample)
dataset.append(DetectionSample(
    image=np.zeros((200, 200, 3), dtype=np.uint8),
    bboxes=np.array([[10, 10, 90, 90], [120, 120, 180, 180]], dtype=np.float32),
    labels=np.array([0, 1], dtype=np.uint8),
    image_info=ImageInfo(width=200, height=200),
))
print(f"Before tiling: {len(dataset)} samples")  # 1

# 3. Configure and apply tiling
config = TilingConfig(tile_width=100, tile_height=100)
tiled_dataset = dataset.transform(create_tiling_transform(config))

print(f"After tiling: {len(tiled_dataset)} samples")  # 4 (2x2 grid)

# Each tile is a regular sample with clipped bboxes, cropped images, etc.
for i in range(len(tiled_dataset)):
    tile = tiled_dataset[i]
    print(f"Tile {i}: image {tile.image.shape}, {len(tile.bboxes)} bboxes")
```

### TilingConfig

```python
# Tiles with overlap (useful to avoid cutting objects at boundaries)
config = TilingConfig(
    tile_width=512,
    tile_height=512,
    overlap_x=0.1,  # 10% horizontal overlap
    overlap_y=0.1,  # 10% vertical overlap
)

# Control annotation drop threshold (default 0.8 = keep if 80% of area is in tile)
tiled = dataset.transform(create_tiling_transform(config, threshold_drop_ann=0.5))
```

### Available Tilers

Tilers are registered per field type and handle how each field should be tiled:

| Tiler               | Field Type          | Description                                     |
| ------------------- | ------------------- | ----------------------------------------------- |
| `ImageTiler`        | `ImageField`        | Extracts image regions for each tile            |
| `BBoxTiler`         | `BBoxField`         | Clips/filters bounding boxes to tile boundaries |
| `PolygonTiler`      | `PolygonField`      | Clips polygons to tile boundaries               |
| `MaskTiler`         | `MaskField`         | Extracts mask regions                           |
| `InstanceMaskTiler` | `InstanceMaskField` | Extracts instance mask regions with keep flags  |
| `LabelTiler`        | `LabelField`        | Handles labels during tiling                    |
| `PassthroughTiler`  | `SubsetField`       | Passes through unchanged (e.g., subset info)    |

### Custom Tilers

Register custom tilers for your field types:

```python
from getidata.tiling.tiler_registry import Tiler, TilerRegistry

@TilerRegistry.register(MyCustomField)
class MyCustomTiler(Tiler):
    def tile(self, df: pl.DataFrame, tiles_df: pl.DataFrame, slice_offset: int = 0) -> pl.DataFrame:
        # Implement tiling logic for your field
        ...
        return result_df
```

---

## Filtering

The filtering system removes samples or annotations based on criteria.

### Filtering empty annotations

The built-in filters automatically remove samples with empty annotation lists (e.g., no bounding boxes). Apply them using `create_filtering_transform`:

```python
import numpy as np
import polars as pl
from getidata import Dataset, Sample
from getidata.fields import bbox_field, image_field
from getidata.filtering.filter_registry import create_filtering_transform

class DetectionSample(Sample):
    image: np.ndarray = image_field(dtype=pl.UInt8())
    bboxes: np.ndarray = bbox_field(dtype=pl.Float32())

dataset = Dataset(DetectionSample)

# Add samples — some with bboxes, one without
dataset.append(DetectionSample(
    image=np.zeros((50, 50, 3), dtype=np.uint8),
    bboxes=np.array([[10, 10, 40, 40]], dtype=np.float32),
))
dataset.append(DetectionSample(
    image=np.zeros((50, 50, 3), dtype=np.uint8),
    bboxes=np.array([], dtype=np.float32).reshape(0, 4),  # empty
))
dataset.append(DetectionSample(
    image=np.zeros((50, 50, 3), dtype=np.uint8),
    bboxes=np.array([[5, 5, 20, 20]], dtype=np.float32),
))

print(f"Before filtering: {len(dataset)} samples")  # 3

filtered = dataset.transform(create_filtering_transform())
print(f"After filtering: {len(filtered)} samples")   # 2 (empty bboxes removed)
```

### Filtering by labels

```python
from getidata.categories import LabelCategories

categories = {"labels": LabelCategories(labels=("cat", "dog", "bird"))}
dataset = Dataset(MySample, categories=categories)
# ... add samples ...

# Keep only samples with "cat" or "dog" labels
filtered = dataset.filter_by_labels(["cat", "dog"])

# Same thing using indices
filtered = dataset.filter_by_labels([0, 1])

# Explicit field name (required when multiple LabelFields exist)
filtered = dataset.filter_by_labels(["cat"], label_field_name="labels")

# Remap categories so filtered labels become indices 0, 1, ...
filtered = dataset.filter_by_labels(["cat", "dog"], update_categories=True)

# Keep all samples but strip non-matching labels and annotations
filtered = dataset.filter_by_labels(["cat"], keep_empty_samples=True)
```

### Filtering by subset

```python
from getidata.fields import Subset

train_dataset = dataset.filter_by_subset(Subset.TRAINING)
val_dataset = dataset.filter_by_subset(Subset.VALIDATION)
```

### Custom filters

Register custom filters for your field types:

```python
from getidata.filtering.filter_registry import FilterRegistry, Filter
from getidata.fields import BBoxField

@FilterRegistry.register(BBoxField)
class EmptyBBoxFilter(Filter):
    def filter(self, df: pl.DataFrame) -> pl.Expr:
        """Return boolean expression for rows to keep."""
        return pl.col(self.field_spec.name).list.len() > 0
```
