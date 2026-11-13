# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for adaptive tiling parameter computation."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import polars as pl

if TYPE_CHECKING:
    import pytest


from getitune.config.data import TileConfig
from getitune.data.utils import adapt_tile_config


def _schema_with_bboxes(box_format: str = "x1y1x2y2", normalize: bool = False) -> Any:  # noqa: ANN401
    """Mimic the datumaro schema: ``subset.schema.attributes["bboxes"].field``."""
    return SimpleNamespace(
        attributes={
            "bboxes": SimpleNamespace(field=SimpleNamespace(format=box_format, normalize=normalize)),
        },
    )


def make_dm_subset(
    boxes: list[list[list[float]]],
    sizes: list[tuple[int, int]] | None = None,
    box_format: str = "x1y1x2y2",
    normalize: bool = False,
    info_column: str = "dm_image_info",
) -> Any:  # noqa: ANN401
    """Build a subset-like object mimicking ``dm_subset.df`` of the datumaro detection schema.

    ``boxes`` holds per-sample boxes in ``box_format``; ``sizes`` optional (width, height) per sample.
    """
    data: dict[str, pl.Series] = {
        "bboxes": pl.Series(boxes, dtype=pl.List(pl.Array(pl.Float32, 4))),
    }
    if sizes is not None:
        data[info_column] = pl.Series(
            [{"width": w, "height": h} for w, h in sizes],
            dtype=pl.Struct({"width": pl.Int32, "height": pl.Int32}),
        )
    return SimpleNamespace(df=pl.DataFrame(data), schema=_schema_with_bboxes(box_format, normalize))


