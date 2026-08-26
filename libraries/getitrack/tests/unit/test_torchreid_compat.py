# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Tests for the torchreid tensorboard-import compatibility shim."""

from __future__ import annotations

import importlib.util
import sys
import types

from getitrack.reid._torchreid_compat import ensure_torchreid_importable

_NAME = "torch.utils.tensorboard"


class TestEnsureTorchreidImportable:
    def test_installs_stub_when_tensorboard_absent(self, monkeypatch):
        monkeypatch.delitem(sys.modules, _NAME, raising=False)
        real = importlib.util.find_spec
        monkeypatch.setattr(importlib.util, "find_spec", lambda n: None if n == "tensorboard" else real(n))

        ensure_torchreid_importable()

        assert _NAME in sys.modules
        from torch.utils.tensorboard import SummaryWriter  # resolves via the stub

        assert SummaryWriter is object

    def test_noop_when_tensorboard_available(self, monkeypatch):
        monkeypatch.delitem(sys.modules, _NAME, raising=False)
        real = importlib.util.find_spec
        monkeypatch.setattr(importlib.util, "find_spec", lambda n: object() if n == "tensorboard" else real(n))

        ensure_torchreid_importable()

        # No stub is registered; the real torch.utils.tensorboard would be used.
        assert _NAME not in sys.modules

    def test_noop_when_already_registered(self, monkeypatch):
        sentinel = types.ModuleType(_NAME)
        monkeypatch.setitem(sys.modules, _NAME, sentinel)

        ensure_torchreid_importable()

        assert sys.modules[_NAME] is sentinel
