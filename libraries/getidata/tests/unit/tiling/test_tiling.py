import numpy as np
import polars as pl
import pytest

from getidata.dataset import AttributeInfo
from getidata.fields import (
    TileInfo,
    bbox_field,
    image_field,
    image_info_field,
    instance_mask_field,
    label_field,
    mask_field,
    polygon_field,
    tile_field,
)
from getidata.schema import Schema
from getidata.tiling.tiler_registry import (
    AttributeSpec,
    TilingConfig,
    TilingTransform,
    _apply_tiling,
    _calculate_tiles,
    _create_tiling_plan,
    _TilingTransformFactory,
    create_tiling_transform,
)


@pytest.fixture
def sample_schema():
    return Schema(
        attributes={
            "image": AttributeInfo(type=np.ndarray, field=image_field(pl.UInt8())),
            "image_info": AttributeInfo(type=dict, field=image_info_field()),
        }
    )


@pytest.fixture
def sample_df():
    # Create sample image data
    image1 = np.zeros((100, 100, 3), dtype=np.uint8)
    image2 = np.ones((200, 150, 3), dtype=np.uint8)

    # Flatten images and get shapes
    flat_image1 = image1.reshape(-1)
    flat_image2 = image2.reshape(-1)
    shape1 = list(image1.shape)
    shape2 = list(image2.shape)

    # Create sample image info
    info1 = {"height": 100, "width": 100}
    info2 = {"height": 200, "width": 150}

    # Create DataFrame with explicit schema
    return pl.DataFrame(
        {
            "image": [flat_image1, flat_image2],
            "image_shape": [shape1, shape2],
            "image_info": [info1, info2],
        },
        schema={
            "image": pl.List(pl.UInt8()),
            "image_shape": pl.List(pl.Int32()),
            "image_info": pl.Struct(
                [
                    pl.Field("height", pl.Int32()),
                    pl.Field("width", pl.Int32()),
                ]
            ),
        },
    )


def test_calculate_tiles(sample_df):
    config = TilingConfig(tile_width=50, tile_height=50)

    schema = Schema(
        attributes={
            "image_info": AttributeInfo(type=dict, field=image_info_field()),
            "tile": AttributeInfo(type=dict, field=tile_field()),
        }
    )

    # Create specs from schema
    image_info_spec = AttributeSpec(name="image_info", field=schema.attributes["image_info"].field)
    tile_info_spec = AttributeSpec(name="tile", field=schema.attributes["tile"].field)

    # Calculate tiles
    tiles_df = _calculate_tiles(sample_df, config, image_info_spec, tile_info_spec, 0)

    # Check that we have the right number of tiles
    # First image (100x100) should have 4 tiles (2x2 grid)
    # Second image (200x150) should have 12 tiles (4x3 grid)
    assert len(tiles_df) == 16

    # Verify tile parameters
    tiles = [TileInfo(**row["tile"]) for row in tiles_df.to_dicts()]

    # Check first image tiles
    first_image_tiles = tiles[:4]
    for tile in first_image_tiles:
        assert tile.width <= 50
        assert tile.height <= 50
        assert tile.x % 50 == 0
        assert tile.y % 50 == 0

    # Check second image tiles
    second_image_tiles = tiles[4:]
    for tile in second_image_tiles:
        assert tile.width <= 50
        assert tile.height <= 50
        assert tile.x % 50 == 0
        assert tile.y % 50 == 0


def test_apply_tiling(sample_df, sample_schema):
    config = TilingConfig(tile_width=50, tile_height=50)

    # Apply tiling
    plan = _create_tiling_plan(sample_schema, config)
    result_df, result_fields = _apply_tiling(sample_df, None, plan, ["image", "image_info"])

    # Check the generated fields
    assert result_fields == {"image", "image_info"}

    # Check DataFrame
    assert "tile" in result_df.columns
    assert "image_info" in result_df.columns
    assert "image" in result_df.columns
    assert len(result_df) == 16  # Same as test_calculate_tiles

    # Check image info field values
    for row in result_df.iter_rows(named=True):
        tile_info = row["image_info"]
        # Each tile should have dimensions <= config size
        assert tile_info["width"] <= config.tile_width
        assert tile_info["height"] <= config.tile_height
        # Should track original image
        assert "source_sample_idx" in tile_info


