# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import builtins
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import numpy as np
import pytest
from PIL import Image
from pydantic import ValidationError

from app.models import MediaStorage
from app.models.ome import OmeChannelSetting, OmeChannelSettings, OmeImageMetadata, RgbProjection
from app.services.base import InvalidImageError, ResourceNotFoundError
from app.services.ome.projection import window_channel
from app.services.ome.rendering import (
    InvalidChannelViewError,
    InvalidRenderSelectionError,
    OmeRenderingService,
    composite_channels,
    parse_channel_override,
)

ASSETS = Path(__file__).parents[3] / "assets" / "ome"


@pytest.mark.parametrize(
    ("minimum", "maximum", "values"),
    [(10, 110, [-10, 10, 60, 110, 150]), (-100, 100, [-200, -100, 0, 100, 200])],
)
def test_window_boundaries(minimum, maximum, values):
    np.testing.assert_array_equal(window_channel(np.array(values), minimum, maximum), [0, 0, 127, 255, 255])


def test_window_with_large_finite_range():
    pixels = np.array([-1e308, -5e307, 0, 5e307, 1e308])
    np.testing.assert_array_equal(window_channel(pixels, -1e308, 1e308), [0, 63, 127, 191, 255])


def test_compositing_colors_clipping_and_disabled_channel():
    settings = parse_channel_override("0|0:100$FF0080,1|0:100$FF8000,2|0:100$FFFFFF").settings
    settings[2] = settings[2].model_copy(update={"enabled": False})
    pixels = np.array([[[0, 50, 100]], [[100, 50, 100]], [[100, 100, 100]]])

    np.testing.assert_array_equal(
        composite_channels(pixels, settings),
        [[[255, 128, 0], [254, 63, 63], [255, 128, 128]]],
    )


def test_empty_view_is_rgb_black():
    np.testing.assert_array_equal(composite_channels(np.empty((0, 2, 3)), []), np.zeros((2, 3, 3)))


@pytest.mark.parametrize("pixels", [np.zeros((2, 2)), np.zeros((1, 2, 2)), np.zeros((0, 2, 2), dtype=complex)])
def test_invalid_pixels(pixels):
    with pytest.raises(InvalidImageError):
        composite_channels(pixels, [])


@pytest.mark.parametrize(
    "value",
    [
        "0",
        "0|0:1",
        "0|0:1$FFFFFF,",
        "0|0:1$#FFFFFF",
        "0|0:1$FFFFFG",
        "-1|0:1$FFFFFF",
        "0|1:1$FFFFFF",
        "0|2:1$FFFFFF",
        "0|nan:1$FFFFFF",
        "0|0:inf$FFFFFF",
        "0|0:1$FFFFFF,0|0:1$FF0000",
        "0.5|0:1$FFFFFF",
    ],
)
def test_invalid_channel_override(value):
    with pytest.raises(InvalidChannelViewError):
        parse_channel_override(value)


def test_override_normalizes_colors_and_allows_shared_colors():
    view = parse_channel_override("0|-1.5:2.5$ffffff,1|0:1$ffffff")
    assert [setting.color for setting in view.settings] == ["#FFFFFF", "#FFFFFF"]
    assert view.settings[0].window_min == -1.5
    assert parse_channel_override("").settings == []


@pytest.mark.parametrize(
    "update",
    [
        {"channel": -1},
        {"color": "white"},
        {"window_min": 1},
        {"window_max": -1},
        {"window_min": float("nan")},
        {"window_max": float("inf")},
    ],
)
def test_invalid_setting(update):
    with pytest.raises(ValidationError):
        OmeChannelSetting.model_validate({"channel": 0, "color": "#FFFFFF", "window_min": 0, "window_max": 1, **update})


@pytest.fixture
def rendering(tmp_path):
    source = tmp_path / "source.ome.tiff"
    source.write_bytes((ASSETS / "xyczt.ome.tiff").read_bytes())
    from app.services.ome import OmeReaderRegistry

    storage = MediaStorage(root=source)
    with OmeReaderRegistry().get_reader(storage).open(storage) as handle:
        info = OmeImageMetadata(**handle.info.model_dump(), channel_projection=RgbProjection(channels=()))
    media_service = Mock()
    media_service.get_ome_image_info.return_value = info
    media_service.get_media_storage.return_value = storage
    service = OmeRenderingService(media_service)
    with patch.object(service, "_repository") as repository:
        repository.return_value.get_by_id.return_value = None
        yield service, uuid4(), uuid4(), info


