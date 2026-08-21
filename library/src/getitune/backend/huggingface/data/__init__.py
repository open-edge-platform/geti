# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Data bridge between Geti's Datumaro-backed datasets and the HF backend."""

from .adapter import HFDatasetAdapter

__all__ = ["HFDatasetAdapter"]
