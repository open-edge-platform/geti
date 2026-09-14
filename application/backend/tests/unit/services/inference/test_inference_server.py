# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from unittest.mock import ANY, Mock, patch
from uuid import UUID, uuid4

import numpy as np
import pytest
from model_api.models import Model

from app.models import BatchInferenceInput, DatasetItemAnnotation, Label
from app.models.model_revision import ModelFormat, ModelPrecision, ModelVariant
from app.models.system import DeviceInfo, DeviceType
from app.services import ModelService
from app.services.inference import InferenceModel, InferenceServer, InferenceState, InferenceStatus
from app.services.inference.inference_server import InferenceBusyError
from app.services.inference.model_loader import LoadedModelHandle
from app.services.inference.model_registry import EntryState, ModelCacheEntry

CPU = DeviceInfo(type=DeviceType.CPU, name="CPU", memory=None, index=None)
XPU = DeviceInfo(type=DeviceType.XPU, name="XPU", memory=1024, index=0)


def _handle(model_id: UUID, variant_id: UUID, device: DeviceInfo, model: Mock | None = None) -> LoadedModelHandle:
    """A loaded model handle wrapping a mocked Model API model."""
    return LoadedModelHandle(
        model_id=model_id,
        variant_id=variant_id,
        model=model if model is not None else Mock(spec=Model),
        device=device,
        loaded_at=datetime.now(),
    )


def _seed_entry(
    server: InferenceServer,
    *,
    model_id: UUID | None = None,
    variant_id: UUID | None = None,
    device: DeviceInfo = CPU,
    model: Mock | None = None,
    size_bytes: int = 0,
    state: EntryState = EntryState.READY,
    refcount: int = 0,
    last_used: float | None = None,
) -> ModelCacheEntry:
    """Insert a ready-made cache entry at the MRU front of the server cache, bypassing any loading."""
    entry = ModelCacheEntry(
        project_id=uuid4(),
        model_id=model_id if model_id is not None else uuid4(),
        variant_id=variant_id if variant_id is not None else uuid4(),
        device=device,
        xml_path=Path("model.xml"),
        size_bytes=size_bytes,
        state=state,
        refcount=refcount,
    )
    if state is EntryState.READY:
        entry.handle = _handle(entry.model_id, entry.variant_id, device, model)
        entry.ready.set()
    if last_used is not None:
        entry.last_used = last_used
    server._entries.insert(0, entry)
    return entry


@contextmanager
def _patched_model_service(
    tmp_path, weights_size: int = 0, variant_id: UUID | None = None
) -> Iterator[dict[UUID, UUID]]:
    """Patch the database lookups performed while resolving a model variant.

    Args:
        tmp_path: Directory holding the fake model files.
        weights_size: On-disk size reported for the resolved variant weights.
        variant_id: Variant id resolved for every model; a fresh one per model when omitted.

    Yields a mapping of model id to the variant id resolved for it.
    """
    variant_ids: dict[UUID, UUID] = {}

    def _get_model_variants(*, project_id: UUID, model_id: UUID) -> list[Mock]:
        resolved_id = variant_ids.setdefault(model_id, variant_id if variant_id is not None else uuid4())
        return [
            Mock(
                spec=ModelVariant,
                id=resolved_id,
                format=ModelFormat.OPENVINO,
                precision=ModelPrecision.FP16,
                weights_size=weights_size,
            )
        ]

    with (
        patch.object(target=ModelService, attribute="get_model_variants", side_effect=_get_model_variants),
        patch.object(
            target=ModelService,
            attribute="get_model_binary_files",
            return_value=(True, (tmp_path / "model.xml", tmp_path / "model.bin")),
        ),
    ):
        yield variant_ids


