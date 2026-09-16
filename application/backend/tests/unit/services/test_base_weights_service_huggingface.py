# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from huggingface_hub.errors import LocalEntryNotFoundError

from app.models import TaskType
from app.models.model_manifest import HuggingFacePretrainedWeights
from app.services import BaseWeightsService


@pytest.fixture
def fxt_service(tmp_path: Path) -> BaseWeightsService:
    return BaseWeightsService(tmp_path)


@pytest.fixture
def fxt_weights() -> HuggingFacePretrainedWeights:
    return HuggingFacePretrainedWeights(repo_id="org/model", revision="0123456789abcdef")


def fxt_repo_info() -> MagicMock:
    return MagicMock(siblings=[MagicMock(size=100), MagicMock(size=200)])


def test_downloads_snapshot_to_application_cache(fxt_service: BaseWeightsService, fxt_weights) -> None:
    manifest = MagicMock(pretrained_weights=fxt_weights)
    calls: list[dict] = []

    def snapshot_download(**kwargs):
        calls.append(kwargs)
        if kwargs.get("local_files_only"):
            raise LocalEntryNotFoundError("not cached")

    with (
        patch.object(fxt_service, "_get_and_validate_model_manifest", return_value=manifest),
        patch("app.services.base_weights_service.huggingface_hub.model_info", return_value=fxt_repo_info()),
        patch("app.services.base_weights_service.huggingface_hub.snapshot_download", side_effect=snapshot_download),
    ):
        result = fxt_service.get_local_weights_path(TaskType.DETECTION, "hf-model")

    local_path = fxt_service.pretrained_weights_dir / "detection" / "hf-model"
    assert result == local_path
    # Cache-first: a local resolution attempt always precedes the network pull.
    assert len(calls) == 2
    assert calls[0] == {
        "repo_id": "org/model",
        "revision": "0123456789abcdef",
        "local_dir": local_path,
        "local_files_only": True,
    }
    snapshot_network = calls[1]
    assert snapshot_network["repo_id"] == "org/model"
    assert snapshot_network["revision"] == "0123456789abcdef"
    assert snapshot_network["local_dir"] == local_path
    assert snapshot_network.get("local_files_only") is None
    assert snapshot_network.get("max_workers") == 1


def test_offline_lookup_uses_hub_cache(fxt_service: BaseWeightsService, fxt_weights) -> None:
    manifest = MagicMock(pretrained_weights=fxt_weights)
    snapshot_download = MagicMock()

    with (
        patch.object(fxt_service, "_get_and_validate_model_manifest", return_value=manifest),
        patch("app.services.base_weights_service.huggingface_hub.snapshot_download", snapshot_download),
    ):
        result = fxt_service.get_local_weights_path(TaskType.DETECTION, "hf-model", allow_download=False)

    assert result == fxt_service.pretrained_weights_dir / "detection" / "hf-model"
    snapshot_download.assert_called_once_with(
        repo_id="org/model",
        revision="0123456789abcdef",
        local_dir=result,
        local_files_only=True,
    )


def test_offline_lookup_raises_when_snapshot_is_missing(fxt_service: BaseWeightsService, fxt_weights) -> None:
    manifest = MagicMock(pretrained_weights=fxt_weights)
    with (
        patch.object(fxt_service, "_get_and_validate_model_manifest", return_value=manifest),
        patch(
            "app.services.base_weights_service.huggingface_hub.snapshot_download",
            side_effect=LocalEntryNotFoundError("missing"),
        ),
        pytest.raises(FileNotFoundError, match="download is disabled"),
    ):
        fxt_service.get_local_weights_path(TaskType.DETECTION, "hf-model", allow_download=False)


def test_revision_is_resolved_by_hub(fxt_service: BaseWeightsService, fxt_weights) -> None:
    manifest = MagicMock(pretrained_weights=fxt_weights.model_copy(update={"revision": None}))
    snapshot_download = MagicMock()

    with (
        patch.object(fxt_service, "_get_and_validate_model_manifest", return_value=manifest),
        patch("app.services.base_weights_service.huggingface_hub.model_info", return_value=fxt_repo_info()),
        patch("app.services.base_weights_service.huggingface_hub.snapshot_download", snapshot_download),
    ):
        fxt_service.get_local_weights_path(TaskType.DETECTION, "hf-model")

    assert snapshot_download.call_args.kwargs["revision"] is None


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


def test_disk_space_uses_hub_repository_metadata(fxt_service: BaseWeightsService) -> None:
    info = MagicMock(siblings=[MagicMock(size=100), MagicMock(size=200)])
    with (
        patch("app.services.base_weights_service.shutil.disk_usage", return_value=MagicMock(free=299)),
        pytest.raises(OSError, match="Insufficient disk space"),
    ):
        fxt_service._check_huggingface_disk_space(info, safety_margin_gb=0)