def test_thumbnail_bounds_sampling_at_lowest_level(rendering):
    service, project_id, media_id, info = rendering
    large = info.model_copy(
        update={
            "size_x": 40000,
            "size_y": 30000,
            "pyramid_levels": [
                {"level": 0, "width": 40000, "height": 30000},
                {"level": 1, "width": 20000, "height": 15000},
            ],
        }
    )
    service.media_service.validate_ome_plane_selection.return_value = large
    service.media_service.get_ome_image_info.return_value = large
    handle = MagicMock()
    handle.__enter__.return_value = handle
    handle.read_region.return_value = np.zeros((1, 192, 256), dtype=np.uint16)
    with (
        patch.object(service, "_open_image", return_value=handle),
        patch.object(service, "_get_channel_view", return_value=parse_channel_override("0|0:65535$FFFFFF")),
    ):
        content = service.render_thumbnail(project_id, media_id, z=0, t=0)
    handle.read_region.assert_called_once_with(z=0, t=0, level=1, channels=[0], output_size=(256, 192))
    with Image.open(BytesIO(content)) as thumbnail:
        assert thumbnail.format == "JPEG"
        assert thumbnail.size == (256, 256)


def test_defaults_are_sampled_deterministically_without_creating_db_row(rendering):
    service, project_id, media_id, info = rendering
    with patch.object(service.registry, "get_reader", wraps=service.registry.get_reader) as reader:
        first = service.get_channel_view(project_id, media_id)
        second = service.get_channel_view(project_id, media_id)
    assert first == second
    assert first.is_default
    assert len(first.settings) == info.size_c
    assert all(setting.enabled == (setting.channel < 3) for setting in first.settings)
    assert all(setting.window_min < setting.window_max for setting in first.settings)
    assert reader.call_count == 2
    service._repository.return_value.save.assert_not_called()


def test_render_returns_png_bytes_and_canonical_etag(rendering):
    service, project_id, media_id, _ = rendering
    override = parse_channel_override("0|0:100$ff0000,1|0:100$00ff00")
    selection = service.resolve_render(project_id, media_id, override=override)
    with patch.object(service.registry, "get_reader", wraps=service.registry.get_reader) as reader:
        content = service.render(selection)
        assert service.render(selection) == content
    assert reader.call_count == 2
    reordered = OmeChannelSettings(settings=list(reversed(override.settings)))
    assert service.resolve_render(project_id, media_id, override=reordered).etag == selection.etag
    assert isinstance(content, bytes)
    with Image.open(BytesIO(content)) as image:
        assert image.mode == "RGB"
        assert image.size == (selection.info.size_x, selection.info.size_y)


def test_source_version_changes_etag(rendering):
    service, project_id, media_id, _ = rendering
    override = parse_channel_override("")
    first = service.resolve_render(project_id, media_id, override=override)
    first.storage.root.write_bytes(first.storage.root.read_bytes() + b"\0")
    second = service.resolve_render(project_id, media_id, override=override)
    assert first.etag != second.etag


def test_missing_source_returns_resource_not_found(rendering):
    service, project_id, media_id, _ = rendering
    service.media_service.get_media_storage.return_value.root.unlink()
    with pytest.raises(ResourceNotFoundError, match="payload was not found"):
        service.resolve_render(project_id, media_id, override=parse_channel_override(""))


def test_corrupt_source_reports_invalid_image(rendering):
    service, project_id, media_id, _ = rendering
    service.media_service.get_media_storage.return_value.root.write_bytes(b"not a TIFF")
    with pytest.raises(InvalidImageError, match="no longer readable"):
        service.get_channel_view(project_id, media_id)
    selection = service.resolve_render(project_id, media_id, override=parse_channel_override(""))
    with pytest.raises(InvalidImageError, match="no longer readable"):
        service.render(selection)


@pytest.mark.parametrize("value", [0.0, float("nan"), float("inf")])
def test_constant_or_nonfinite_samples_use_declared_range(rendering, value):
    service, _, _, info = rendering
    reader = Mock()
    handle = MagicMock()
    handle.read_region.return_value = np.full((3, 4, 5), value)
    reader.open.return_value = handle
    handle.__enter__.return_value = handle
    with patch.object(service.registry, "get_reader", return_value=reader):
        view = service._default_view(info, MediaStorage(root=Path("image")))
    assert all((setting.window_min, setting.window_max) == (0, 65535) for setting in view.settings)


