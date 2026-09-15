# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

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
    """Repository metadata with two flat files and one nested file."""
    return MagicMock(
        siblings=[
            MagicMock(rfilename="config.json", size=13),
            MagicMock(rfilename="nested/model.safetensors", size=7),
            MagicMock(rfilename="README.md", size=None),  # unknown size
        ]
    )


def test_downloads_snapshot_to_application_cache(fxt_service: BaseWeightsService, fxt_weights) -> None:
    manifest = MagicMock(pretrained_weights=fxt_weights)

    def download_file(url: str, destination: Path, expected_size: int | None) -> None:
        destination.write_bytes(b"content!")

    with (
        patch.object(fxt_service, "_get_and_validate_model_manifest", return_value=manifest),
        patch("app.services.base_weights_service.huggingface_hub.model_info", return_value=fxt_repo_info()),
        patch.object(fxt_service, "_download_huggingface_file", side_effect=download_file) as download,
    ):
        result = fxt_service.get_local_weights_path(TaskType.DETECTION, "hf-model")

    assert result == fxt_service.pretrained_weights_dir / "detection" / "hf-model"
    assert (result / "config.json").read_bytes() == b"content!"
    assert (result / "nested" / "model.safetensors").read_bytes() == b"content!"
    assert download.call_count == 3
    for call in download.call_args_list:
        assert "resolve/0123456789abcdef" in call.kwargs["url"]
    assert json.loads((result / fxt_service.HF_CACHE_METADATA_FILENAME).read_text()) == {
        "repo_id": "org/model",
        "revision": "0123456789abcdef",
    }
    # partial directory folded into the final path (no leftover hidden dirs)
    assert not (result.parent / ".hf-model.partial").exists()


def test_skips_files_already_downloaded(fxt_service: BaseWeightsService, fxt_weights) -> None:
    manifest = MagicMock(pretrained_weights=fxt_weights)
    partial_dir = fxt_service.pretrained_weights_dir / "detection" / ".hf-model.partial"
    (partial_dir / "nested").mkdir(parents=True)
    config = partial_dir / "config.json"
    config.write_bytes(b"x" * 13)  # complete size -> must be skipped

    download = MagicMock()

    with (
        patch.object(fxt_service, "_get_and_validate_model_manifest", return_value=manifest),
        patch("app.services.base_weights_service.huggingface_hub.model_info", return_value=fxt_repo_info()),
        patch.object(fxt_service, "_download_huggingface_file", download),
    ):
        fxt_service.get_local_weights_path(TaskType.DETECTION, "hf-model")

    # config.json reached its expected size and is skipped; nested/ is still
    # fetched and README has no declared size so it is always re-verified.
    assert download.call_count == 2
    final_dir = fxt_service.pretrained_weights_dir / "detection" / "hf-model"
    assert (final_dir / "config.json").read_bytes() == b"x" * 13


def test_reuses_snapshot_offline(fxt_service: BaseWeightsService, fxt_weights) -> None:
    local_path = fxt_service.pretrained_weights_dir / "detection" / "hf-model"
    local_path.mkdir()
    (local_path / fxt_service.HF_CACHE_METADATA_FILENAME).write_text(
        '{"repo_id": "org/model", "revision": "0123456789abcdef"}'
    )
    manifest = MagicMock(pretrained_weights=fxt_weights)
    with (
        patch.object(fxt_service, "_get_and_validate_model_manifest", return_value=manifest),
        patch.object(fxt_service, "_download_huggingface_file") as download,
    ):
        result = fxt_service.get_local_weights_path(TaskType.DETECTION, "hf-model", allow_download=False)

    assert result == local_path
    download.assert_not_called()


def test_replaces_snapshot_when_revision_changes(fxt_service: BaseWeightsService, fxt_weights) -> None:
    local_path = fxt_service.pretrained_weights_dir / "detection" / "hf-model"
    local_path.mkdir()
    (local_path / fxt_service.HF_CACHE_METADATA_FILENAME).write_text('{"repo_id": "org/model", "revision": "old"}')

    manifest = MagicMock(pretrained_weights=fxt_weights)
    with (
        patch.object(fxt_service, "_get_and_validate_model_manifest", return_value=manifest),
        patch("app.services.base_weights_service.huggingface_hub.model_info", return_value=fxt_repo_info()),
        patch.object(fxt_service, "_download_huggingface_file") as download,
    ):
        fxt_service.get_local_weights_path(TaskType.DETECTION, "hf-model")

    download.assert_called()


def test_offline_lookup_raises_when_snapshot_is_missing(fxt_service: BaseWeightsService, fxt_weights) -> None:
    manifest = MagicMock(pretrained_weights=fxt_weights)
    with (
        patch.object(fxt_service, "_get_and_validate_model_manifest", return_value=manifest),
        patch.object(fxt_service, "_download_huggingface_file") as download,
        pytest.raises(FileNotFoundError, match="download is disabled"),
    ):
        fxt_service.get_local_weights_path(TaskType.DETECTION, "hf-model", allow_download=False)
    download.assert_not_called()


