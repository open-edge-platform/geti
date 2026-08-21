# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""XPU-specific support for the Hugging Face backend.

The Ultralytics backend needed two XPU-specific fixes: periodic memory
clearing, and promoting the loss to fp32 before evaluation because
``tensor.numpy()`` doesn't support bf16. Only the first turned out to apply
here — verified directly, not assumed. A real ``Trainer.evaluate()`` run with
``bf16=True`` on this machine's XPU produced valid metrics with no crash;
``transformers`` already avoids the bf16/numpy problem internally. So there
is no loss-promotion workaround in this module. If a future ``transformers``
version regresses on this, the fix would go here.
"""

from __future__ import annotations

from typing import Any

from transformers import TrainerCallback

from getitune.utils.device import is_xpu_available

__all__ = ["XPUMemoryCallback", "clear_xpu_memory"]


def clear_xpu_memory() -> None:
    """Release cached XPU allocations. A no-op when XPU isn't available."""
    if not is_xpu_available():
        return
    import torch

    torch.xpu.empty_cache()


class XPUMemoryCallback(TrainerCallback):
    """Clears the XPU allocator cache at the end of every epoch.

    Mirrors ``XPUAwareTrainerMixin._clear_memory`` from the Ultralytics
    backend, which exists because ``spawn`` DataLoader workers plus long XPU
    training runs fragment the allocator enough to matter. Cleared once per
    epoch rather than per step: frequent enough to help, infrequent enough
    that the cache-clear itself isn't the bottleneck.
    """

    def on_epoch_end(self, args: Any, state: Any, control: Any, **kwargs: Any) -> None:  # noqa: ANN401
        """Clear the XPU cache."""
        clear_xpu_memory()
