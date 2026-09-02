# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Compatibility shim for importing torchreid without its training-only deps.

torchreid 0.2.5 eagerly imports ``torch.utils.tensorboard`` at package load (for
its training engine), which in turn requires the heavy ``tensorboard`` package.
The tracking library only ever runs ReID inference, so this stubs the module when
the real one is absent, letting torchreid import without ``tensorboard`` installed.
"""

from __future__ import annotations

import importlib.util
import sys
import types


def ensure_torchreid_importable() -> None:
    """Install a stub ``torch.utils.tensorboard`` when the real module is missing.

    A no-op when ``tensorboard`` is installed (the real module is used) or when a
    stub is already registered. Must be called before importing torchreid.
    """
    name = "torch.utils.tensorboard"
    if name in sys.modules or importlib.util.find_spec("tensorboard") is not None:
        return
    importlib.import_module("torch.utils")  # ensure the parent package is initialised
    stub = types.ModuleType(name)
    # torchreid's engine imports SummaryWriter but never instantiates it for
    # inference; a placeholder is enough to satisfy the import.
    stub.__dict__["SummaryWriter"] = object
    sys.modules[name] = stub
