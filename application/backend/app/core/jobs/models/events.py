# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ExecutionEvent:
    pass


@dataclass(frozen=True, slots=True)
class Started(ExecutionEvent):
    pass


@dataclass(frozen=True, slots=True)
class Progress(ExecutionEvent):
    message: str
    value: float  # percentage of completion (0.0, 100.0]
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class Heartbeat(ExecutionEvent):
    """Liveness signal emitted while a long-running, non-instrumented operation is in progress.

    Some operations (e.g. NNCF accuracy-aware quantization) can legitimately run for a long time
    without producing any structured progress updates. Emitting a ``Heartbeat`` lets the job control
    plane know the job is still alive and actively working, without changing its message or
    percentage of completion, so it isn't mistakenly killed by the stale-job monitor.
    """


@dataclass(frozen=True, slots=True)
class Done(ExecutionEvent):
    pass


@dataclass(frozen=True, slots=True)
class Cancelled(ExecutionEvent):
    pass


@dataclass(frozen=True, slots=True)
class Failed(ExecutionEvent):
    details: str
