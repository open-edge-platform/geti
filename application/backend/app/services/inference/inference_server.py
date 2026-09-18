# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

from loguru import logger

from app.db import get_db_session
from app.models import BatchInferenceInput, DatasetItemAnnotation, Label
from app.models.inference import InferenceModel, InferenceState, InferenceStatus
from app.models.model_revision import ModelFormat, ModelPrecision
from app.models.system import DeviceInfo
from app.services.base import ResourceNotFoundError, ResourceType
from app.services.data_collect.prediction_converter import convert_prediction

from .model_loader import ModelLoader
from .model_registry import EntryState, ModelCacheEntry

if TYPE_CHECKING:
    from model_api.models import Model

LOCK_ACQUIRE_TIMEOUT = 30  # seconds
RETRY_INTERVAL = 0.05  # seconds, sleep between spin-retries
CONFIDENCE_THRESHOLD_PARAM = "confidence_threshold"  # defined in 'model_api/models/parameters.py'


class InferenceBusyError(Exception):
    """
    Exception raised when an inference request is made while the server is busy loading a model or performing inference.
    """

    def __init__(self):
        super().__init__(
            "Inference request timed out waiting for the model lock. Another inference is in "
            "progress or model is not loaded yet."
        )


@dataclass(frozen=True)
class _ResolvedVariant:
    """Outcome of resolving a model variant against the database."""

    variant_id: UUID
    xml_path: Path
    size_bytes: int


