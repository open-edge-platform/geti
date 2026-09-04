# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import huggingface_hub
import pytest

from app.models import TaskType
from app.models.model_manifest import HuggingFacePretrainedWeights
from app.services import BaseWeightsService


@pytest.fixture
def fxt_service(tmp_path: Path) -> BaseWeightsService:
    return BaseWeightsService(tmp_path)


@pytest.fixture
def fxt_weights() -> HuggingFacePretrainedWeights:
    return HuggingFacePretrainedWeights(repo_id="org/model", revision="0123456789abcdef")


def test_downloads_snapshot_to_application_cache(fxt_service: BaseWeightsService, fxt_weights) -> None:
    manifest = MagicMock(pretrained_weights=fxt_weights)

    def download_snapshot(**kwargs) -> str:
        local_dir = Path(kwargs["local_dir"])
        (local_dir / "nested").mkdir(parents=True)
        (local_dir / "nested" / "model.safetensors").write_bytes(b"weights")
        return str(local_dir)

    with (
        patch.object(fxt_service, "_get_and_validate_model_manifest", return_value=manifest),
        patch.object(fxt_service, "_check_huggingface_disk_space"),
        patch(
            "app.services.base_weights_service.huggingface_hub.snapshot_download", side_effect=download_snapshot
        ) as download,
    ):
        result = fxt_service.get_local_weights_path(TaskType.DETECTION, "hf-model")

    assert result == fxt_service.pretrained_weights_dir / "detection" / "hf-model"
    assert (result / "nested" / "model.safetensors").read_bytes() == b"weights"
    assert download.call_args.kwargs["repo_id"] == "org/model"
    assert download.call_args.kwargs["revision"] == "0123456789abcdef"
    assert download.call_args.kwargs["local_dir"].parent == result.parent
    assert download.call_args.kwargs["max_workers"] == 1
    assert not download.call_args.kwargs["local_dir"].exists()


def test_retries_snapshot_after_transport_error(fxt_service: BaseWeightsService, fxt_weights) -> None:
    manifest = MagicMock(pretrained_weights=fxt_weights)
    attempts = 0

    def download_snapshot(**kwargs) -> str:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx.ReadError("proxy connection reset")
        local_dir = Path(kwargs["local_dir"])
        local_dir.mkdir(parents=True, exist_ok=True)
        (local_dir / "model.safetensors").write_bytes(b"weights")
        return str(local_dir)

    with (
        patch.object(fxt_service, "_get_and_validate_model_manifest", return_value=manifest),
        patch.object(fxt_service, "_check_huggingface_disk_space"),
        patch(
            "app.services.base_weights_service.huggingface_hub.snapshot_download",
            side_effect=download_snapshot,
        ) as download,
        patch("app.services.base_weights_service.time.sleep") as sleep,
    ):
        result = fxt_service.get_local_weights_path(TaskType.DETECTION, "hf-model")

    assert download.call_count == 2
    assert download.call_args_list[0].kwargs["local_dir"] == download.call_args_list[1].kwargs["local_dir"]
    sleep.assert_called_once_with(fxt_service.RETRY_BACKOFF_FACTOR)
    assert (result / "model.safetensors").read_bytes() == b"weights"


def test_retries_snapshot_after_wrapped_transport_error(fxt_service: BaseWeightsService, fxt_weights) -> None:
    manifest = MagicMock(pretrained_weights=fxt_weights)

    def wrapped_transport_error() -> huggingface_hub.errors.LocalEntryNotFoundError:
        try:
            raise httpx.ConnectError("Cannot assign requested address")
        except httpx.ConnectError as cause:
            error = huggingface_hub.errors.LocalEntryNotFoundError("snapshot is not cached")
            error.__cause__ = cause
            return error

    def download_snapshot(**kwargs) -> str:
        local_dir = Path(kwargs["local_dir"])
        local_dir.mkdir(parents=True, exist_ok=True)
        if download.call_count == 1:
            (local_dir / "partial.safetensors").write_bytes(b"partial")
            raise wrapped_transport_error()
        (local_dir / "model.safetensors").write_bytes(b"weights")
        return str(local_dir)

    with (
        patch.object(fxt_service, "_get_and_validate_model_manifest", return_value=manifest),
        patch.object(fxt_service, "_check_huggingface_disk_space"),
        patch(
            "app.services.base_weights_service.huggingface_hub.snapshot_download",
            side_effect=download_snapshot,
        ) as download,
        patch("app.services.base_weights_service.time.sleep") as sleep,
    ):
        result = fxt_service.get_local_weights_path(TaskType.DETECTION, "hf-model")

    assert download.call_count == 2
    assert download.call_args_list[0].kwargs["local_dir"] == download.call_args_list[1].kwargs["local_dir"]
    sleep.assert_called_once_with(fxt_service.RETRY_BACKOFF_FACTOR)
    assert (result / "partial.safetensors").read_bytes() == b"partial"
    assert (result / "model.safetensors").read_bytes() == b"weights"


def test_does_not_retry_local_entry_error_without_transport_cause(fxt_service: BaseWeightsService, fxt_weights) -> None:
    manifest = MagicMock(pretrained_weights=fxt_weights)
    error = huggingface_hub.errors.LocalEntryNotFoundError("snapshot is not cached")

    with (
        patch.object(fxt_service, "_get_and_validate_model_manifest", return_value=manifest),
        patch.object(fxt_service, "_check_huggingface_disk_space"),
        patch("app.services.base_weights_service.huggingface_hub.snapshot_download", side_effect=error) as download,
        patch("app.services.base_weights_service.time.sleep") as sleep,
        pytest.raises(huggingface_hub.errors.LocalEntryNotFoundError),
    ):
        fxt_service.get_local_weights_path(TaskType.DETECTION, "hf-model")

    download.assert_called_once()
    sleep.assert_not_called()