class TestAdaptTileConfig:
    """Tests for ``adapt_tile_config``."""

    def test_small_objects_keep_default_tile(self) -> None:
        # p95 object edge 80 -> tile ceil32(80/0.25)=320 -> min 400 keeps the validated default.
        # (32*12=384 < 400, so the minimum wins.)
        subset_df = make_dm_subset([[[10, 10, 90, 90]]] * 20, sizes=[(1360, 765)] * 20)
        tile_config = TileConfig(enable_tiler=True, tile_size=(400, 400), overlap=0.2)

        adapt_tile_config(tile_config, subset_df)

        assert tile_config.enable_tiler is True
        assert tile_config.tile_size == (400, 400)
        assert tile_config.overlap == 0.25

    def test_mid_size_objects_enlarge_tile(self) -> None:
        # p50 larger edge 400 on a 4000px image, input 640: 400*640/4000=64 < 80 -> tiled.
        subset_df = make_dm_subset([[[0, 0, 400, 200]]] * 20, sizes=[(4000, 4000)] * 20)
        tile_config = TileConfig(enable_tiler=True, tile_size=(400, 400), overlap=0.2)

        adapt_tile_config(tile_config, subset_df, input_size=(640, 640))

        assert tile_config.tile_size == (1600, 1600)
        assert tile_config.overlap == 0.25

    def test_typical_objects_large_at_input_disable_tiling(self) -> None:
        # Human at ~215px of a 1280x720 image, input 640: 215*640/720=190 >= 80 -> no tiling.
        subset_df = make_dm_subset([[[0, 0, 100, 215]]] * 20, sizes=[(1280, 720)] * 20)
        tile_config = TileConfig(enable_tiler=True, tile_size=(400, 400))

        adapt_tile_config(tile_config, subset_df, input_size=(640, 640))

        assert tile_config.enable_tiler is False

    def test_input_size_unknown_falls_back_to_tiling(self) -> None:
        # Without input_size the on/off gate cannot run; tiling stays on with the computed size.
        subset_df = make_dm_subset([[[0, 0, 100, 215]]] * 20, sizes=[(1280, 720)] * 20)
        tile_config = TileConfig(enable_tiler=True, tile_size=(400, 400))

        adapt_tile_config(tile_config, subset_df)

        assert tile_config.enable_tiler is True
        assert tile_config.tile_size == (864, 864)  # ceil32(215/0.25)

    def test_huge_objects_disable_tiling(self) -> None:
        # Vehicle-like: p50 edge 3500 on 4160, input 640: 3500*640/4160=538 >= 80 -> no tiling.
        subset_df = make_dm_subset([[[100, 100, 2600, 3500]]] * 20, sizes=[(4160, 4160)] * 20)
        tile_config = TileConfig(enable_tiler=True, tile_size=(400, 400))

        adapt_tile_config(tile_config, subset_df, input_size=(640, 640))

        assert tile_config.enable_tiler is False

    def test_no_annotations_keep_config(self) -> None:
        subset_df = make_dm_subset([[]] * 3, sizes=[(1000, 1000)] * 3)
        tile_config = TileConfig(enable_tiler=True, tile_size=(512, 512), overlap=0.4)

        adapt_tile_config(tile_config, subset_df)

        assert tile_config.tile_size == (512, 512)
        assert tile_config.overlap == 0.4
        assert tile_config.enable_tiler is True

    def test_no_image_info_skips_gate(self) -> None:
        # Without dm_image_info the on/off gate cannot run; tiling stays on with the computed size.
        subset_df = make_dm_subset([[[0, 0, 400, 200]]] * 20)
        tile_config = TileConfig(enable_tiler=True, tile_size=(400, 400))

        adapt_tile_config(tile_config, subset_df)

        assert tile_config.tile_size == (1600, 1600)

    def test_missing_dataframe_keeps_config(self, caplog: pytest.LogCaptureFixture) -> None:
        tile_config = TileConfig(enable_tiler=True)

        adapt_tile_config(tile_config, object())

        assert tile_config.enable_tiler is True
        assert any("no dataframe" in message for message in caplog.messages)

    def test_cxcywh_boxes_are_interpreted_as_size(self) -> None:
        # YOLO-style import: [cx, cy, w, h] absolute. Larger edge 92 -> tile min 400.
        subset_df = make_dm_subset([[[898, 618, 54, 92]]] * 20, sizes=[(1360, 765)] * 20, box_format="cxcywh")
        tile_config = TileConfig(enable_tiler=True)

        adapt_tile_config(tile_config, subset_df)

        assert tile_config.tile_size == (400, 400)

    def test_cxcywh_huge_boxes_disable_tiling(self) -> None:
        # Vehicle-like: 3100px object edge on a 4160px image, input 640 -> 477 >= 80 -> no tiling.
        subset_df = make_dm_subset([[[2080, 2080, 3100, 3100]]] * 20, sizes=[(4160, 4160)] * 20, box_format="cxcywh")
        tile_config = TileConfig(enable_tiler=True)

        adapt_tile_config(tile_config, subset_df, input_size=(640, 640))

        assert tile_config.enable_tiler is False

    def test_normalized_boxes_scale_by_image_size(self) -> None:
        # Normalized cxcywh: w,h are fractions; 0.1 of a 1600px edge -> larger edge 160 -> tile 640.
        subset_df = make_dm_subset(
            [[[0.5, 0.5, 0.1, 0.1]]] * 20, sizes=[(1600, 1600)] * 20, box_format="cxcywh", normalize=True
        )
        tile_config = TileConfig(enable_tiler=True)

        adapt_tile_config(tile_config, subset_df)

        assert tile_config.tile_size == (640, 640)

    def test_raw_image_info_column_is_used(self) -> None:
        # The raw import uses "image_info"; the datumaro-converted one "dm_image_info". Both work.
        subset_df = make_dm_subset(
            [[[100, 100, 2600, 3600]]] * 20,
            sizes=[(4160, 4160)] * 20,
            info_column="image_info",
        )
        tile_config = TileConfig(enable_tiler=True)

        adapt_tile_config(tile_config, subset_df, input_size=(640, 640))

        assert tile_config.enable_tiler is False

    def test_unsupported_box_format_keeps_config(self, caplog: pytest.LogCaptureFixture) -> None:
        subset_df = make_dm_subset([[[10, 10, 90, 90]]] * 20, box_format="cxcywhr")
        tile_config = TileConfig(enable_tiler=True, tile_size=(400, 400))

        adapt_tile_config(tile_config, subset_df)

        assert tile_config.tile_size == (400, 400)
        assert any("unsupported box format" in message for message in caplog.messages)

    def test_all_adaptive_fields_set_together(self) -> None:
        subset_df = make_dm_subset([[[0, 0, 100, 100]]] * 4, sizes=[(1280, 960)] * 4)
        tile_config = TileConfig(enable_tiler=True, tile_size=(400, 400), overlap=0.2)

        adapt_tile_config(tile_config, subset_df)

        # 100/0.25 = 400, but 400 is not a multiple of 32, so ceil -> 416.
        assert tile_config.tile_size == (416, 416)
        assert tile_config.overlap == 0.25
