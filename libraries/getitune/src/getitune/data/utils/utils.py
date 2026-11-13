# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Utility functions for the data module."""

from __future__ import annotations

import importlib
import inspect
import logging
import math
from multiprocessing import cpu_count
from typing import TYPE_CHECKING, Any

import numpy as np
import polars as pl
import torch

from getitune.utils.device import is_xpu_available

if TYPE_CHECKING:
    from getidata import Dataset
    from torch.utils.data import Dataset as TorchDataset
    from torch.utils.data import Sampler

    from getitune.config.data import SamplerConfig, TileConfig

logger = logging.getLogger(__name__)

# Adaptive tiling parameters (see ``adapt_tile_config``).
_ADAPTIVE_TILE_OVERLAP = 0.25
_MIN_ADAPTIVE_TILE_SIZE = 400
_ADAPTIVE_TILE_SIZE_MULTIPLE = 32
# Tiling is only useful when the *typical* object appears small in the model input after the
# whole-image resize. If the p50 object edge reaches this fraction of the input edge, skip tiling.
_MIN_OBJECT_EDGE_AT_INPUT_RATIO = 0.125


def instantiate_sampler(sampler_config: SamplerConfig, dataset: TorchDataset, **kwargs) -> Sampler:
    """Instantiate a sampler object based on the provided configuration.

    Args:
        sampler_config (SamplerConfig): The configuration object for the sampler.
        dataset (Dataset): The dataset object to be sampled.
        **kwargs: Additional keyword arguments to be passed to the sampler's constructor.

    Returns:
        Sampler: The instantiated sampler object.
    """
    class_module, class_name = sampler_config.class_path.rsplit(".", 1)
    module = __import__(class_module, fromlist=[class_name])
    sampler_class = getattr(module, class_name)
    init_signature = list(inspect.signature(sampler_class.__init__).parameters.keys())
    if "batch_size" not in init_signature:
        kwargs.pop("batch_size", None)
    # Handle None init_args
    init_args = sampler_config.init_args or {}
    sampler_kwargs = {**init_args, **kwargs}
    return sampler_class(dataset, **sampler_kwargs)


def get_adaptive_num_workers(num_dataloader: int = 1) -> int | None:
    """Measure appropriate num_workers value and return it."""
    num_devices = torch.xpu.device_count() if is_xpu_available() else torch.cuda.device_count()
    if num_devices == 0:
        return None
    return min(cpu_count() // (num_dataloader * num_devices), 8)  # max available num_workers is 8


def import_object_from_module(obj_path: str) -> Any:  # noqa: ANN401
    """Get object from import format string."""
    module_name, obj_name = obj_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, obj_name)


def fill_null_annotation_lists(dm_dataset: Dataset) -> Dataset:
    """Replace ``None`` list-typed annotation columns with empty lists.

    getitune datasets legitimately store ``None`` (rather than an empty list) for
    list-typed annotation fields (e.g. ``labels``, ``bboxes``, ``polygons``) on
    samples with no annotations at all (e.g. background-only images). Datumaro's
    tiling transforms (``LabelTiler``, ``PolygonTiler``, ...) iterate over these
    columns with plain Python loops and don't guard against ``None``, which
    raises ``TypeError: object of type 'NoneType' has no len()`` (or similar)
    when such a sample is tiled. Sanitize the dataframe up front so tiling never
    sees a ``None`` where an (empty) list is expected.

    Only simple scalar ``List`` columns (e.g. ``List(UInt32)`` for labels) are
    filled. Columns whose (possibly nested) inner type is a fixed-size ``Array``
    or ``Struct`` (e.g. ``List(Array(Float32, shape=(4,)))`` for bboxes, or
    ``List(List(Array(Float32, shape=(2,))))`` for polygons) are left unchanged
    because ``fill_null([])`` can corrupt the dtype and because the corresponding
    datumaro tilers (``BboxTiler``, …) already handle ``None`` gracefully via
    Polars expressions.
    """
    try:
        null_list_columns = [
            name
            for name, dtype in dm_dataset.df.schema.items()
            if isinstance(dtype, pl.List) and _is_simple_scalar_list(dtype)
        ]
    except (AttributeError, TypeError):
        # Defensive: don't let sanitization itself break dataset construction for
        # dataset-like objects (e.g. test doubles) that don't expose a real
        # datumaro-backed dataframe.
        return dm_dataset
    if null_list_columns:
        dm_dataset.df = dm_dataset.df.with_columns([pl.col(name).fill_null([]) for name in null_list_columns])
    return dm_dataset


