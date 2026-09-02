# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import hashlib
import json
import shutil
from pathlib import Path
from uuid import uuid4

import huggingface_hub
import requests
from loguru import logger
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from app.models import ModelManifest, TaskType
from app.models.model_manifest import DirectLinkPretrainedWeights, HuggingFacePretrainedWeights

from .model_manifest_service import ModelManifestService


class BaseWeightsService:
    """Service for downloading and managing pretrained model weights from external archives."""

    REQUEST_TIMEOUT = (5, 600)  # (connect timeout, read timeout) in seconds
    RETRY_TOTAL = 2  # total number of retries for failed requests
    RETRY_CONNECT = 1  # retries specifically for connection failures (fail fast on unreachable hosts)
    RETRY_BACKOFF_FACTOR = 0.5  # exponential backoff factor for retries (e.g., 0.5s, 1s)
    HF_CACHE_METADATA_FILENAME = ".geti-huggingface-snapshot.json"

    def __init__(self, data_dir: Path) -> None:
        self.pretrained_weights_dir = data_dir / "pretrained_weights"
        for task in TaskType:
            task_dir = self.pretrained_weights_dir / task.name.lower()
            task_dir.mkdir(parents=True, exist_ok=True)

    def get_remote_weights_path(self, task: TaskType, model_manifest_id: str) -> str:
        """
        Return the remote location of the weights as configured in the manifest.

        Args:
            task: The task type (used for validation)
            model_manifest_id: The unique identifier of the model architecture

        Returns:
            str: The remote URL of the pretrained weights
        """
        manifest = self._get_and_validate_model_manifest(task, model_manifest_id)
        pretrained_weights = manifest.pretrained_weights
        if isinstance(pretrained_weights, DirectLinkPretrainedWeights):
            return pretrained_weights.url
        if isinstance(pretrained_weights, HuggingFacePretrainedWeights):
            return pretrained_weights.repo_id
        raise ValueError(f"Model {model_manifest_id} does not have application-managed pretrained weights")

    def get_local_weights_path(self, task: TaskType, model_manifest_id: str, allow_download: bool = True) -> Path:
        """
        Return the location of the weights file or snapshot directory.

        If not already present and allow_download is enabled, downloads the weights from remote.

        Args:
            task: The task type
            model_manifest_id: The unique identifier of the model architecture
            allow_download: Whether to download weights if not present locally

        Returns:
            Path: Path to the local weights file or snapshot directory

        Raises:
            FileNotFoundError: If weights are not found locally and allow_download is False
        """
        manifest = self._get_and_validate_model_manifest(task, model_manifest_id)

        pretrained_weights = manifest.pretrained_weights
        if isinstance(pretrained_weights, HuggingFacePretrainedWeights):
            return self._get_huggingface_snapshot(
                task=task,
                model_manifest_id=model_manifest_id,
                pretrained_weights=pretrained_weights,
                allow_download=allow_download,
            )
        if not isinstance(pretrained_weights, DirectLinkPretrainedWeights):
            raise ValueError(f"Model {model_manifest_id} does not have application-managed pretrained weights")

        local_filename = pretrained_weights.local_filename
        local_path = self.pretrained_weights_dir / task.name.lower() / local_filename
        if local_path.exists():
            if self._verify_file_integrity(file_path=local_path, sha_sum=pretrained_weights.sha_sum):
                logger.info("Using cached weights for {}: {}", model_manifest_id, local_path)
                return local_path

            logger.warning("Cached weights for {} failed integrity check, will re-download", model_manifest_id)
            local_path.unlink()

        if not allow_download:
            raise FileNotFoundError(f"Weights not found locally for model {model_manifest_id} and download is disabled")

        logger.info("Downloading pretrained weights for {}", model_manifest_id)
        urls = [pretrained_weights.url]
        if pretrained_weights.mirror_url is not None:
            urls.append(pretrained_weights.mirror_url)
        self._download_weights(
            urls=urls,
            local_path=local_path,
            sha_sum=pretrained_weights.sha_sum,
        )

        return local_path

    def remove_local_weights(self, task: TaskType, model_manifest_id: str) -> bool:
        """
        Delete the local base weights of a specific model architecture to free space on disk.

        Args:
            task: The task type
            model_manifest_id: The unique identifier of the model architecture

        Returns:
            bool: True if weights were successfully removed, False if they didn't exist
        """
        manifest = self._get_and_validate_model_manifest(task, model_manifest_id)
        pretrained_weights = manifest.pretrained_weights
        task_dir = self.pretrained_weights_dir / task.name.lower()
        if isinstance(pretrained_weights, DirectLinkPretrainedWeights):
            local_path = task_dir / pretrained_weights.local_filename
        elif isinstance(pretrained_weights, HuggingFacePretrainedWeights):
            local_path = task_dir / model_manifest_id
        else:
            raise ValueError(f"Model {model_manifest_id} does not have application-managed pretrained weights")

        if local_path.exists() or local_path.is_symlink():
            try:
                self._remove_path(local_path)
                logger.info("Removed local weights for {}: {}", model_manifest_id, local_path)
                return True
            except OSError as e:
                logger.error("Failed to remove weights file {}: {}", local_path, e)

        return False

    def remove_all_local_weights(self) -> int:
        """
        Remove all locally cached pretrained weights to free space on disk.

        Returns:
            int: Number of cached weight artifacts that were removed
        """
        removed_count = 0
        if not self.pretrained_weights_dir.exists():
            return 0

        try:
            for task_dir in self.pretrained_weights_dir.iterdir():
                if not task_dir.is_dir() or task_dir.is_symlink():
                    continue
                for weights_path in task_dir.iterdir():
                    try:
                        self._remove_path(weights_path)
                        if not weights_path.name.startswith("."):
                            removed_count += 1
                        logger.debug("Removed cached weights: {}", weights_path)
                    except OSError as e:
                        logger.error("Failed to remove cached weights {}: {}", weights_path, e)

            logger.info("Removed {} cached weight files", removed_count)
            return removed_count
        except OSError as e:
            logger.error("Failed to remove cached weights: {}", e)
            return 0

    def _get_huggingface_snapshot(
        self,
        task: TaskType,
        model_manifest_id: str,
        pretrained_weights: HuggingFacePretrainedWeights,
        allow_download: bool,
    ) -> Path:
        local_path = self.pretrained_weights_dir / task.name.lower() / model_manifest_id
        if self._is_matching_huggingface_snapshot(local_path, pretrained_weights):
            logger.info("Using cached weights for {}: {}", model_manifest_id, local_path)
            return local_path
        if local_path.exists() or local_path.is_symlink():
            self._remove_path(local_path)

        if not allow_download:
            raise FileNotFoundError(f"Weights not found locally for model {model_manifest_id} and download is disabled")

        self._check_huggingface_disk_space(pretrained_weights)
        temp_path = local_path.with_name(f".{local_path.name}.{uuid4().hex}.tmp")
        logger.info("Downloading Hugging Face snapshot for {}", model_manifest_id)
        try:
            huggingface_hub.snapshot_download(
                repo_id=pretrained_weights.repo_id,
                revision=pretrained_weights.revision,
                local_dir=temp_path,
            )
            (temp_path / self.HF_CACHE_METADATA_FILENAME).write_text(
                json.dumps({"repo_id": pretrained_weights.repo_id, "revision": pretrained_weights.revision})
            )
            try:
                temp_path.rename(local_path)
            except FileExistsError:
                if not self._is_matching_huggingface_snapshot(local_path, pretrained_weights):
                    raise
        finally:
            if temp_path.exists() or temp_path.is_symlink():
                self._remove_path(temp_path)

        logger.info("Successfully downloaded Hugging Face snapshot: {}", local_path)
        return local_path

    def _is_matching_huggingface_snapshot(self, path: Path, pretrained_weights: HuggingFacePretrainedWeights) -> bool:
        if not path.is_dir() or path.is_symlink():
            return False
        try:
            metadata = json.loads((path / self.HF_CACHE_METADATA_FILENAME).read_text())
        except (OSError, ValueError):
            return False
        return metadata == {"repo_id": pretrained_weights.repo_id, "revision": pretrained_weights.revision}

    def _check_huggingface_disk_space(
        self, pretrained_weights: HuggingFacePretrainedWeights, safety_margin_gb: float = 1.0
    ) -> None:
        repository_size = 500 * 1024 * 1024
        try:
            info = huggingface_hub.model_info(
                pretrained_weights.repo_id,
                revision=pretrained_weights.revision,
                files_metadata=True,
            )
            sizes = [sibling.size for sibling in (info.siblings or []) if sibling.size is not None]
            if sizes:
                repository_size = sum(sizes)
            else:
                logger.warning("Could not determine repository size for {}, assuming 500MB", pretrained_weights.repo_id)
        except Exception as e:
            logger.warning(
                "Could not determine repository size for {}, assuming 500MB: {}", pretrained_weights.repo_id, e
            )

        available_space = shutil.disk_usage(self.pretrained_weights_dir).free
        required_space = repository_size + (safety_margin_gb * 1024 * 1024 * 1024)
        if available_space < required_space:
            raise OSError(
                f"Insufficient disk space. Required: {required_space / (1024**3):.2f} GB, "
                f"Available: {available_space / (1024**3):.2f} GB"
            )

    @staticmethod
    def _remove_path(path: Path) -> None:
        if path.is_symlink() or path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)

    @staticmethod
    def _verify_file_integrity(file_path: Path, sha_sum: str) -> bool:
        """
        Verify the integrity of a downloaded file using SHA256 checksum.

        Args:
            file_path: Path to the file to verify
            sha_sum: Expected SHA256 checksum

        Returns:
            bool: True if the file integrity is valid, False otherwise
        """
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)

            actual_sha_sum = sha256_hash.hexdigest()
            return actual_sha_sum == sha_sum
        except Exception as e:
            logger.error("Failed to verify file integrity for {}: {}", file_path, e)
            return False

    def _check_disk_space(self, remote_url: str, safety_margin_gb: float = 1.0) -> None:
        """
        Check if there's sufficient disk space for downloading the remote file.

        Args:
            remote_url: URL of the file to download
            safety_margin_gb: Additional safety margin in GB

        Raises:
            OSError: If there's insufficient disk space
        """
        # Use a conservative default (500MB) if the remote size cannot be queried.
        file_size = 500 * 1024 * 1024
        # Try with and without proxies, as some environments may have proxy issues that cause the HEAD request to fail
        for use_env_proxy in (True, False):
            try:
                with self._build_retry_session(use_env_proxy=use_env_proxy) as session:
                    response = session.head(remote_url, allow_redirects=True, timeout=self.REQUEST_TIMEOUT)
                    response.raise_for_status()

                    content_length = response.headers.get("content-length")
                    if content_length:
                        file_size = int(content_length)
                    else:
                        logger.warning("Could not determine file size for {}, assuming 500MB", remote_url)
                    break
            except Exception as e:
                # Log per mode so we can see whether proxy or direct access failed.
                proxy_mode = "env-proxy" if use_env_proxy else "direct"
                logger.warning("Could not check remote file size for {} via {}: {}", remote_url, proxy_mode, e)
        else:
            logger.warning("Could not check remote file size for {}; assuming 500MB", remote_url)

        stat = shutil.disk_usage(self.pretrained_weights_dir)
        available_space = stat.free
        required_space = file_size + (safety_margin_gb * 1024 * 1024 * 1024)

        if available_space < required_space:
            raise OSError(
                f"Insufficient disk space. Required: {required_space / (1024**3):.2f} GB, "
                f"Available: {available_space / (1024**3):.2f} GB"
            )

    def _download_weights(self, urls: list[str], local_path: Path, sha_sum: str) -> None:
        """
        Download weights from the first working URL among the given candidates (e.g. primary then mirror).
        Before download, checks if there is enough space on disk.

        Args:
            urls: Candidate URLs in priority order.
            local_path: Local path to save the file
            sha_sum: Expected SHA256 checksum for verification

        Raises:
            RuntimeError: If none of the candidate URLs yield a file that passes integrity verification.
        """
        local_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = local_path.with_suffix(".tmp")

        last_error: Exception | None = None
        try:
            for url in urls:
                logger.info("Downloading pretrained weights from {}", url)
                try:
                    self._check_disk_space(url)
                    self._download_from_url(url, temp_path)
                except requests.RequestException as e:
                    last_error = e
                    logger.warning("Failed to download weights from {}: {}", url, e)
                    continue

                if self._verify_file_integrity(temp_path, sha_sum):
                    temp_path.rename(local_path)
                    logger.info("Successfully downloaded and verified weights: {}", local_path)
                    return

                last_error = RuntimeError(f"Integrity check failed for weights downloaded from {url}")
                logger.warning("Downloaded weights from {} failed integrity check, trying next candidate URL", url)
                temp_path.unlink(missing_ok=True)

            raise RuntimeError(
                f"Failed to download weights from any of the candidate URLs {urls}: {last_error}"
            ) from last_error

        finally:
            # Clean up temporary file if it exists
            if temp_path.exists():
                temp_path.unlink()

    def _download_from_url(self, url: str, temp_path: Path) -> None:
        """
        Download a single URL to temp_path, retrying with & without the environment proxy on failure.

        Raises:
            requests.RequestException: If both the proxied and direct attempts fail.
        """
        last_error: Exception | None = None
        for use_env_proxy in (True, False):
            try:
                with (
                    self._build_retry_session(use_env_proxy=use_env_proxy) as session,
                    session.get(url, stream=True, timeout=self.REQUEST_TIMEOUT) as response,
                ):
                    response.raise_for_status()
                    with open(temp_path, "wb") as f:
                        for data in response.iter_content(chunk_size=4096):
                            f.write(data)
                return
            except requests.RequestException as e:
                last_error = e
                proxy_mode = "env-proxy" if use_env_proxy else "direct"
                logger.warning("Weight download failed via {} for {}: {}", proxy_mode, url, e)
        raise requests.RequestException(f"Failed to download from {url}") from last_error

    def _build_retry_session(self, use_env_proxy: bool) -> requests.Session:
        session = requests.Session()
        # trust_env=False disables HTTP(S)_PROXY and NO_PROXY from environment.
        session.trust_env = use_env_proxy

        retry = Retry(
            total=self.RETRY_TOTAL,
            connect=self.RETRY_CONNECT,
            read=self.RETRY_TOTAL,
            backoff_factor=self.RETRY_BACKOFF_FACTOR,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=frozenset(["HEAD", "GET"]),
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    @staticmethod
    def _get_and_validate_model_manifest(task: TaskType, model_manifest_id: str) -> ModelManifest:
        """
        Validate or retrieve the default model manifest ID for a given task.

        Args:
            task: The task type (e.g., classification, detection)
            model_manifest_id: The provided model manifest ID, or None to use default

        Returns:
            ModelManifest: The validated model manifest

        Raises:
            ValueError: If the model manifest is not found, task type mismatch, or doesn't have pretrained weights
        """
        manifest = ModelManifestService.get_model_manifest_by_id(model_manifest_id)
        if manifest.task != task:
            raise ValueError(f"Task mismatch: expected '{task.name.lower()}', got '{manifest.task.lower()}'")
        return manifest