class InferenceServer:
    """
    Inference Server manages the lifecycle of the models used for inference.

    It keeps a small LRU cache of loaded models (at most `max_models`, and, best-effort, within `max_memory`
    bytes of estimated memory), loads them on demand, and evicts them once they are no longer needed: either
    because the cache is full or because they have been idle for longer than `model_ttl` seconds.

    Cache entries are keyed by `(model_id, variant_id)`; requesting an already cached model on a different
    device unloads and reloads it. Inference on different models runs in parallel, while inference on a single
    model is serialized, since Model API objects are not safe for concurrent mutation.
    """

    def __init__(
        self,
        data_dir: Path,
        max_models: int = 1,
        max_memory: int | None = None,
        memory_overhead_factor: float = 1.5,
        model_ttl: int = 60,
    ) -> None:
        """
        Args:
            data_dir: Root directory holding the model files.
            max_models: Maximum number of models kept loaded at the same time.
            max_memory: Approximate upper bound, in bytes, on the memory used by the loaded models.
                None means unlimited. The limit never prevents loading a model when it would be the only one.
            memory_overhead_factor: Multiplier applied to a model's on-disk size to estimate its memory footprint.
            model_ttl: Time-to-live, in seconds, of an idle model before it is evicted.
        """
        self._data_dir = data_dir
        self._max_models = max_models
        self._max_memory = max_memory
        self._memory_overhead_factor = memory_overhead_factor
        self._model_ttl = model_ttl
        self._entries: list[ModelCacheEntry] = []  # MRU-ordered
        self._deleted_models: set[tuple[UUID, UUID]] = set()
        self._pending_unloads: list[ModelCacheEntry] = []
        self._registry_lock = threading.Lock()

    # --- registry primitives, called with `self._registry_lock` held ---

    def _find(self, model_id: UUID, variant_id: UUID) -> ModelCacheEntry | None:
        """Return the cached entry for the given model variant, or None."""
        for entry in self._entries:
            if entry.model_id == model_id and entry.variant_id == variant_id:
                return entry
        return None

    def _touch(self, entry: ModelCacheEntry) -> None:
        """Move an entry to the MRU front of the cache and refresh its idle timer."""
        entry.last_used = time.monotonic()
        if entry in self._entries:
            self._entries.remove(entry)
            self._entries.insert(0, entry)

    @staticmethod
    def _deleted_model_error(model_id: UUID) -> ResourceNotFoundError:
        """Build the not-found error raised when a deleted model is requested or finishes loading late."""
        return ResourceNotFoundError(ResourceType.MODEL, str(model_id))

    def _drop(self, entry: ModelCacheEntry) -> None:
        """Remove an entry from the cache and mark it evicted. The caller must unload it outside the lock."""
        if entry in self._entries:
            self._entries.remove(entry)
        entry.state = EntryState.EVICTED

    def _insert(
        self, project_id: UUID, model_id: UUID, resolved: _ResolvedVariant, device: DeviceInfo
    ) -> ModelCacheEntry:
        """Insert a new LOADING entry, already leased by the caller, at the MRU front of the cache."""
        entry = ModelCacheEntry(
            project_id=project_id,
            model_id=model_id,
            variant_id=resolved.variant_id,
            device=device,
            xml_path=resolved.xml_path,
            size_bytes=resolved.size_bytes,
            state=EntryState.LOADING,
            refcount=1,
        )
        self._entries.insert(0, entry)
        return entry

    # --- lease and unload helpers, taking the lock internally ---

    def _release(self, entry: ModelCacheEntry) -> None:
        """Release a lease previously taken by `_acquire`."""
        unload_later = False
        with self._registry_lock:
            entry.refcount -= 1
            if entry in self._entries:
                self._touch(entry)
            else:
                entry.last_used = time.monotonic()
            unload_later = entry.refcount == 0 and entry.state is EntryState.EVICTED and entry.handle is not None
        if unload_later:
            with self._registry_lock:
                if entry not in self._pending_unloads:
                    self._pending_unloads.append(entry)

    def _unload(self, entry: ModelCacheEntry) -> None:
        """Unload the model held by an entry that has already been dropped from the cache."""
        handle = entry.handle
        if handle is None:
            return
        logger.info("Unloading model {} (variant {}) from device {}", entry.model_id, entry.variant_id, entry.device)
        try:
            ModelLoader.unload(handle)
        except Exception:
            with self._registry_lock:
                if entry not in self._pending_unloads:
                    self._pending_unloads.append(entry)
            raise
        entry.handle = None

    def invalidate_model(self, project_id: UUID, model_id: UUID) -> None:
        """Invalidate every cached variant of a deleted model revision."""
        to_unload: list[ModelCacheEntry] = []
        with self._registry_lock:
            self._deleted_models.add((project_id, model_id))
            for entry in list(self._entries):
                if entry.project_id != project_id or entry.model_id != model_id:
                    continue
                self._drop(entry)
                if entry.handle is not None and entry.refcount == 0:
                    to_unload.append(entry)
        first_error: BaseException | None = None
        for entry in to_unload:
            try:
                self._unload(entry)
            except BaseException as exc:
                if first_error is None:
                    first_error = exc
        if first_error is not None:
            raise first_error

    def _wait_ready(self, entry: ModelCacheEntry, deadline: float) -> ModelCacheEntry | None:
        """
        Wait for a leased entry to become READY.

        Args:
            entry: The leased entry to wait for.
            deadline: Monotonic timestamp after which the wait gives up.

        Returns:
            The entry, still leased, once it is ready; None if its load failed or it was evicted meanwhile,
            in which case the lease has been released and the caller should retry.

        Raises:
            InferenceBusyError: if the entry does not become ready before the deadline.
        """
        if not entry.ready.wait(timeout=max(0.0, deadline - time.monotonic())):
            self._release(entry)
            raise InferenceBusyError
        with self._registry_lock:
            if entry.error is None and entry.state is EntryState.READY:
                return entry
            entry.refcount -= 1
        return None

    # --- variant resolution, never performed under the registry lock ---

    def _resolve_variant(self, project_id: UUID, model_id: UUID, variant_id: UUID | None) -> _ResolvedVariant:
        """
        Resolve a model variant and its files against the database.

        Args:
            project_id: Project identifier.
            model_id: Model identifier.
            variant_id: Optional variant identifier. When None, the default OpenVINO FP16 variant is selected.

        Returns:
            The resolved variant id, the path of its `.xml` file and its estimated memory footprint.

        Raises:
            ResourceNotFoundError: if the variant or its binary files do not exist.
        """
        with get_db_session() as db:
            from app.services import ModelService

            model_service = ModelService(data_dir=self._data_dir, db_session=db)

            model_variants = model_service.get_model_variants(project_id=project_id, model_id=model_id)
            if variant_id is not None:
                model_variant = next((mv for mv in model_variants if mv.id == variant_id), None)
                if not model_variant:
                    raise ResourceNotFoundError(
                        resource_type=ResourceType.MODEL,
                        resource_id=f"{model_id} variant {variant_id}",
                    )
            else:
                format = ModelFormat.OPENVINO
                precision = ModelPrecision.FP16
                model_variant = next(
                    (mv for mv in model_variants if mv.format == format and mv.precision == precision), None
                )
                if not model_variant:
                    raise ResourceNotFoundError(
                        resource_type=ResourceType.MODEL,
                        resource_id=f"{model_id} with format {format.value} and precision {precision}",
                    )
            files_exist, paths = model_service.get_model_binary_files(
                project_id=project_id, model_id=model_id, model_variant_id=model_variant.id
            )
            if not files_exist:
                raise ResourceNotFoundError(
                    resource_type=ResourceType.MODEL,
                    resource_id=f"{model_id} variant {model_variant.id}",
                )
            return _ResolvedVariant(
                variant_id=model_variant.id,
                xml_path=paths[0],
                size_bytes=int(model_variant.weights_size * self._memory_overhead_factor),
            )

    # --- loading and eviction ---

    def _make_room(self, entry: ModelCacheEntry, deadline: float) -> None:
        """
        Evict LRU entries until `entry` fits within the count and memory budgets.

        The memory budget is best-effort: it is never enforced down to zero models and never blocks a load.
        The count budget is hard, so this waits for a slot to free up.

        Args:
            entry: The entry being loaded, which must never be evicted here.
            deadline: Monotonic timestamp after which waiting for a free slot gives up.

        Raises:
            InferenceBusyError: if no slot can be freed before the deadline.
        """
        while True:
            victim: ModelCacheEntry | None = None
            with self._registry_lock:
                others = [e for e in self._entries if e is not entry]
                over_count = len(self._entries) > self._max_models
                over_memory = (
                    self._max_memory is not None
                    and sum(e.size_bytes for e in self._entries) > self._max_memory
                    and len(others) >= 1  # never enforced down to zero models
                )
                if not over_count and not over_memory:
                    return
                victim = next(
                    (
                        e
                        for e in reversed(self._entries)  # LRU end first
                        if e is not entry and e.refcount == 0 and e.state is EntryState.READY
                    ),
                    None,
                )
                if victim is not None:
                    self._drop(victim)
            if victim is not None:
                self._unload(victim)  # outside the lock
                continue
            if not over_count:
                return  # memory budget is best-effort: never block on it
            if time.monotonic() >= deadline:
                raise InferenceBusyError
            time.sleep(RETRY_INTERVAL)

    def _load(self, entry: ModelCacheEntry, deadline: float) -> ModelCacheEntry:
        """
        Load the model of a LOADING entry owned by the caller, making room for it first.

        Args:
            entry: The LOADING entry leased by the caller.
            deadline: Monotonic timestamp after which waiting for a free slot gives up.

        Returns:
            The entry, READY and still leased by the caller.
        """
        try:
            self._make_room(entry, deadline)
            logger.info("Loading model {} (variant {}) on device {}", entry.model_id, entry.variant_id, entry.device)
            handle = ModelLoader.load(
                model_id=entry.model_id,
                variant_id=entry.variant_id,
                model_xml_path=entry.xml_path,
                device=entry.device,
            )
        except BaseException as exc:
            with self._registry_lock:
                self._drop(entry)
                entry.refcount -= 1
            entry.error = exc
            entry.ready.set()  # release waiters so they retry
            raise

        aborted_error: BaseException | None = None
        with self._registry_lock:
            if entry.state is EntryState.LOADING:
                entry.handle = handle
                entry.state = EntryState.READY
                entry.last_used = time.monotonic()
            else:
                # The entry was evicted while ModelLoader.load() was running (e.g. stop()).
                # Do not publish it back to READY; unload and abort instead.
                entry.handle = handle
                if (entry.project_id, entry.model_id) in self._deleted_models:
                    entry.error = self._deleted_model_error(entry.model_id)
                else:
                    entry.error = InferenceBusyError()
                entry.refcount -= 1
                aborted_error = entry.error

        if aborted_error is not None:
            entry.ready.set()  # wake waiters so they can observe eviction and retry
            self._unload(entry)
            raise aborted_error

        entry.ready.set()
        return entry

    def _try_lease(
        self,
        project_id: UUID,
        model_id: UUID,
        device: DeviceInfo,
        variant_id: UUID,
        resolved: _ResolvedVariant | None,
    ) -> tuple[ModelCacheEntry | None, ModelCacheEntry | None, ModelCacheEntry | None]:
        """
        Look the model up in the cache and lease an entry for it, under the registry lock.

        Args:
            project_id: Project identifier.
            model_id: Model identifier.
            device: Device to use for inference.
            variant_id: Exact variant identifier to look up in the cache.
            resolved: The resolved variant, once the database has been queried, else None.

        Returns:
            A `(hit, mine, stale)` triple, of which at most one element is set: an existing leased entry to wait
            for, a new LOADING entry owned by the caller, or an entry dropped for a device switch that the caller
            must unload outside the lock. An all-None result means the caller should retry.
        Raises:
            ResourceNotFoundError: if the model was invalidated by deletion.
        """
        with self._registry_lock:
            if (project_id, model_id) in self._deleted_models:
                raise self._deleted_model_error(model_id)
            entry = self._find(model_id, variant_id)
            if entry is not None and entry.device == device:
                entry.refcount += 1
                self._touch(entry)  # move to MRU front
                return entry, None, None
            if entry is not None:
                if entry.refcount != 0:
                    return None, None, None  # busy on another device -> retry
                logger.info(
                    "Model {} is loaded on device {}, reloading it on device {}", model_id, entry.device, device
                )
                self._drop(entry)  # device switch: unload, then retry
                return None, None, entry
            if resolved is not None:
                return None, self._insert(project_id, model_id, resolved, device), None
            return None, None, None

    def _acquire(
        self, project_id: UUID, model_id: UUID, device: DeviceInfo, variant_id: UUID | None
    ) -> ModelCacheEntry:
        """
        Return a leased, READY entry for the given model and device, loading the model if needed.

        The caller is responsible for calling `_release` on the returned entry.

        Args:
            project_id: Project identifier.
            model_id: Model identifier.
            device: Device to use for inference.
            variant_id: Optional variant identifier. When None, the default OpenVINO FP16 variant is resolved
                from the database before the cache lookup.

        Returns:
            A leased entry whose model is ready for inference.

        Raises:
            InferenceBusyError: if no entry could be leased before the timeout expires.
            ResourceNotFoundError: if the model was deleted while resolving or loading.
        """
        deadline = time.monotonic() + LOCK_ACQUIRE_TIMEOUT
        resolved: _ResolvedVariant | None = None
        exact_variant_id = variant_id
        if exact_variant_id is None:
            resolved = self._resolve_variant(project_id, model_id, exact_variant_id)
            exact_variant_id = resolved.variant_id
        while True:
            hit, mine, stale = self._try_lease(project_id, model_id, device, exact_variant_id, resolved)
            if stale is not None:
                self._unload(stale)  # outside the lock
            if hit is not None:
                ready = self._wait_ready(hit, deadline)  # None -> load failed / evicted, retry
                if ready is not None:
                    return ready
            elif mine is not None:
                return self._load(mine, deadline)  # loads outside the lock, sets `ready`
            elif stale is None and resolved is None:
                # No entry to wait for and nothing to unload: resolve the variant before inserting one
                resolved = self._resolve_variant(project_id, model_id, exact_variant_id)
                exact_variant_id = resolved.variant_id
                continue
            elif stale is not None:
                continue  # the stale entry is gone, retry immediately with a free slot
            if time.monotonic() >= deadline:
                raise InferenceBusyError
            time.sleep(RETRY_INTERVAL)

    # --- public API ---

    def _set_confidence_threshold(self, model: "Model", confidence_threshold: float) -> bool:
        """
        Apply a confidence threshold to a loaded model, unless it already uses that value.

        The caller must hold the entry's inference lock.

        Args:
            model: The Model API model to configure.
            confidence_threshold: Threshold to apply.

        Returns:
            True if the threshold was changed, False if the model already used it or does not support one.
        """
        if CONFIDENCE_THRESHOLD_PARAM not in model.parameters():
            logger.warning("Model has no confidence threshold to set")
            return False
        current_threshold = model.get_param(CONFIDENCE_THRESHOLD_PARAM)
        if current_threshold == confidence_threshold:
            return False
        logger.info("Changing confidence threshold of model from {} to {}", current_threshold, confidence_threshold)
        model.set_param(CONFIDENCE_THRESHOLD_PARAM, confidence_threshold)
        return True

    def get_status(self) -> InferenceState:
        """
        Get inference server status.

        Returns:
            The server status, together with every model currently loaded.
        """
        with self._registry_lock:
            snapshot = [(entry.state, entry.model_id, entry.device, entry.handle) for entry in self._entries]

        models = tuple(
            InferenceModel(model_id=model_id, device=device, load_timestamp=handle.loaded_at)
            for state, model_id, device, handle in snapshot
            if state is EntryState.READY and handle is not None
        )
        if models:
            status = InferenceStatus.ACTIVE
        elif any(state is EntryState.LOADING for state, _, _, _ in snapshot):
            status = InferenceStatus.LOADING
        else:
            status = InferenceStatus.IDLE
        return InferenceState(status=status, models=models)

    def infer_batch(
        self,
        project_id: UUID,
        model_id: UUID,
        device: DeviceInfo,
        labels: list[Label],
        inputs: list[BatchInferenceInput],
        model_variant_id: UUID | None = None,
        confidence_threshold: float | None = None,
    ) -> dict[tuple[UUID, int | None], list[DatasetItemAnnotation]]:
        """
        Perform batch inference on the provided inputs, loading the requested model if it is not cached yet.

        It processes each input, runs inference, and converts the raw predictions into a structured
        format using the provided labels.

        Args:
            project_id: Project identifier.
            model_id: Model identifier.
            device: Device to use for inference.
            labels: Project labels.
            inputs: List of inputs.
            model_variant_id: Optional model variant identifier. If None, the default OpenVINO FP16 variant is used.
            confidence_threshold: Threshold to apply to the model before inferring.
                When None, the model keeps the threshold it is currently using.

        Returns:
            Dictionary mapping (media_id, frame_index) tuples to lists of DatasetItemAnnotation predictions.

        Raises:
            InferenceBusyError: if the model could not be leased, or is busy with another inference.
        """
        entry = self._acquire(project_id=project_id, model_id=model_id, device=device, variant_id=model_variant_id)
        try:
            if not entry.infer_lock.acquire(timeout=LOCK_ACQUIRE_TIMEOUT):
                raise InferenceBusyError
            try:
                handle = entry.handle
                if handle is None:  # evicted between the lease and the inference lock
                    raise InferenceBusyError
                # Applied under the same lock as the inference, so concurrent requests cannot swap it mid-flight
                if confidence_threshold is not None:
                    self._set_confidence_threshold(handle.model, confidence_threshold)
                logger.debug("Running inference on batch of {} inputs", len(inputs))

                input_data = [inp.data for inp in inputs]
                inference_result = handle.model.infer_batch(input_data)
            finally:
                entry.infer_lock.release()
        finally:
            self._release(entry)

        return {
            (input.media_id, input.frame_index): convert_prediction(
                labels=labels, frame_data=input_data[idx], prediction=inference_result[idx]
            )
            for idx, input in enumerate(inputs)
        }

    def evict_expired(self) -> None:
        """Unload every cached model that has been idle for longer than the configured TTL."""
        now = time.monotonic()
        with self._registry_lock:
            pending_unloads, self._pending_unloads = self._pending_unloads, []
            expired = [
                entry
                for entry in self._entries
                if entry.state is EntryState.READY and entry.refcount == 0 and now - entry.last_used >= self._model_ttl
            ]
            for entry in expired:
                self._drop(entry)
        first_error: BaseException | None = None
        for entry in [*pending_unloads, *expired]:
            try:
                self._unload(entry)  # outside the lock
            except BaseException as exc:
                if first_error is None:
                    first_error = exc
        if first_error is not None:
            raise first_error

    def stop(self) -> None:
        """
        Stop the inference server and unload every model.
        """
        with self._registry_lock:
            entries, self._entries = self._entries, []
            pending_unloads, self._pending_unloads = self._pending_unloads, []
            for entry in entries:
                entry.state = EntryState.EVICTED
        first_error: BaseException | None = None
        for entry in [*pending_unloads, *entries]:
            # Take the inference lock first so teardown never races an in-flight inference
            acquired = entry.infer_lock.acquire(timeout=LOCK_ACQUIRE_TIMEOUT)
            if not acquired:
                logger.warning(
                    "Timed out waiting to unload model {} (variant {}) during shutdown; deferring retry.",
                    entry.model_id,
                    entry.variant_id,
                )
                with self._registry_lock:
                    if entry.handle is not None and entry not in self._pending_unloads:
                        self._pending_unloads.append(entry)
                continue
            try:
                self._unload(entry)
            except BaseException as exc:
                if first_error is None:
                    first_error = exc
            finally:
                if acquired:
                    entry.infer_lock.release()
        if first_error is not None:
            raise first_error
