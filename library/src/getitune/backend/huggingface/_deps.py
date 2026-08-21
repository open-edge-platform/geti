# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Optional-dependency gate for the Hugging Face backend.

Importing this module raises :class:`ImportError` unless the ``huggingface``
extra is installed. Every entry point into the backend imports it, so the
``try/except ImportError`` guards in :mod:`getitune.engine.utils.create`,
:mod:`getitune.models`, and :mod:`getitune.types.types` degrade correctly.

``accelerate`` is the discriminating dependency. ``transformers`` is already
present transitively through ``rfdetr``, so checking it alone would not detect
a missing extra.
"""

from __future__ import annotations

_INSTALL_HINT = (
    "The Hugging Face backend requires the 'huggingface' extra. "
    "Install it with: uv sync --extra huggingface  (or: just venv --device <cpu|xpu|cuda>)"
)

try:
    import accelerate
    import transformers
    from transformers.utils import ModelOutput
except ImportError as exc:  # pragma: no cover - exercised via the guards above
    _msg = f"{exc}. {_INSTALL_HINT}"
    raise ImportError(_msg) from exc

#: Resolved versions, useful for diagnostics and version-gated workarounds.
TRANSFORMERS_VERSION: str = transformers.__version__
ACCELERATE_VERSION: str = accelerate.__version__

__all__ = [
    "ACCELERATE_VERSION",
    "TRANSFORMERS_VERSION",
    "ModelOutput",
    "accelerate",
    "transformers",
]