def test_tiling_with_overlap(sample_df, sample_schema):
    config = TilingConfig(tile_width=50, tile_height=50, overlap_x=0.2, overlap_y=0.2)

    # Apply tiling
    plan = _create_tiling_plan(sample_schema, config)
    result_df, _ = _apply_tiling(sample_df, None, plan, [])

    # Convert tile data to TileInfo objects
    tiles = [TileInfo(**row["tile"]) for row in result_df.to_dicts()]

    # Check overlap between adjacent tiles
    for i in range(len(tiles) - 1):
        tile = tiles[i]
        next_tile = tiles[i + 1]

        # If tiles are from the same row
        if tile.source_sample_idx == next_tile.source_sample_idx and tile.y == next_tile.y:
            overlap = ((tile.x + tile.width) - next_tile.x) / tile.width
            assert overlap == config.overlap_x

        # If tiles are from the same column
        elif tile.source_sample_idx == next_tile.source_sample_idx and tile.x == next_tile.x:
            overlap = ((tile.y + tile.height) - next_tile.y) / tile.height
            assert overlap == config.overlap_y


def test_invalid_schema():
    # Create schema without image info
    invalid_schema = Schema(
        attributes={
            "image": AttributeInfo(type=np.ndarray, field=image_field(pl.UInt8())),
        }
    )

    pl.DataFrame({"image": [np.zeros((100, 100, 3)).flatten()], "image_shape": [(100, 100, 3)]})
    config = TilingConfig(tile_width=50, tile_height=50)

    # Should raise error due to missing ImageInfoField
    with pytest.raises(ValueError, match="Schema must contain an ImageInfoField"):
        _create_tiling_plan(invalid_schema, config)


def test_mask_tiling():
    # Create schema with both types of masks
    schema = Schema(
        attributes={
            "image_info": AttributeInfo(type=dict, field=image_info_field()),
            "segmentation": AttributeInfo(type=np.ndarray, field=mask_field()),
            "instances": AttributeInfo(type=list, field=instance_mask_field()),
        }
    )

    # Create sample data
    # Semantic segmentation: 100x100 with two classes (0 and 1)
    semantic_mask = np.zeros((100, 100), dtype=np.int32)
    semantic_mask[25:75, 25:75] = 1  # Class 1 square in middle

    # Instance segmentation: 2 instances x 100 x 100
    instances = np.zeros((2, 100, 100), dtype=bool)
    instances[0, 20:70, 20:70] = True  # Large instance in middle
    instances[1, 80:90, 80:90] = True  # Small instance in corner

    df = pl.DataFrame(
        {
            "image_info": [
                {"width": 100, "height": 100},
            ],
            "segmentation": semantic_mask.reshape(1, -1),
            "segmentation_shape": [semantic_mask.shape],
            "instances": instances.reshape(1, -1),
            "instances_shape": [instances.shape],
        }
    )

    # Configure tiling to create 50x50 tiles
    config = TilingConfig(tile_width=50, tile_height=50)

    # Apply tiling
    plan = _create_tiling_plan(schema, config)
    result_df, _ = _apply_tiling(df, None, plan, ["segmentation", "instances"])

    # There should be 4 tiles (2x2 grid)
    assert len(result_df) == 4

    # Check first tile (top-left)

    # Check semantic segmentation tile
    assert result_df[0, "segmentation"].shape == (50 * 50,)
    assert tuple(result_df[0, "segmentation_shape"]) == (50, 50)
    assert np.any(result_df[0, "segmentation"].to_numpy() == 1)  # Should contain class 1

    # Check instance segmentation tile
    # Only instance 0 (bbox 20-70) overlaps the top-left tile; the corner
    # instance 1 (bbox 80-90) is filtered out to stay aligned with boxes/labels.
    assert result_df[0, "instances"].shape == (1 * 50 * 50,)
    assert tuple(result_df[0, "instances_shape"]) == (1, 50, 50)
    instances = result_df[0, "instances"].reshape((1, 50, 50)).to_numpy()
    assert np.any(instances[0])

    # Check last tile (bottom-right)

    # Check semantic segmentation tile
    assert result_df[3, "segmentation"].shape == (50 * 50,)
    assert tuple(result_df[3, "segmentation_shape"]) == (50, 50)
    assert np.any(result_df[3, "segmentation"].to_numpy() == 1)  # Should contain class 1

    # Check instance segmentation tile
    # Both instances overlap the bottom-right tile, so both are kept.
    assert result_df[3, "instances"].shape == (2 * 50 * 50,)
    assert tuple(result_df[3, "instances_shape"]) == (2, 50, 50)
    instances = result_df[3, "instances"].reshape((2, 50, 50)).to_numpy()
    assert np.any(instances[0])  # First (large) instance spans all tiles, so present here
    assert np.any(instances[1])  # Second (small corner) instance present only in this tile