def test_failed_download_keeps_partial_snapshot_for_resume(fxt_service: BaseWeightsService, fxt_weights) -> None:
    """Interrupted snapshots keep their partial directory (visible only via download error)."""
    manifest = MagicMock(pretrained_weights=fxt_weights)

    def fail_download(url: str, destination: Path, expected_size: int | None) -> None:
        raise requests.RequestException("interrupted")

    with (
        patch.object(fxt_service, "_get_and_validate_model_manifest", return_value=manifest),
        patch("app.services.base_weights_service.huggingface_hub.model_info", return_value=fxt_repo_info()),
        patch.object(fxt_service, "_download_huggingface_file", side_effect=fail_download),
        patch.object(fxt_service, "_configure_huggingface_environment"),
        pytest.raises(requests.RequestException, match="interrupted"),
    ):
        fxt_service.get_local_weights_path(TaskType.DETECTION, "hf-model")

    # the partial directory is preserved for the next attempt's resume
    assert (fxt_service.pretrained_weights_dir / "detection" / ".hf-model.partial").is_dir()


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
        patch("app.services.base_weights_service.shutil.disk_usage", return_value=MagicMock(free=299)),
        pytest.raises(OSError, match="Insufficient disk space"),
    ):
        fxt_service._check_huggingface_disk_space(info, safety_margin_gb=0)


def _fake_http_session(response) -> MagicMock:
    """A requests.Session stand-in whose get() is a context manager."""
    session = MagicMock()
    session.__enter__.return_value = session
    session.__exit__.return_value = False
    session.get.return_value.__enter__.return_value = response
    session.get.return_value.__exit__.return_value = False
    return session


def test_download_file_resumes_from_partial_bytes(tmp_path, fxt_service) -> None:
    """Retries after connection resets must resume with a Range header and append."""
    destination = tmp_path / "model.safetensors"
    (tmp_path / "model.safetensors.part").write_bytes(b"resume-")

    response = MagicMock(status_code=206)
    response.iter_content.return_value = iter([b"more", b"!"])
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    session = _fake_http_session(response)

    with (
        patch.object(fxt_service, "_build_retry_session", return_value=session),
        patch("app.services.base_weights_service.time.sleep") as sleep,
    ):
        fxt_service._download_huggingface_file(
            url="https://huggingface.co/org/model/resolve/rev/model.safetensors",
            destination=destination,
            expected_size=12,
        )

    headers = session.get.call_args.kwargs["headers"]
    assert headers["Range"] == "bytes=7-"
    assert destination.read_bytes() == b"resume-more!"
    assert not (tmp_path / "model.safetensors.part").exists()
    sleep.assert_not_called()


def test_download_file_restarts_when_server_ignores_range(tmp_path, fxt_service) -> None:
    destination = tmp_path / "model.safetensors"
    (tmp_path / "model.safetensors.part").write_bytes(b"resume-")

    response = MagicMock(status_code=200)  # server ignored the Range request
    response.iter_content.return_value = iter([b"fresh"])
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    session = _fake_http_session(response)

    with (
        patch.object(fxt_service, "_build_retry_session", return_value=session),
        patch("app.services.base_weights_service.time.sleep"),
    ):
        fxt_service._download_huggingface_file(
            url="https://huggingface.co/org/model/resolve/rev/model.safetensors",
            destination=destination,
            expected_size=None,  # unknown size: rely on a 200/206 download completing
        )

    assert destination.read_bytes() == b"fresh"


def test_download_file_gives_up_after_attempt_budget(tmp_path, fxt_service) -> None:
    destination = tmp_path / "model.safetensors"
    (tmp_path / "model.safetensors.part").write_bytes(b"resume-")

    session = MagicMock()
    session.get.side_effect = requests.ConnectionError("conn reset")
    session.__enter__.return_value = session
    session.__exit__.return_value = False

    sleep = MagicMock()
    with (
        patch.object(fxt_service, "_build_retry_session", return_value=session),
        patch("app.services.base_weights_service.time.sleep", sleep),
        pytest.raises(requests.RequestException, match="connection resets|after|attempts"),
    ):
        fxt_service._download_huggingface_file(
            url="https://huggingface.co/org/model/resolve/rev/model.safetensors",
            destination=destination,
            expected_size=100,
        )

    assert session.get.call_count == fxt_service.HF_RETRY_ATTEMPTS
    delays = [call.args[0] for call in sleep.call_args_list]
    assert delays == [
        min(fxt_service.HF_RETRY_BACKOFF_FACTOR * (2**i), fxt_service.HF_RETRY_MAX_DELAY) for i in range(len(delays))
    ]
    # partial bytes are kept for the next job's resume
    assert (tmp_path / "model.safetensors.part").exists()