def test_default_sampling_is_bounded_and_uses_midplane_lowest_level(rendering):
    service, _, _, info = rendering
    info = info.model_copy(
        update={
            "size_x": 100000,
            "size_y": 80000,
            "size_z": 10,
            "size_t": 8,
            "size_c": 4,
            "pyramid_levels": [{"width": 100000, "height": 80000}, {"width": 10000, "height": 8000}],
            "channels": [],
        }
    )
    reader = Mock()
    handle = MagicMock()
    handle.read_region.return_value = np.tile(np.arange(20, dtype=np.uint16).reshape(1, 4, 5), (3, 1, 1))
    reader.open.return_value = handle
    handle.__enter__.return_value = handle
    storage = MediaStorage(root=Path("image"))
    with patch.object(service.registry, "get_reader", return_value=reader):
        view = service._default_view(info, storage)
    handle.read_region.assert_called_once_with(level=1, z=5, t=4, channels=[0, 1, 2], output_size=(256, 205))
    assert len(view.settings) == 4
    assert not view.settings[3].enabled
    assert (view.settings[0].window_min, view.settings[0].window_max) == tuple(np.percentile(np.arange(20), (1, 99)))
    assert view.settings[3].window_min == 0
    assert view.settings[3].window_max == 65535


@pytest.mark.parametrize(
    "selection", [{"z": -1}, {"z": 1000}, {"t": 1000}, {"level": -1}, {"level": 1000}, {"max_size": 0}]
)
def test_invalid_render_selection(rendering, selection):
    service, project_id, media_id, _ = rendering
    with pytest.raises(InvalidRenderSelectionError):
        service.resolve_render(project_id, media_id, **selection)


def test_out_of_range_channel(rendering):
    service, project_id, media_id, info = rendering
    view = parse_channel_override(f"{info.size_c}|0:100$FFFFFF")
    with pytest.raises(InvalidChannelViewError):
        service.resolve_render(project_id, media_id, override=view)
    with pytest.raises(InvalidChannelViewError):
        service.set_channel_view(project_id, media_id, view)


def test_downsample_uses_reader_output_size_and_distinct_key(rendering):
    service, project_id, media_id, _ = rendering
    view = parse_channel_override("0|0:100$FFFFFF")
    full = service.resolve_render(project_id, media_id, override=view)
    sampled = service.resolve_render(project_id, media_id, override=view, max_size=2)
    assert full.etag != sampled.etag
    with Image.open(BytesIO(service.render(sampled))) as image:
        assert max(image.size) == 2
    assert service.resolve_render(project_id, media_id, override=view, max_size=100).etag == full.etag


@pytest.mark.parametrize("max_size", [None, 16384, 40000])
@pytest.mark.parametrize("override", [None, "", "0|0:100$FFFFFF"])
@pytest.mark.parametrize("dimensions", [(40000, 30000), (16384, 16384)])
def test_oversized_output_is_rejected_before_reading_pixels(rendering, max_size, override, dimensions):
    service, project_id, media_id, info = rendering
    service.media_service.get_ome_image_info.return_value = info.model_copy(
        update={"size_x": dimensions[0], "size_y": dimensions[1], "pyramid_levels": []}
    )
    view = None if override is None else parse_channel_override(override)
    with (
        patch.object(service, "_open_image") as open_image,
        patch.object(service, "_get_channel_view") as get_view,
        pytest.raises(InvalidRenderSelectionError, match="256 MiB.*Use a smaller max_size"),
    ):
        service.resolve_render(project_id, media_id, override=view, max_size=max_size)
    open_image.assert_not_called()
    get_view.assert_not_called()


@pytest.mark.parametrize("channel_count", [0, 1, 3, 64])
def test_render_budget_accepts_boundary_and_rejects_next_pixel(rendering, channel_count):
    service, project_id, media_id, info = rendering
    max_pixels = (256 * 1024 * 1024 - 128 * 1024 * 1024) // (128 + 32 * channel_count)
    view = parse_channel_override(",".join(f"{index}|0:100$FFFFFF" for index in range(channel_count)))
    info = info.model_copy(
        update={"size_x": max_pixels, "size_y": 1, "size_c": max(1, channel_count), "pyramid_levels": []}
    )
    service.media_service.get_ome_image_info.return_value = info
    with patch.object(service, "_open_image") as open_image:
        selection = service.resolve_render(project_id, media_id, override=view)
        assert selection.output_size is None
        service.media_service.get_ome_image_info.return_value = info.model_copy(update={"size_x": max_pixels + 1})
        with pytest.raises(InvalidRenderSelectionError, match="working-memory budget"):
            service.resolve_render(project_id, media_id, override=view)
    open_image.assert_not_called()