def test_bbox_tiling():
    # Create schema with bounding boxes
    schema = Schema(
        attributes={
            "image_info": AttributeInfo(type=dict, field=image_info_field()),
            "bboxes": AttributeInfo(type=list, field=bbox_field(dtype=pl.Float64())),
        }
    )

    polars_schema = schema.attributes["image_info"].field.to_polars_schema("image_info")
    polars_schema.update(schema.attributes["bboxes"].field.to_polars_schema("bboxes"))

    # Create sample data with bounding boxes
    df = pl.DataFrame(
        {
            "image_info": [
                {"width": 100, "height": 100},
            ],
            "bboxes": [
                [
                    # Box that spans tiles
                    [20, 20, 80, 80],
                    # Box entirely in top-right tile
                    [60, 10, 90, 40],
                    # Box outside any tile (at overlap)
                    [48, 48, 52, 52],
                ]
            ],
        },
        schema=polars_schema,
    )

    # Configure tiling to create 50x50 tiles
    config = TilingConfig(tile_width=50, tile_height=50)

    # Apply tiling
    plan = _create_tiling_plan(schema, config, threshold_drop_ann=0.0)
    result_df, _ = _apply_tiling(df, None, plan, ["bboxes"])

    # There should be 4 tiles (2x2 grid)
    assert len(result_df) == 4

    # Check first tile (top-left, 0,0,50,50)
    assert len(result_df[0, "bboxes"]) == 2  # All original boxes except one
    assert (result_df[0, "bboxes"][0] == [20, 20, 50, 50]).all()
    assert (result_df[0, "bboxes"][1] == [48, 48, 50, 50]).all()

    # Check second tile (top-right, 50,0,100,50)
    assert len(result_df[1, "bboxes"]) == 3  # All original boxes
    assert (result_df[1, "bboxes"][0] == [0, 20, 30, 50]).all()  # Clipped and offset
    assert (result_df[1, "bboxes"][1] == [10, 10, 40, 40]).all()  # Offset from tile origin
    assert (result_df[1, "bboxes"][2] == [0, 48, 2, 50]).all()  # Clipped and offset


def test_polygon_and_label_tiling():
    # Create schema with both polygon and label fields
    schema = Schema(
        attributes={
            "image_info": AttributeInfo(type=dict, field=image_info_field()),
            "polygons": AttributeInfo(type=list, field=polygon_field(dtype=pl.Float64())),
            "labels": AttributeInfo(type=list, field=label_field(is_list=True)),
        }
    )

    # Create sample data with image info, polygons and labels
    df = pl.DataFrame(
        {
            "image_info": [
                {"width": 100, "height": 100},
            ],
            "polygons": [
                [
                    # Two polygons: one that will intersect tile, one that won't
                    [[25, 25], [75, 25], [75, 75], [25, 75], [25, 25]],  # Square in middle
                    [[80, 80], [90, 80], [90, 90], [80, 90], [80, 80]],  # Square in corner
                ]
            ],
            "labels": [["cat", "dog"]],  # One label per polygon
        }
    )

    # Configure tiling to create 50x50 tiles
    config = TilingConfig(tile_width=50, tile_height=50)

    # Apply tiling
    plan = _create_tiling_plan(schema, config, threshold_drop_ann=0.1)
    result_df, _ = _apply_tiling(df, None, plan, ["polygons", "labels"])

    # There should be 4 tiles (2x2 grid)
    assert len(result_df) == 4

    # Check first tile (top-left, should contain part of first polygon)
    assert len(result_df[0, "polygons"]) == 1  # One entry for the original polygon
    assert len(result_df[0, "labels"]) == 1  # One entry for the original label
    assert result_df[0, "labels"][0] == "cat"  # First label kept

    # Check last tile (bottom-right, should contain second polygon)
    assert len(result_df[3, "polygons"]) == 2
    assert len(result_df[3, "labels"]) == 2
    assert result_df[3, "labels"][0] == "cat"  # First label kept
    assert result_df[3, "labels"][1] == "dog"  # Second label kept


