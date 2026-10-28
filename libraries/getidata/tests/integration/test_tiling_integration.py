from typing import Any

import numpy as np
import polars as pl
import pytest

from getidata.dataset import Dataset, Sample
from getidata.fields import ImageInfo, image_field, image_info_field
from getidata.tiling.tiler_registry import TilingConfig, create_tiling_transform


class TiledSample(Sample):
    """Sample class for tiling tests."""

    image: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8())
    image_info: ImageInfo = image_info_field()


@pytest.fixture
def sample_dataset():
    # Create sample images
    image1 = np.zeros((300, 400, 3), dtype=np.uint8)
    image2 = np.ones((400, 300, 3), dtype=np.uint8)

    # Create samples
    sample1 = TiledSample(image=image1, image_info=ImageInfo(width=400, height=300))
    sample2 = TiledSample(image=image2, image_info=ImageInfo(width=300, height=400))

    # Create dataset
    dataset = Dataset(TiledSample)
    dataset.append(sample1)
    dataset.append(sample2)

    return dataset


def test_dataset_tiling(sample_dataset):
    # Create tiling config
    config = TilingConfig(tile_width=100, tile_height=100, overlap_x=0.2, overlap_y=0.2)

    # Create and apply tiling transform
    tiling_transform = create_tiling_transform(config)
    tiled_dataset = sample_dataset.transform(tiling_transform)

    # Check that we have the expected number of tiles
    # With 100x100 tiles and 20px overlap:
    # Image 1 (300x400): 5x4 grid = 20 tiles
    #   - Width: ceil((400 - 20)/(100 - 20)) = 5 tiles
    #   - Height: ceil((300 - 20)/(100 - 20)) = 4 tiles
    # Image 2 (400x300): 4x5 grid = 20 tiles
    #   - Width: ceil((300 - 20)/(100 - 20)) = 4 tiles
    #   - Height: ceil((400 - 20)/(100 - 20)) = 5 tiles
    assert len(tiled_dataset) == 40

    # Check that we have tile information
    assert "tile" in tiled_dataset.schema.attributes
    assert "image" in tiled_dataset.schema.attributes
    assert "image_info" in tiled_dataset.schema.attributes

    # Verify tile properties
    for item in tiled_dataset:
        # Check tile size constraints
        assert item.tile.width <= config.tile_width
        assert item.tile.height <= config.tile_height

        # Check image data
        assert item.image.shape[:2] == (item.tile.height, item.tile.width)


def test_dataset_tiling_edge_case(sample_dataset):
    # Test with tile size equal to image size
    config = TilingConfig(tile_width=400, tile_height=300)

    # Create and apply tiling transform to first image only
    tiling_transform = create_tiling_transform(config)
    tiled_dataset = sample_dataset.slice(0, 1).transform(tiling_transform)

    # Should have exactly one tile per image
    assert len(tiled_dataset) == 1

    # Verify tiles match original images
    first_tile = tiled_dataset[0]
    assert first_tile.tile.width == 400
    assert first_tile.tile.height == 300
    assert first_tile.tile.x == 0
    assert first_tile.tile.y == 0
