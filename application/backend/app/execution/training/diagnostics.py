# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Verbose diagnostic helpers for the training pipeline.

NOTE
----
This module is intentionally *very* verbose and exists purely to help diagnose
runtime issues (hangs, slow steps, OOM / ``DataLoader worker exited
unexpectedly`` crashes, shared-memory exhaustion, ...). It is meant to live in a
throwaway diagnostic commit and is **not** intended to be merged to master.

Everything here is defensive: diagnostics must never break or slow down the
pipeline, so all collectors swallow their own exceptions and log at ``DEBUG``.
"""

from __future__ import annotations

import os
import shutil
import time
from contextlib import contextmanager
from typing import TYPE_CHECKING

import psutil
from loguru import logger

if TYPE_CHECKING:
    from collections.abc import Iterator


def fmt_bytes(num: float) -> str:
    """Return a human-readable representation of a byte count."""
    value = float(num)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(value) < 1024.0:
            return f"{value:3.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} PiB"


def log_system_resources(context: str) -> None:
    """Log a snapshot of process + system resource usage.

    Captures the metrics most useful for diagnosing training-pipeline failures:

    - process RSS / VMS memory and system memory availability (OOM),
    - ``/dev/shm`` usage (DataLoader worker shared-memory transfers),
    - CPU load,
    - open file descriptors, thread count and number of child processes
      (leaked workers / descriptor exhaustion).

    Args:
        context: Short label identifying where the snapshot was taken.
    """
    try:
        proc = psutil.Process()
        with proc.oneshot():
            mem = proc.memory_info()
            num_fds = proc.num_fds() if hasattr(proc, "num_fds") else -1
            num_threads = proc.num_threads()
            num_children = len(proc.children(recursive=True))
        vm = psutil.virtual_memory()
        logger.debug(
            "[diag:{}] proc RSS={} VMS={} | sys mem used={} avail={} ({:.1f}%) | "
            "cpu={:.1f}% | fds={} threads={} children={}",
            context,
            fmt_bytes(mem.rss),
            fmt_bytes(mem.vms),
            fmt_bytes(vm.used),
            fmt_bytes(vm.available),
            vm.percent,
            psutil.cpu_percent(interval=None),
            num_fds,
            num_threads,
            num_children,
        )
        log_shared_memory_usage(context)
    except Exception as exc:  # diagnostics must never break the pipeline
        logger.debug("[diag:{}] failed to collect system resources: {}", context, exc)


def log_shared_memory_usage(context: str) -> None:
    """Log ``/dev/shm`` capacity and usage.

    ``/dev/shm`` is the tmpfs used by PyTorch DataLoader workers to hand batches
    back to the main process. In containers it is often small (e.g. 64 MiB);
    overflowing it surfaces as ``DataLoader worker (pid(s) ...) exited
    unexpectedly``, so tracking it around data loading is invaluable.
    """
    try:
        usage = shutil.disk_usage("/dev/shm")  # noqa: S108 - reading tmpfs usage, not creating a temp file
    except FileNotFoundError:
        logger.debug("[diag:{}] /dev/shm not present", context)
        return
    except Exception as exc:
        logger.debug("[diag:{}] failed to read /dev/shm usage: {}", context, exc)
        return
    logger.debug(
        "[diag:{}] /dev/shm total={} used={} free={} ({:.1f}% used)",
        context,
        fmt_bytes(usage.total),
        fmt_bytes(usage.used),
        fmt_bytes(usage.free),
        (usage.used / usage.total * 100.0) if usage.total else 0.0,
    )


def log_gpu_memory(context: str) -> None:
    """Log CUDA memory usage per visible device, when torch + CUDA are available."""
    try:
        import torch

        if not torch.cuda.is_available():
            logger.debug("[diag:{}] CUDA not available", context)
            return
        for i in range(torch.cuda.device_count()):
            free, total = torch.cuda.mem_get_info(i)
            logger.debug(
                "[diag:{}] cuda:{} '{}' free={} total={} allocated={} reserved={}",
                context,
                i,
                torch.cuda.get_device_name(i),
                fmt_bytes(free),
                fmt_bytes(total),
                fmt_bytes(torch.cuda.memory_allocated(i)),
                fmt_bytes(torch.cuda.memory_reserved(i)),
            )
    except Exception as exc:
        logger.debug("[diag:{}] failed to collect GPU memory: {}", context, exc)


def log_environment(context: str, keys: tuple[str, ...] = ()) -> None:
    """Log selected environment variables relevant to training/runtime behaviour."""
    default_keys = (
        "CUDA_VISIBLE_DEVICES",
        "PRETRAINED_WEIGHTS_CACHE_DIR",
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "PYTORCH_CUDA_ALLOC_CONF",
    )
    for key in keys or default_keys:
        logger.debug("[diag:{}] env {}={}", context, key, os.environ.get(key, "<unset>"))


@contextmanager
def log_duration(label: str, *, resources: bool = False, gpu: bool = False) -> Iterator[None]:
    """Context manager logging the wall-clock duration of a code block.

    Args:
        label: Human-readable label for the block.
        resources: When True, snapshot system resources before and after.
        gpu: When True, snapshot GPU memory before and after.
    """
    if resources:
        log_system_resources(f"{label}:before")
    if gpu:
        log_gpu_memory(f"{label}:before")
    logger.debug("[diag] ⏱ start: {}", label)
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        logger.debug("[diag] ⏱ done: {} in {:.3f}s", label, elapsed)
        if resources:
            log_system_resources(f"{label}:after")
        if gpu:
            log_gpu_memory(f"{label}:after")


def describe_dataloader(loader: object) -> str:
    """Best-effort one-line description of a DataLoader's key settings.

    Useful for confirming batch size / worker / pin-memory settings actually in
    effect for a given subset (e.g. the tiled-eval safe settings).
    """
    attrs = ("batch_size", "num_workers", "pin_memory", "persistent_workers", "prefetch_factor")
    parts = []
    for attr in attrs:
        if hasattr(loader, attr):
            parts.append(f"{attr}={getattr(loader, attr)!r}")
    dataset = getattr(loader, "dataset", None)
    if dataset is not None:
        parts.append(f"dataset={type(dataset).__name__}")
        try:
            parts.append(f"num_items={len(dataset)}")  # type: ignore[arg-type]
        except TypeError:
            pass
    return ", ".join(parts)