def test_create_tiling_transform_returns_module_level_callable():
    """The returned factory should be an instance of the module-level class,
    not a local closure, so it can be pickled by reference."""
    factory = create_tiling_transform(TilingConfig(tile_width=50, tile_height=50))

    assert isinstance(factory, _TilingTransformFactory)
    # Module-level qualname (no ``<locals>``) is what enables pickle-by-reference.
    assert "<locals>" not in type(factory).__qualname__
    assert type(factory).__module__ == create_tiling_transform.__module__


def test_create_tiling_transform_factory_stores_config():
    """The factory should retain the config and threshold it was created with."""
    config = TilingConfig(tile_width=64, tile_height=32, overlap_x=0.1, overlap_y=0.2)
    factory = create_tiling_transform(config, threshold_drop_ann=0.5)

    assert factory.config == config
    assert factory.threshold_drop_ann == 0.5


def test_create_tiling_transform_factory_is_picklable():
    """The factory returned by ``create_tiling_transform`` must pickle by reference."""
    import pickle

    config = TilingConfig(tile_width=50, tile_height=50, overlap_x=0.25, overlap_y=0.0)
    factory = create_tiling_transform(config, threshold_drop_ann=0.3)
    restored = pickle.loads(pickle.dumps(factory))

    assert isinstance(restored, _TilingTransformFactory)
    assert restored.config == config
    assert restored.threshold_drop_ann == 0.3


def test_tiling_factory_builds_transform_after_unpickling(sample_df, sample_schema):
    """A round-tripped factory should still build a working TilingTransform."""
    import pickle

    from getidata.transform import IdentityTransform

    config = TilingConfig(tile_width=50, tile_height=50)
    factory = pickle.loads(pickle.dumps(create_tiling_transform(config)))
    transform = factory(IdentityTransform(sample_df, sample_schema))

    assert isinstance(transform, TilingTransform)
    assert len(transform) == 16  # matches test_apply_tiling


def _bbox_tiler_keep(x1, y1, x2, y2, tx, ty, tw, th):
    """Reference reimplementation of ``BboxTiler``'s keep criterion."""
    return (x2 > tx) and (x1 < tx + tw) and (y2 > ty) and (y1 < ty + th)


def _mask_from_box(x1, y1, x2, y2, h=100, w=100):
    m = np.zeros((h, w), dtype=np.uint8)
    m[y1:y2, x1:x2] = 1
    return m


def test_instance_intersects_tile_drops_empty_mask():
    """An all-zero instance mask has no bounding box and is never kept."""
    from getidata.tiling.tilers import _boxes_intersect_tile, _instance_bounding_boxes

    instances = np.zeros((1, 100, 100), dtype=np.uint8)
    boxes = _instance_bounding_boxes(instances)
    # Empty mask yields a degenerate (0, 0, 0, 0) box.
    assert boxes.tolist() == [[0, 0, 0, 0]]
    assert _boxes_intersect_tile(boxes, 0, 0, 50, 50).tolist() == [False]


@pytest.mark.parametrize(
    ("box", "tile"),
    [
        ((10, 10, 40, 40), (0, 0, 50, 50)),  # fully inside
        ((45, 45, 60, 60), (0, 0, 50, 50)),  # straddles bottom-right corner
        ((49, 49, 55, 55), (0, 0, 50, 50)),  # 1px overlap in the tile
        ((60, 60, 90, 90), (50, 50, 50, 50)),  # inside the second tile
        ((50, 10, 70, 30), (0, 0, 50, 50)),  # touches right edge (x1==tile_x2) -> dropped
        ((10, 10, 40, 40), (50, 0, 50, 50)),  # left of the second tile -> dropped
    ],
)
def test_instance_intersects_tile_matches_bbox_tiler(box, tile):
    """The mask-derived keep decision equals the box-based ``BboxTiler`` decision."""
    from getidata.tiling.tilers import _boxes_intersect_tile, _instance_bounding_boxes

    x1, y1, x2, y2 = box
    tx, ty, tw, th = tile
    mask = _mask_from_box(x1, y1, x2, y2)[None]  # (1, H, W)
    boxes = _instance_bounding_boxes(mask)
    # The rasterised mask's exclusive bbox equals (x1, y1, x2, y2) for an axis-aligned rectangle.
    assert boxes.tolist() == [[x1, y1, x2, y2]]
    expected = _bbox_tiler_keep(x1, y1, x2, y2, tx, ty, tw, th)
    assert bool(_boxes_intersect_tile(boxes, tx, ty, tw, th)[0]) is expected


