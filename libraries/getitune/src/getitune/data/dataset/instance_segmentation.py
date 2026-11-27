# Copyright (C) 2025-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Module for InstanceSegDataset."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from getidata.fields import PolygonField

from getitune import LabelInfo
from getitune.data.augmentation.pipeline import CPUAugmentationPipeline, _IntensityAdapter
from getitune.data.augmentation.transforms import CachedMosaic, Resize
from getitune.data.dataset.base import Transforms, VisionDataset
from getitune.data.entity.sample import InstanceSegmentationPolygonSample, InstanceSegmentationSample
from getitune.data.entity.utils import with_image_dtype
from getitune.types import TaskType

if TYPE_CHECKING:
    from getidata import Dataset

logger = logging.getLogger(__name__)


class InstanceSegDataset(VisionDataset):
    """Dataset class for instance segmentation tasks in getitune.

    This class handles loading images and their masks.

    Args:
        dm_subset (DmDataset): The subset of the dataset to use.
        transforms (Transforms, optional): Data transformations to be applied.
        task_type (TaskType, optional): The task type. Defaults to INSTANCE_SEGMENTATION.
        max_refetch (int, optional): Maximum number of times to refetch data. Defaults to 1000.
        storage_dtype (str): Storage dtype for image data (e.g. "uint8", "float32"). Defaults to "uint8".

    """

    def __init__(
        self,
        dm_subset: Dataset,
        transforms: Transforms | None = None,
        task_type: TaskType = TaskType.INSTANCE_SEGMENTATION,
        max_refetch: int = 1000,
        storage_dtype: str = "uint8",
    ) -> None:
        sample_type = with_image_dtype(InstanceSegmentationSample, storage_dtype)
        # Kept until ``use_polygons``: the converted subset has no polygons any more.
        self._source_dm_subset: Dataset | None = dm_subset
        self._storage_dtype = storage_dtype
        self.rasterize_polygons = False
        self._mask_resize: Resize | CachedMosaic | None = None
        dm_subset = dm_subset.convert_to_schema(sample_type)
        super().__init__(
            dm_subset=dm_subset,
            transforms=transforms,
            max_refetch=max_refetch,
        )

        labels = list(dm_subset.label_categories.labels)  # type: ignore[missing-attribute]
        self.label_info = LabelInfo(
            label_names=labels,
            label_groups=[labels],
            label_ids=[str(i) for i in range(len(labels))],
        )
        self._task_type = task_type
        # Plain-resize pipelines shrink the masks right away: rasterize them at that size, not at full image size.
        if (resize := self._first_resize()) is not None:
            self.use_polygons(mask_resize=resize)

    def _first_resize(self) -> Resize | CachedMosaic | None:
        """Return the first spatial transform if it resizes (and pads) masks itself: ``Resize`` or ``CachedMosaic``."""
        if not isinstance(self.transforms, CPUAugmentationPipeline):
            return None
        for aug in self.transforms.augmentations:
            if isinstance(aug, _IntensityAdapter):
                continue
            if isinstance(aug, CachedMosaic) or (isinstance(aug, Resize) and aug.resize_targets):
                return aug
            return None
        return None

    def use_polygons(self, mask_resize: Resize | CachedMosaic | None = None) -> bool:
        """Read samples from polygons and rasterize masks per sample, instead of from stored full-size masks.

        Tiling needs this: a tile's masks must come from the tile's own clipped polygons. Rasterizing each
        instance at full image size first costs gigabytes for a 20 MP image with a few hundred instances.

        Args:
            mask_resize: Rasterize masks at the size this transform gives the image content (before padding) instead
                of the image size. Tiling leaves it unset: tiles are already small.

        Returns:
            bool: True when the dataset now reads polygons; False (nothing changed) when the source has none.
        """
        self._mask_resize = mask_resize
        source = self._source_dm_subset
        if source is None:
            return self.rasterize_polygons
        if not any(isinstance(attr.field, PolygonField) for attr in source.schema.attributes.values()):
            return False
        try:
            self.dm_subset = source.convert_to_schema(
                with_image_dtype(InstanceSegmentationPolygonSample, self._storage_dtype)
            )
        except Exception:
            logger.warning("Cannot read polygons from this dataset; instance masks are used as stored.", exc_info=True)
            return False
        self._source_dm_subset = None
        self.rasterize_polygons = True
        return True

    def _read_dm_item(self, index: int) -> InstanceSegmentationSample:
        item = super()._read_dm_item(index)
        if not self.rasterize_polygons:
            return item  # pyrefly: ignore[bad-return]
        mask_size = None
        if self._mask_resize is not None:
            info = item.dm_image_info  # pyrefly: ignore[missing-attribute]
            mask_size = self._mask_resize.mask_content_size(info.height, info.width)
        return item.to_instance_segmentation_sample(mask_size=mask_size)  # pyrefly: ignore[missing-attribute]

    def get_idx_list_per_classes(self, use_string_label: bool = False) -> dict[int | str, list[int]]:
        """Get a dictionary mapping class labels (string or int) to lists of samples.

        Args:
            use_string_label (bool): If True, use string class labels as keys.
                If False, use integer indices as keys.
        """
        idx_list_per_classes: dict[int | str, list[int]] = {}
        for idx in range(len(self)):
            item = self.dm_subset[idx]
            labels = item.label.tolist()
            if use_string_label:
                labels = [self.label_info.label_names[label] for label in labels]
            for label in labels:
                if label not in idx_list_per_classes:
                    idx_list_per_classes[label] = []
                idx_list_per_classes[label].append(idx)
        return idx_list_per_classes

    @property
    def task_type(self) -> TaskType:
        """Getitune Task Type for the dataset.

        Returns:
            TaskType: The instance segmentation task type.
        """
        return self._task_type
