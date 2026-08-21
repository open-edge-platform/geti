# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Dataset adapter: wraps a Geti ``VisionDataset`` for ``transformers.Trainer``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from torch.utils.data import Dataset as TorchDataset

if TYPE_CHECKING:
    from collections.abc import Callable

    from getitune.data.dataset.base import VisionDataset
    from getitune.data.entity.sample import BaseSample, SampleBatch


class HFDatasetAdapter(TorchDataset):
    """Wraps a Geti ``VisionDataset`` for ``transformers.Trainer``.

    Unlike the Ultralytics adapter, this one does no per-task reshaping.
    Ultralytics needs that because its trainers expect a bespoke dict shape
    per task; the Geti collate function already produces a task-agnostic
    ``SampleBatch``, and the per-task conversion into HF forward kwargs
    happens in ``HFModel.build_targets``, one level up. So there is nothing
    for ``__getitem__`` to dispatch on here — it just returns the sample
    unchanged, and ``collate_fn`` is the wrapped dataset's own collate
    function, untouched.

    ``task_kind`` is kept anyway, for logging and for the day a task turns
    out to need item-level handling after all.
    """

    def __init__(self, dataset: VisionDataset, task_kind: str) -> None:
        """Wrap *dataset* and pre-warm its augmentation caches.

        Args:
            dataset: The Geti ``VisionDataset`` to wrap.
            task_kind: The Geti task this dataset serves, e.g.
                ``"detection"``. Not currently used to change behaviour.
        """
        self.dataset = dataset
        self.task_kind = task_kind

        # CachedMosaic/CachedMixUp populate a shared cache the first time
        # they see a dataset. DataLoader workers use the spawn context, so
        # without this each worker would rebuild its own fragmented cache
        # instead of inheriting one full, frozen one. Mirrors what
        # DataModule.train_dataloader() already does for Lightning, and what
        # UltralyticsDatasetAdapter does for Ultralytics.
        transforms = getattr(dataset, "transforms", None)
        if hasattr(transforms, "prepare"):
            transforms.prepare(dataset)

    def __len__(self) -> int:
        return len(self.dataset)

    def __getitem__(self, index: int) -> BaseSample:
        return self.dataset[index]

    @property
    def collate_fn(self) -> Callable[[list[BaseSample]], SampleBatch]:
        """The wrapped dataset's own collate function."""
        return self.dataset.collate_fn