def test_instance_bounding_boxes_caches_multiple_instances():
    """Bounding boxes are derived once for a whole instance stack (vectorized)."""
    from getidata.tiling.tilers import _boxes_intersect_tile, _instance_bounding_boxes

    stack = np.stack(
        [
            _mask_from_box(10, 10, 40, 40),
            np.zeros((100, 100), dtype=np.uint8),  # empty -> degenerate box
            _mask_from_box(60, 60, 90, 90),
        ]
    )
    boxes = _instance_bounding_boxes(stack)
    assert boxes.tolist() == [[10, 10, 40, 40], [0, 0, 0, 0], [60, 60, 90, 90]]
    # A single tile check keeps only the first instance for the top-left tile.
    assert _boxes_intersect_tile(boxes, 0, 0, 50, 50).tolist() == [True, False, False]
    assert _boxes_intersect_tile(boxes, 50, 50, 50, 50).tolist() == [False, False, True]


def test_last_image_cache_reuses_and_evicts():
    """The single-slot cache reuses within an image and evicts on image change.

    Tiles are generated grouped by source image, so caching only the last seen
    image captures all reuse while keeping memory bounded to one image.
    """
    from getidata.tiling.tilers import _LastImageCache

    cache: _LastImageCache[str] = _LastImageCache()
    calls = []

    def factory(tag: str):
        def _make() -> str:
            calls.append(tag)
            return tag

        return _make

    # First access for image 0 computes.
    assert cache.get(0, factory("img0-a")) == "img0-a"
    # Repeated access for the same image reuses the cached value (no recompute).
    assert cache.get(0, factory("img0-b")) == "img0-a"
    # Moving to a new image evicts the previous entry and recomputes.
    assert cache.get(1, factory("img1")) == "img1"
    # Returning to image 0 is a miss (single slot only holds the last image).
    assert cache.get(0, factory("img0-c")) == "img0-c"

    assert calls == ["img0-a", "img1", "img0-c"]


def test_instance_mask_tiling_stays_aligned_with_bboxes_and_labels():
    """Instance masks must be filtered in sync with bboxes and labels.

    Regression test: previously ``InstanceMaskTiler`` kept an entry for every
    source instance in every tile while ``BboxTiler``/``LabelTiler`` pruned
    non-overlapping instances, leaving ``len(masks) != len(bboxes) == len(labels)``.
    """
    schema = Schema(
        attributes={
            "image_info": AttributeInfo(type=dict, field=image_info_field()),
            "bboxes": AttributeInfo(type=list, field=bbox_field(dtype=pl.Float64())),
            "labels": AttributeInfo(type=list, field=label_field(is_list=True)),
            "instances": AttributeInfo(type=list, field=instance_mask_field()),
        }
    )

    size = 200
    # Instances placed to fully-contain, straddle, and sit outside tile boundaries at 100.
    specs = [(10, 10, 40, 40), (90, 90, 110, 110), (150, 20, 180, 60), (95, 150, 140, 190)]

    def inst(x1, y1, x2, y2):
        m = np.zeros((size, size), dtype=bool)
        m[y1:y2, x1:x2] = True
        return m

    instances = np.stack([inst(*s) for s in specs])
    bboxes = [[float(v) for v in s] for s in specs]

    polars_schema = schema.attributes["image_info"].field.to_polars_schema("image_info")
    polars_schema.update(schema.attributes["bboxes"].field.to_polars_schema("bboxes"))

    df = pl.DataFrame(
        {
            "image_info": [{"width": size, "height": size}],
            "bboxes": [bboxes],
            "labels": [["a", "b", "c", "a"]],
            "instances": instances.reshape(1, -1),
            "instances_shape": [list(instances.shape)],
        },
        schema={
            **polars_schema,
            "labels": pl.List(pl.Utf8()),
            "instances": pl.List(pl.Boolean()),
            "instances_shape": pl.List(pl.Int32()),
        },
    )

    config = TilingConfig(tile_width=100, tile_height=100)
    plan = _create_tiling_plan(schema, config, threshold_drop_ann=0.0)
    result_df, _ = _apply_tiling(df, None, plan, ["bboxes", "labels", "instances"])

    assert len(result_df) == 4
    for i in range(len(result_df)):
        n_boxes = len(result_df[i, "bboxes"])
        n_labels = len(result_df[i, "labels"])
        n_masks = result_df[i, "instances_shape"][0]
        assert n_boxes == n_labels == n_masks, f"tile {i}: boxes={n_boxes} labels={n_labels} masks={n_masks}"