def _is_simple_scalar_list(dtype: pl.List) -> bool:
    """Return True if a ``polars.List`` column holds a simple scalar inner type.

    For ``List(Array(…))`` or ``List(Struct(…))`` columns — including nested cases
    such as ``List(List(Array(…)))`` (e.g. ``polygons``) — ``fill_null([])``
    produces an empty list whose dtype does not round-trip properly through
    Datumaro's schema conversion (empty ``(0,)`` becomes ``(1,0)``). Unwrap any
    level of list nesting before checking the innermost element type.
    """
    inner = dtype.inner
    while isinstance(inner, pl.List):
        inner = inner.inner
    return not isinstance(inner, (pl.Array, pl.Struct))


def adapt_tile_config(tile_config: TileConfig, train_dm_subset: Any, input_size: tuple[int, int] | None = None) -> None:  # noqa: ANN401
    """Adapt the tiling parameters to the training annotations, or disable tiling when it cannot help.

    Called when ``tile_config.enable_tiler`` and ``tile_config.enable_adaptive_tiling`` are both set,
    before the tiled datasets are created. Only the training annotations are inspected; validation
    and test data never influence the tiling parameters.

    The rule uses the fact that, for a tile grid of edge ``s`` with overlap ``o``, any box whose
    larger edge ``L <= o * s`` is fully contained in at least one tile (the overlap region alone
    guarantees it). So:

    - ``overlap`` is fixed to ``_ADAPTIVE_TILE_OVERLAP`` (0.25),
    - the tile edge is ``ceil32(p95(box larger edge) / overlap)``, with a minimum of
      ``_MIN_ADAPTIVE_TILE_SIZE`` so small-object datasets keep the validated default,
    - tiling is disabled (``enable_tiler = False``) when the typical object is already large
      enough in the model input: a typical (p50) object edge of ``L`` in an image of edge ``I``
      becomes ``L * input / I`` after the whole-image resize to ``input_size``, and if that is
      at least ``_MIN_OBJECT_EDGE_AT_INPUT_RATIO`` (0.125) of the input edge, the model sees the
      objects well enough without tiling. This is the typical large-object case (e.g. one
      vehicle filling a 4K frame). The decision is deliberately relative to the model input,
      not the image size, so upscaling or downscaling the dataset does not change it. Tile
      size itself is still derived from the p95 edge so that 95% of the objects fit in a tile.

    Image sizes come from the image-info column; no image is decoded. Datasets without
    ``bboxes``/``polygons`` (classification, semantic segmentation) keep their configured values.

    Args:
        tile_config: Tiling configuration, mutated in place.
        train_dm_subset: Datumaro training subset (``dm_subset.df`` is a polars dataframe).
        input_size: Final model input shape (height, width) after the whole-image resize, if known.
    """
    subset_df = getattr(train_dm_subset, "df", None)
    if subset_df is None:
        logger.warning("Adaptive tiling: subset has no dataframe; keeping the configured tiling parameters.")
        return
    box_format, normalize = _box_format_info(train_dm_subset)
    edges = _collect_object_edges(subset_df, box_format, normalize)
    if edges is None:
        logger.warning(
            "Adaptive tiling: no box or polygon annotations found in the training subset; "
            "keeping the configured tiling parameters."
        )
        return
    tile_size = _adaptive_tile_size(edges)
    image_edge = _median_shorter_image_edge(subset_df)
    p50_edge = float(np.percentile(edges, 50))
    if (
        image_edge is not None
        and input_size is not None
        and _objects_large_enough_at_input(p50_edge, image_edge, input_size)
    ):
        logger.info(
            "Adaptive tiling: the p50 object edge %.1f px already reaches %.0f%% of the model input edge %s "
            "after the whole-image resize (median image edge %s); tiling is disabled.",
            p50_edge,
            _MIN_OBJECT_EDGE_AT_INPUT_RATIO * 100,
            max(input_size),
            image_edge,
        )
        tile_config.enable_tiler = False
        return
    tile_config.tile_size = (tile_size, tile_size)
    tile_config.overlap = _ADAPTIVE_TILE_OVERLAP
    logger.info(
        "Adaptive tiling: tile_size=%s overlap=%s (p50 object edge %.1f px, p95 %.1f px, "
        "median image edge %s, model input %s).",
        tile_size,
        _ADAPTIVE_TILE_OVERLAP,
        p50_edge,
        float(np.percentile(edges, 95)),
        image_edge,
        input_size,
    )