def test_disabled_channels_do_not_consume_source_buffer_budget(rendering):
    service, project_id, media_id, info = rendering
    service.media_service.get_ome_image_info.return_value = info.model_copy(
        update={"size_x": 512, "size_y": 512, "size_c": 64, "pyramid_levels": []}
    )
    view = parse_channel_override(",".join(f"{index}|0:100$FFFFFF" for index in range(64)))
    with pytest.raises(InvalidRenderSelectionError, match="64 enabled channels"):
        service.resolve_render(project_id, media_id, override=view)
    view = OmeChannelSettings(
        settings=[setting.model_copy(update={"enabled": setting.channel == 0}) for setting in view.settings]
    )
    selection = service.resolve_render(project_id, media_id, override=view)
    assert len(selection.settings.settings) == 1


@pytest.mark.parametrize("use_level", [False, True])
def test_large_image_can_render_with_safe_downsampling_or_pyramid_level(rendering, use_level):
    service, project_id, media_id, info = rendering
    service.media_service.get_ome_image_info.return_value = info.model_copy(
        update={
            "size_x": 40000,
            "size_y": 30000,
            "pyramid_levels": [{"width": 40000, "height": 30000}, {"width": 512, "height": 384}],
        }
    )
    selection = service.resolve_render(
        project_id,
        media_id,
        override=parse_channel_override("0|0:100$FFFFFF"),
        level=1 if use_level else 0,
        max_size=None if use_level else 512,
    )
    handle = MagicMock()
    handle.__enter__.return_value = handle
    handle.read_region.return_value = np.zeros((1, 384, 512), dtype=np.uint16)
    with patch.object(service, "_open_image", return_value=handle):
        content = service.render(selection)
    handle.read_region.assert_called_once_with(
        z=0, t=0, level=1 if use_level else 0, channels=[0], output_size=None if use_level else (512, 384)
    )
    with Image.open(BytesIO(content)) as image:
        assert image.size == (512, 384)


@pytest.mark.parametrize("output_size", [None, (16384, 16384)])
def test_direct_render_rechecks_budget_before_opening_image(rendering, output_size):
    service, project_id, media_id, info = rendering
    selection = service.resolve_render(project_id, media_id, override=parse_channel_override("0|0:100$FFFFFF"))
    selection = replace(
        selection,
        info=info.model_copy(update={"size_x": 40000, "size_y": 30000, "pyramid_levels": []}),
        output_size=output_size,
    )
    with (
        patch.object(service, "_open_image") as open_image,
        pytest.raises(InvalidRenderSelectionError, match="working-memory budget"),
    ):
        service.render(selection)
    open_image.assert_not_called()


def test_concurrent_renders_return_identical_complete_pngs(rendering):
    service, project_id, media_id, _ = rendering
    selection = service.resolve_render(project_id, media_id, override=parse_channel_override("0|0:100$FFFFFF"))
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: service.render(selection), range(16)))
    assert len(set(results)) == 1
    with Image.open(BytesIO(results[0])) as image:
        image.load()
        assert image.size == (selection.info.size_x, selection.info.size_y)


def test_defaults_and_rendering_never_write_to_filesystem(rendering):
    service, project_id, media_id, _ = rendering
    original_open = builtins.open

    def read_only_open(file, mode="r", *args, **kwargs):
        assert not any(flag in mode for flag in "wax+"), "Rendering must not write files."
        return original_open(file, mode, *args, **kwargs)

    with (
        patch("builtins.open", side_effect=read_only_open),
        patch("io.open", side_effect=read_only_open),
        patch.object(Path, "mkdir", side_effect=AssertionError("Rendering must not create directories.")),
    ):
        service.get_channel_view(project_id, media_id)
        selection = service.resolve_render(project_id, media_id)
        content = service.render(selection)
    with Image.open(BytesIO(content)) as image:
        image.load()
        assert image.size == (selection.info.size_x, selection.info.size_y)