@contextmanager
def _patched_loader() -> Iterator[tuple[Mock, Mock, list[LoadedModelHandle]]]:
    """Patch the model loader, handing out a fresh handle per load.

    Yields the load and unload mocks, together with the handles returned by each load, in order.
    """
    handles: list[LoadedModelHandle] = []

    def _load(*, model_id: UUID, variant_id: UUID, model_xml_path: Path, device: DeviceInfo) -> LoadedModelHandle:
        handle = _handle(model_id, variant_id, device)
        handles.append(handle)
        return handle

    with (
        patch("app.services.inference.model_loader.ModelLoader.load", side_effect=_load) as mock_load,
        patch("app.services.inference.model_loader.ModelLoader.unload") as mock_unload,
    ):
        yield mock_load, mock_unload, handles


class TestInferenceServer:
    def test_confidence_threshold_param_exists_in_mapi(self) -> None:
        """Ensure that the confidence threshold parameter is defined in the Model API."""
        from model_api.models.parameters import ParameterRegistry

        from app.services.inference.inference_server import CONFIDENCE_THRESHOLD_PARAM

        assert CONFIDENCE_THRESHOLD_PARAM in ParameterRegistry.CONFIDENCE_THRESHOLD

    # --- cache behaviour ---

    def test_cache_hit_does_not_reload(self, tmp_path) -> None:
        """A second request for an already cached model on the same device does not load it again."""
        server = InferenceServer(data_dir=Path(tmp_path), max_models=2)
        entry = _seed_entry(server)

        with _patched_loader() as (mock_load, mock_unload, handles):
            for _ in range(2):
                server.infer_batch(
                    project_id=entry.project_id,
                    model_id=entry.model_id,
                    model_variant_id=entry.variant_id,
                    device=CPU,
                    labels=[],
                    inputs=[],
                )

        mock_load.assert_not_called()
        mock_unload.assert_not_called()
        assert server._entries == [entry]

    def test_device_switch_unloads_then_reloads(self, tmp_path) -> None:
        """Requesting a cached model on another device unloads it and loads it again on the new device."""
        server = InferenceServer(data_dir=Path(tmp_path), max_models=2)
        entry = _seed_entry(server, device=CPU)
        old_handle = entry.handle

        with (
            _patched_model_service(tmp_path, variant_id=entry.variant_id),
            _patched_loader() as (mock_load, mock_unload, handles),
        ):
            server.infer_batch(
                project_id=entry.project_id,
                model_id=entry.model_id,
                model_variant_id=entry.variant_id,
                device=XPU,
                labels=[],
                inputs=[],
            )

        mock_unload.assert_called_once_with(old_handle)
        mock_load.assert_called_once_with(
            model_id=entry.model_id, variant_id=entry.variant_id, model_xml_path=tmp_path / "model.xml", device=XPU
        )
        assert [e.device for e in server._entries] == [XPU]

    def test_evicts_lru_when_max_models_reached(self, tmp_path) -> None:
        """With a full cache, loading another model evicts the least recently used one."""
        server = InferenceServer(data_dir=Path(tmp_path), max_models=2)
        project_id = uuid4()
        model_a, model_b, model_c = uuid4(), uuid4(), uuid4()

        with _patched_model_service(tmp_path), _patched_loader() as (mock_load, mock_unload, handles):
            for model_id in (model_a, model_b, model_c):
                server.infer_batch(project_id=project_id, model_id=model_id, device=CPU, labels=[], inputs=[])
            evicted_handle = handles[0]

        assert mock_load.call_count == 3
        mock_unload.assert_called_once_with(evicted_handle)
        assert {e.model_id for e in server._entries} == {model_b, model_c}

    def test_memory_budget_evicts_lru(self, tmp_path) -> None:
        """Loading a model that pushes the estimated memory over the budget evicts the LRU one."""
        # Two models of 40 bytes on disk, with the default 1.5 overhead factor, need 120 bytes.
        server = InferenceServer(data_dir=Path(tmp_path), max_models=5, max_memory=100)
        project_id = uuid4()
        model_a, model_b = uuid4(), uuid4()

        with _patched_model_service(tmp_path, weights_size=40), _patched_loader() as (mock_load, mock_unload, handles):
            for model_id in (model_a, model_b):
                server.infer_batch(project_id=project_id, model_id=model_id, device=CPU, labels=[], inputs=[])
            evicted_handle = handles[0]

        mock_unload.assert_called_once_with(evicted_handle)
        assert [e.model_id for e in server._entries] == [model_b]
        assert [e.size_bytes for e in server._entries] == [60]

    def test_memory_budget_never_evicts_the_only_model(self, tmp_path) -> None:
        """A single model larger than the memory budget is still loaded: the budget is best-effort."""
        server = InferenceServer(data_dir=Path(tmp_path), max_models=2, max_memory=10)
        model_id = uuid4()

        with (
            _patched_model_service(tmp_path, weights_size=1000),
            _patched_loader() as (mock_load, mock_unload, handles),
        ):
            server.infer_batch(project_id=uuid4(), model_id=model_id, device=CPU, labels=[], inputs=[])

        mock_load.assert_called_once()
        mock_unload.assert_not_called()
        assert [e.model_id for e in server._entries] == [model_id]

    def test_in_use_model_is_not_evicted(self, tmp_path, monkeypatch) -> None:
        """An entry that is leased is skipped both when making room and when evicting expired models."""
        monkeypatch.setattr("app.services.inference.inference_server.LOCK_ACQUIRE_TIMEOUT", 0.2)
        server = InferenceServer(data_dir=Path(tmp_path), max_models=1, model_ttl=60)
        in_use = _seed_entry(server, refcount=1, last_used=0.0)  # leased and long expired

        with _patched_model_service(tmp_path), _patched_loader() as (mock_load, mock_unload, handles):
            # The only slot is taken by a leased entry, so no room can be made for another model.
            with pytest.raises(InferenceBusyError):
                server.infer_batch(project_id=uuid4(), model_id=uuid4(), device=CPU, labels=[], inputs=[])

            server.evict_expired()

        mock_load.assert_not_called()
        mock_unload.assert_not_called()
        assert server._entries == [in_use]

    def test_concurrent_requests_for_same_model_load_once(self, tmp_path) -> None:
        """Two threads asking for the same model share a single load and the resulting handle."""
        server = InferenceServer(data_dir=Path(tmp_path), max_models=2)
        project_id, model_id = uuid4(), uuid4()
        load_started = threading.Event()
        finish_load = threading.Event()
        handles: list[LoadedModelHandle | None] = []

        def _blocking_load(*, model_id: UUID, variant_id: UUID, model_xml_path: Path, device: DeviceInfo):
            load_started.set()
            finish_load.wait(timeout=5)
            return _handle(model_id, variant_id, device)

        def _acquire_and_release() -> None:
            entry = server._acquire(project_id=project_id, model_id=model_id, device=CPU, variant_id=None)
            handles.append(entry.handle)
            server._release(entry)

        with (
            _patched_model_service(tmp_path),
            patch("app.services.inference.model_loader.ModelLoader.load", side_effect=_blocking_load) as mock_load,
        ):
            first = threading.Thread(target=_acquire_and_release)
            first.start()
            assert load_started.wait(timeout=5)  # the first thread owns the load and is inside it

            second = threading.Thread(target=_acquire_and_release)
            second.start()
            finish_load.set()
            first.join(timeout=5)
            second.join(timeout=5)

        assert mock_load.call_count == 1
        assert len(handles) == 2
        assert handles[0] is handles[1] is not None
        assert len(server._entries) == 1

    def test_load_failure_removes_entry_and_propagates(self, tmp_path) -> None:
        """A failed load leaves no entry behind, propagates the error, and does not poison later requests."""
        server = InferenceServer(data_dir=Path(tmp_path), max_models=2)
        project_id, model_id = uuid4(), uuid4()
        handle = _handle(model_id, uuid4(), CPU)

        with (
            _patched_model_service(tmp_path),
            patch(
                "app.services.inference.model_loader.ModelLoader.load",
                side_effect=[RuntimeError("load failed"), handle],
            ) as mock_load,
        ):
            with pytest.raises(RuntimeError, match="load failed"):
                server.infer_batch(project_id=project_id, model_id=model_id, device=CPU, labels=[], inputs=[])

            assert server._entries == []

            server.infer_batch(project_id=project_id, model_id=model_id, device=CPU, labels=[], inputs=[])

        assert mock_load.call_count == 2
        assert [e.handle for e in server._entries] == [handle]

    # --- eviction and teardown ---

    def test_evict_expired_unloads_only_expired_entries(self, tmp_path) -> None:
        """Only the models idle for longer than the TTL are unloaded."""
        server = InferenceServer(data_dir=Path(tmp_path), max_models=2, model_ttl=60)
        expired = _seed_entry(server, last_used=0.0)
        fresh = _seed_entry(server)
        expired_handle = expired.handle

        with patch("app.services.inference.model_loader.ModelLoader.unload") as mock_unload:
            server.evict_expired()

        mock_unload.assert_called_once_with(expired_handle)
        assert server._entries == [fresh]
        assert expired.state is EntryState.EVICTED

    def test_stop_unloads_all_models(self, tmp_path) -> None:
        """Stopping the server drains the cache and unloads every model."""
        server = InferenceServer(data_dir=Path(tmp_path), max_models=2)
        first = _seed_entry(server)
        second = _seed_entry(server)
        unloaded_handles = [entry.handle for entry in server._entries]  # MRU order: second, then first
        assert unloaded_handles == [second.handle, first.handle]

        with patch("app.services.inference.model_loader.ModelLoader.unload") as mock_unload:
            server.stop()

        assert [call.args[0] for call in mock_unload.call_args_list] == unloaded_handles
        assert server._entries == []

    # --- status ---

    @pytest.mark.parametrize(
        "states, expected_status, expected_models",
        [
            pytest.param([], InferenceStatus.IDLE, 0, id="idle"),
            pytest.param([EntryState.LOADING], InferenceStatus.LOADING, 0, id="loading"),
            pytest.param([EntryState.READY, EntryState.READY], InferenceStatus.ACTIVE, 2, id="active"),
        ],
    )
    def test_get_status_idle_loading_active(self, states, expected_status, expected_models, tmp_path) -> None:
        server = InferenceServer(data_dir=Path(tmp_path), max_models=2)
        for state in states:
            _seed_entry(server, state=state)

        status = server.get_status()

        assert status.status == expected_status
        assert len(status.models) == expected_models
        ready = [entry for entry in server._entries if entry.state is EntryState.READY]
        assert list(status.models) == [
            InferenceModel(model_id=entry.model_id, device=entry.device, load_timestamp=ANY) for entry in ready
        ]

    def test_get_status_reports_loaded_model(self, tmp_path) -> None:
        server = InferenceServer(data_dir=Path(tmp_path))
        entry = _seed_entry(server)

        assert server.get_status() == InferenceState(
            status=InferenceStatus.ACTIVE,
            models=(InferenceModel(model_id=entry.model_id, device=CPU, load_timestamp=ANY),),
        )

    # --- inference ---

    @staticmethod
    def _model_with_threshold(current_threshold: float | None) -> Mock:
        """A mocked model that either exposes the given confidence threshold, or none at all."""
        model = Mock(spec=Model)
        model.infer_batch.return_value = []
        model.parameters.return_value = {} if current_threshold is None else {"confidence_threshold": Mock()}
        model.get_param.return_value = current_threshold
        return model

    def _infer(self, server: InferenceServer, entry: ModelCacheEntry, **kwargs) -> dict:
        """Run a batch inference against an already cached entry."""
        return server.infer_batch(
            project_id=entry.project_id,
            model_id=entry.model_id,
            model_variant_id=entry.variant_id,
            device=entry.device,
            labels=kwargs.pop("labels", []),
            inputs=kwargs.pop("inputs", []),
            **kwargs,
        )

    def test_infer_batch_applies_confidence_threshold(self, tmp_path) -> None:
        """A threshold that differs from the one in use is pushed onto the model before inferring."""
        server = InferenceServer(data_dir=Path(tmp_path))
        model = self._model_with_threshold(0.5)
        entry = _seed_entry(server, model=model)

        self._infer(server, entry, confidence_threshold=0.8)

        model.set_param.assert_called_once_with("confidence_threshold", 0.8)
        model.infer_batch.assert_called_once()

    @pytest.mark.parametrize(
        "current_threshold, requested_threshold",
        [
            pytest.param(0.5, 0.5, id="already_applied"),
            pytest.param(0.5, None, id="not_requested"),
            pytest.param(None, 0.8, id="unsupported_by_model"),
        ],
    )
    def test_infer_batch_keeps_confidence_threshold(self, current_threshold, requested_threshold, tmp_path) -> None:
        """The model is left untouched when the threshold is already in use, not requested, or unsupported."""
        server = InferenceServer(data_dir=Path(tmp_path))
        model = self._model_with_threshold(current_threshold)
        entry = _seed_entry(server, model=model)

        self._infer(server, entry, confidence_threshold=requested_threshold)

        model.set_param.assert_not_called()
        model.infer_batch.assert_called_once()

    def test_infer_batch(self, tmp_path) -> None:
        media_id = uuid4()
        model = Mock(spec=Model)
        inference_result = Mock()
        model.infer_batch.return_value = [inference_result]

        label = Mock(spec=Label)
        raw_uint8 = np.full((20, 20, 3), 128, dtype=np.uint8)
        input = BatchInferenceInput(media_id=media_id, frame_index=15, data=raw_uint8)
        annotation = Mock(spec=DatasetItemAnnotation)

        server = InferenceServer(data_dir=Path(tmp_path))
        entry = _seed_entry(server, model=model)

        with patch("app.services.inference.inference_server.convert_prediction") as mock_convert_prediction:
            mock_convert_prediction.return_value = [annotation]
            result = self._infer(server, entry, labels=[label], inputs=[input])

        (passed_batch,) = model.infer_batch.call_args.args
        assert len(passed_batch) == 1
        np.testing.assert_array_equal(passed_batch[0], raw_uint8)
        assert passed_batch[0].dtype == np.uint8

        assert result == {(media_id, 15): [annotation]}

    def test_infer_batch_not_loaded(self, tmp_path) -> None:
        """Inferring with an empty cache loads the requested model instead of failing."""
        server = InferenceServer(data_dir=Path(tmp_path))
        project_id, model_id = uuid4(), uuid4()
        label = Mock(spec=Label)

        with _patched_model_service(tmp_path) as variant_ids, _patched_loader() as (mock_load, _, _handles):
            server.infer_batch(project_id=project_id, model_id=model_id, device=CPU, labels=[label], inputs=[])

        mock_load.assert_called_once_with(
            model_id=model_id,
            variant_id=variant_ids[model_id],
            model_xml_path=tmp_path / "model.xml",
            device=CPU,
        )
        assert [e.model_id for e in server._entries] == [model_id]

    def test_infer_batch_busy_raises(self, tmp_path, monkeypatch) -> None:
        """A model already busy with another inference makes the request time out."""
        monkeypatch.setattr("app.services.inference.inference_server.LOCK_ACQUIRE_TIMEOUT", 0.1)
        server = InferenceServer(data_dir=Path(tmp_path))
        entry = _seed_entry(server)

        entry.infer_lock.acquire()
        try:
            with pytest.raises(InferenceBusyError):
                self._infer(server, entry)
        finally:
            entry.infer_lock.release()

        assert entry.refcount == 0  # the lease is released even when the inference lock times out