def _objects_large_enough_at_input(p50_edge: float, image_edge: int, input_size: tuple[int, int]) -> bool:
    """Whether the typical object appears big enough in the model input without tiling.

    ``input_size`` is (height, width); the comparison uses the larger input edge and the shorter
    image edge, matching the conservative whole-image resize.
    """
    input_edge = max(input_size)
    object_edge_at_input = p50_edge * input_edge / image_edge
    return object_edge_at_input >= _MIN_OBJECT_EDGE_AT_INPUT_RATIO * input_edge


def _box_format_info(train_dm_subset: Any) -> tuple[str, bool]:  # noqa: ANN401
    """Return the coordinate format and normalization flag of the ``bboxes`` field.

    Defaults to absolute ``x1y1x2y2`` when the subset exposes no schema metadata.
    """
    try:
        field = train_dm_subset.schema.attributes["bboxes"].field
    except (AttributeError, KeyError, TypeError):
        return "x1y1x2y2", False
    return getattr(field, "format", "x1y1x2y2") or "x1y1x2y2", bool(getattr(field, "normalize", False))


def _collect_object_edges(df: Any, box_format: str, normalize: bool) -> np.ndarray | None:  # noqa: ANN401
    """Return the larger box edge for every training annotation (bbox-based, polygon fallback), or ``None``.

    The larger edge is what the containment rule needs: a box is fully contained in some tile iff
    its larger edge fits within the overlap. Samples without annotations contribute nothing.

    Args:
        df: Polars dataframe of the training subset.
        box_format: Coordinate format of the ``bboxes`` column (``x1y1x2y2``, ``cxcywh`` or ``xywh``).
        normalize: Whether box coordinates are normalized to the image size.
    """
    info_column = next((name for name in ("dm_image_info", "image_info") if name in df.schema), None)
    if normalize and info_column is None:
        logger.warning(
            "Adaptive tiling: normalized boxes without image size info; keeping the configured tiling parameters."
        )
        return None
    image_sizes: list[dict[str, Any]] = df[info_column].to_list() if info_column is not None else []

    edge_values: list[np.ndarray] = []
    if "bboxes" in df.schema:
        for index, boxes in enumerate(df["bboxes"].to_list()):
            if boxes is None or len(boxes) == 0:
                continue
            arr = np.asarray(boxes, dtype=np.float64).reshape(-1, 4)
            if box_format == "x1y1x2y2":
                widths = np.clip(arr[:, 2] - arr[:, 0], 0.0, None)
                heights = np.clip(arr[:, 3] - arr[:, 1], 0.0, None)
            elif box_format in ("cxcywh", "xywh"):
                widths, heights = arr[:, 2].copy(), arr[:, 3].copy()
            else:
                logger.warning(
                    "Adaptive tiling: unsupported box format '%s'; keeping the configured tiling parameters.",
                    box_format,
                )
                return None
            if normalize and len(image_sizes):
                size = image_sizes[index]
                widths = widths * size["width"]
                heights = heights * size["height"]
            edge_values.append(np.maximum(widths, heights))
    elif "polygons" in df.schema:
        if normalize:
            logger.warning(
                "Adaptive tiling: normalized polygons are not supported; keeping the configured tiling parameters."
            )
            return None
        for polygons in df["polygons"].to_list():
            if polygons is None or len(polygons) == 0:
                continue
            points = np.concatenate([np.asarray(p, dtype=np.float64).reshape(-1, 2) for p in polygons])
            widths = points[:, 0].max() - points[:, 0].min()
            heights = points[:, 1].max() - points[:, 1].min()
            edge_values.append(np.array(max(widths, heights, 0.0)))
    if not edge_values:
        return None
    return np.concatenate(edge_values)


def _adaptive_tile_size(edges: np.ndarray) -> int:
    """Compute the tile edge from the object-edge distribution."""
    p95_edge = float(np.percentile(edges, 95))
    raw = p95_edge / _ADAPTIVE_TILE_OVERLAP
    # Tolerate float32 rounding noise so an exact multiple of 32 stays put instead of rounding up.
    tolerance = max(1e-6, abs(raw) * 1e-6)
    tile = math.ceil((raw - tolerance) / _ADAPTIVE_TILE_SIZE_MULTIPLE) * _ADAPTIVE_TILE_SIZE_MULTIPLE
    return max(tile, _MIN_ADAPTIVE_TILE_SIZE)


def _median_shorter_image_edge(df: Any) -> int | None:  # noqa: ANN401
    """Return the median of the shorter image edge, from the image-info column."""
    info_column = next((name for name in ("dm_image_info", "image_info") if name in df.schema), None)
    if info_column is None:
        return None
    infos = df[info_column].to_list()
    edges = [min(info["width"], info["height"]) for info in infos if info is not None]
    if not edges:
        return None
    return int(np.median(edges))
