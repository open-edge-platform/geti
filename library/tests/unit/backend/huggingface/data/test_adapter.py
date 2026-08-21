# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for ``HFDatasetAdapter``."""

from __future__ import annotations

from unittest.mock import MagicMock

from getitune.backend.huggingface.data import HFDatasetAdapter
from getitune.data.dataset.base import VisionDataset


def _mock_dataset(with_prepare: bool = False) -> MagicMock:
    dataset = MagicMock(spec=VisionDataset)
    dataset.__len__.return_value = 3
    dataset.__getitem__.side_effect = lambda i: f"sample-{i}"
    if with_prepare:
        dataset.transforms = MagicMock()
    else:
        dataset.transforms = None
    return dataset


def test_len_delegates_to_wrapped_dataset() -> None:
    adapter = HFDatasetAdapter(_mock_dataset(), task_kind="detection")
    assert len(adapter) == 3


def test_getitem_returns_the_sample_unchanged() -> None:
    """No per-task reshaping happens here; the raw Geti sample passes through."""
    adapter = HFDatasetAdapter(_mock_dataset(), task_kind="detection")
    assert adapter[1] == "sample-1"


def test_collate_fn_is_the_wrapped_datasets_own() -> None:
    dataset = _mock_dataset()
    adapter = HFDatasetAdapter(dataset, task_kind="detection")
    assert adapter.collate_fn is dataset.collate_fn


def test_task_kind_is_stored() -> None:
    adapter = HFDatasetAdapter(_mock_dataset(), task_kind="semantic_segmentation")
    assert adapter.task_kind == "semantic_segmentation"


def test_prepare_is_called_when_transforms_support_it() -> None:
    dataset = _mock_dataset(with_prepare=True)
    HFDatasetAdapter(dataset, task_kind="detection")
    dataset.transforms.prepare.assert_called_once_with(dataset)


def test_prepare_is_a_no_op_when_transforms_lack_it() -> None:
    """transforms=None (or anything without .prepare) must not raise."""
    dataset = _mock_dataset(with_prepare=False)
    HFDatasetAdapter(dataset, task_kind="detection")  # would raise if it tried to call .prepare on None