def test_reuses_snapshot_offline(fxt_service: BaseWeightsService, fxt_weights) -> None:
    local_path = fxt_service.pretrained_weights_dir / "detection" / "hf-model"
    local_path.mkdir()
    (local_path / fxt_service.HF_CACHE_METADATA_FILENAME).write_text(
        '{"repo_id": "org/model", "revision": "0123456789abcdef"}'
    )
    manifest = MagicMock(pretrained_weights=fxt_weights)
    with (
        patch.object(fxt_service, "_get_and_validate_model_manifest", return_value=manifest),
        patch("app.services.base_weights_service.huggingface_hub.snapshot_download") as download,
    ):
        result = fxt_service.get_local_weights_path(TaskType.DETECTION, "hf-model", allow_download=False)

    assert result == local_path
    download.assert_not_called()


def test_replaces_snapshot_when_revision_changes(fxt_service: BaseWeightsService, fxt_weights) -> None:
    local_path = fxt_service.pretrained_weights_dir / "detection" / "hf-model"
    local_path.mkdir()
    (local_path / fxt_service.HF_CACHE_METADATA_FILENAME).write_text('{"repo_id": "org/model", "revision": "old"}')

    def download_snapshot(**kwargs) -> str:
        destination = Path(kwargs["local_dir"])
        destination.mkdir()
        (destination / "model.safetensors").write_bytes(b"new")
        return str(destination)

    manifest = MagicMock(pretrained_weights=fxt_weights)
    with (
        patch.object(fxt_service, "_get_and_validate_model_manifest", return_value=manifest),
        patch.object(fxt_service, "_check_huggingface_disk_space"),
        patch("app.services.base_weights_service.huggingface_hub.snapshot_download", side_effect=download_snapshot),
    ):
        result = fxt_service.get_local_weights_path(TaskType.DETECTION, "hf-model")

    assert (result / "model.safetensors").read_bytes() == b"new"


def test_offline_lookup_raises_when_snapshot_is_missing(fxt_service: BaseWeightsService, fxt_weights) -> None:
    manifest = MagicMock(pretrained_weights=fxt_weights)
    with (
        patch.object(fxt_service, "_get_and_validate_model_manifest", return_value=manifest),
        patch("app.services.base_weights_service.huggingface_hub.snapshot_download") as download,
        pytest.raises(FileNotFoundError, match="download is disabled"),
    ):
        fxt_service.get_local_weights_path(TaskType.DETECTION, "hf-model", allow_download=False)
    download.assert_not_called()


def test_failed_download_removes_temporary_snapshot(fxt_service: BaseWeightsService, fxt_weights) -> None:
    manifest = MagicMock(pretrained_weights=fxt_weights)

    def fail_download(**kwargs) -> None:
        local_dir = Path(kwargs["local_dir"])
        local_dir.mkdir()
        (local_dir / "partial").write_bytes(b"partial")
        raise RuntimeError("interrupted")

    with (
        patch.object(fxt_service, "_get_and_validate_model_manifest", return_value=manifest),
        patch.object(fxt_service, "_check_huggingface_disk_space"),
        patch("app.services.base_weights_service.huggingface_hub.snapshot_download", side_effect=fail_download),
        pytest.raises(RuntimeError, match="interrupted"),
    ):
        fxt_service.get_local_weights_path(TaskType.DETECTION, "hf-model")

    assert list((fxt_service.pretrained_weights_dir / "detection").iterdir()) == []


def test_removes_snapshots_recursively_without_following_symlinks(
    fxt_service: BaseWeightsService, fxt_weights, tmp_path: Path
) -> None:
    task_dir = fxt_service.pretrained_weights_dir / "detection"
    snapshot = task_dir / "hf-model"
    (snapshot / "nested").mkdir(parents=True)
    (snapshot / "nested" / "weights.bin").write_bytes(b"weights")
    manifest = MagicMock(pretrained_weights=fxt_weights)
    with patch.object(fxt_service, "_get_and_validate_model_manifest", return_value=manifest):
        assert fxt_service.remove_local_weights(TaskType.DETECTION, "hf-model")
    assert not snapshot.exists()

    snapshot.mkdir()
    (snapshot / "config.json").write_text("{}")
    (task_dir / "direct.pth").write_bytes(b"weights")
    external = tmp_path / "external"
    external.mkdir()
    external_file = external / "keep.bin"
    external_file.write_bytes(b"keep")
    (task_dir / "linked-snapshot").symlink_to(external, target_is_directory=True)

    assert fxt_service.remove_all_local_weights() == 3
    assert external_file.read_bytes() == b"keep"


def test_disk_space_uses_hub_repository_metadata(fxt_service: BaseWeightsService, fxt_weights) -> None:
    info = MagicMock(siblings=[MagicMock(size=100), MagicMock(size=200)])
    with (
        patch("app.services.base_weights_service.huggingface_hub.model_info", return_value=info) as model_info,
        patch("app.services.base_weights_service.shutil.disk_usage", return_value=MagicMock(free=299)),
        pytest.raises(OSError, match="Insufficient disk space"),
    ):
        fxt_service._check_huggingface_disk_space(fxt_weights, safety_margin_gb=0)
    model_info.assert_called_once_with("org/model", revision="0123456789abcdef", files_metadata=True)
