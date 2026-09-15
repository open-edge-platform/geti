# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# /// script
# requires-python = ">=3.11"
# dependencies = ["mcp>=2,<3", "httpx>=0.27"]
# ///
"""Model Context Protocol server exposing a running Geti application.

It lets an MCP client (VS Code Copilot, Claude Desktop, …) inspect projects,
datasets, models and jobs of a local Geti instance, and launch training or
quantization jobs.

Run it with ``uv run application/mcp/server.py`` - the inline metadata above
makes ``uv`` install the dependencies into a throw-away environment, so nothing
has to be added to the backend or the library.

Configuration (environment variables):
    GETI_URL: Base URL of the Geti server. Defaults to ``https://localhost:7860``.
    GETI_CERT: Path to the server certificate used to verify the connection.
        Defaults to ``<data dir>/certs/localhost.pem``.
    GETI_TLS_INSECURE: Set to ``1`` to skip certificate verification. Only do
        this for a local server whose certificate cannot be located.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Final

import httpx
from mcp.server.mcpserver import MCPServer

DEFAULT_URL: Final = "https://localhost:7860"
TIMEOUT: Final = httpx.Timeout(30.0, connect=5.0)

mcp = MCPServer("geti", instructions="Inspect and drive a local Geti instance through its REST API.")


def _data_dir() -> Path:
    """Returns the directory Geti stores its data in.

    Mirrors the backend default: the Windows desktop build writes to
    ``%LOCALAPPDATA%\\Intel\\Geti``, a from-source run to
    ``application/backend/data``.
    """
    override = os.environ.get("DATA_DIR")
    if override:
        return Path(override)

    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "Intel" / "Geti"

    return Path(__file__).resolve().parent.parent / "backend" / "data"


def _verify() -> bool | str:
    """Returns the ``verify`` argument for httpx.

    Geti serves a self-signed certificate, so the certificate file itself is
    pinned. Verification is only disabled when explicitly asked for.
    """
    if os.environ.get("GETI_TLS_INSECURE") == "1":
        return False

    override = os.environ.get("GETI_CERT")
    certificate = Path(override) if override else _data_dir() / "certs" / "localhost.pem"

    if certificate.is_file():
        return str(certificate)

    raise RuntimeError(
        f"The Geti certificate was not found at {certificate}. Point GETI_CERT at it, "
        "or set GETI_TLS_INSECURE=1 to connect to a local server without verification."
    )


def _client() -> httpx.AsyncClient:
    """Creates a client for the configured Geti instance."""
    base_url = os.environ.get("GETI_URL", DEFAULT_URL).rstrip("/")

    return httpx.AsyncClient(base_url=base_url, verify=_verify(), timeout=TIMEOUT)


def _describe(error: httpx.HTTPStatusError) -> str:
    """Turns a failed response into a message worth showing to the model."""
    try:
        detail = error.response.json()
    except ValueError:
        detail = error.response.text

    return f"Geti returned {error.response.status_code}: {json.dumps(detail, default=str)}"


async def _request(method: str, path: str, **kwargs: Any) -> str:
    """Calls the Geti API and returns the response body as JSON text.

    Args:
        method: HTTP method.
        path: Path below the base URL, starting with ``/api``.
        **kwargs: Extra arguments for httpx, such as ``params`` or ``json``.

    Returns:
        The response body, pretty-printed as JSON, or the raw text when the
        response is not JSON.

    Raises:
        RuntimeError: When the server cannot be reached or answers with an error.
    """
    try:
        async with _client() as client:
            response = await client.request(method, path, **kwargs)
            response.raise_for_status()
    except httpx.HTTPStatusError as error:
        raise RuntimeError(_describe(error)) from error
    except httpx.HTTPError as error:
        raise RuntimeError(f"Could not reach Geti at {os.environ.get('GETI_URL', DEFAULT_URL)}: {error}") from error

    if response.headers.get("content-type", "").startswith("application/json"):
        return json.dumps(response.json(), indent=2, default=str)

    return response.text


async def _get(path: str, params: dict[str, Any] | None = None) -> str:
    """Issues a GET request, dropping query parameters that were left unset."""
    cleaned = {key: value for key, value in (params or {}).items() if value is not None}

    return await _request("GET", path, params=cleaned)


def _without_none(values: dict[str, Any]) -> dict[str, Any]:
    """Drops keys whose value is ``None`` so server-side defaults apply."""
    return {key: value for key, value in values.items() if value is not None}


@mcp.tool()
async def list_projects() -> str:
    """Lists every project on the Geti instance, with its id, name and task type."""
    return await _get("/api/projects")


@mcp.tool()
async def get_project(project_id: str) -> str:
    """Returns one project, including its labels and dataset summary.

    Args:
        project_id: Id of the project.
    """
    return await _get(f"/api/projects/{project_id}")


@mcp.tool()
async def get_dataset_statistics(project_id: str, dataset_view_id: str | None = None) -> str:
    """Returns media counts, annotation counts and per-label statistics of a dataset.

    Args:
        project_id: Id of the project.
        dataset_view_id: Optional id of a named dataset view to restrict to.
    """
    return await _get(f"/api/projects/{project_id}/dataset/statistics", {"dataset_view_id": dataset_view_id})


@mcp.tool()
async def list_media(
    project_id: str,
    limit: int = 10,
    offset: int = 0,
    annotation_status: str | None = None,
    subsets: list[str] | None = None,
) -> str:
    """Lists media items of a project's dataset.

    Args:
        project_id: Id of the project.
        limit: Number of items to return, between 1 and 100.
        offset: Number of items to skip.
        annotation_status: Optional filter, for example ``not_annotated``.
        subsets: Optional subsets to restrict to, such as ``training`` or ``validation``.
    """
    return await _get(
        f"/api/projects/{project_id}/dataset/media",
        {
            "limit": max(1, min(limit, 100)),
            "offset": max(0, offset),
            "annotation_status": annotation_status,
            "subsets": subsets,
        },
    )


@mcp.tool()
async def list_dataset_revisions(project_id: str) -> str:
    """Lists the frozen dataset revisions a model can be trained on.

    Args:
        project_id: Id of the project.
    """
    return await _get(f"/api/projects/{project_id}/dataset_revisions")


@mcp.tool()
async def list_models(project_id: str, dataset_revision_id: str | None = None) -> str:
    """Lists the trained models of a project.

    Args:
        project_id: Id of the project.
        dataset_revision_id: Optional dataset revision to restrict the list to.
    """
    return await _get(f"/api/projects/{project_id}/models", {"dataset_revision_id": dataset_revision_id})


@mcp.tool()
async def get_model(project_id: str, model_id: str) -> str:
    """Returns one model revision, with its scores and optimized variants.

    Args:
        project_id: Id of the project.
        model_id: Id of the model revision.
    """
    return await _get(f"/api/projects/{project_id}/models/{model_id}")


@mcp.tool()
async def get_training_metrics(project_id: str, model_id: str) -> str:
    """Returns the per-epoch training curves of a model revision.

    Args:
        project_id: Id of the project.
        model_id: Id of the model revision.
    """
    return await _get(f"/api/projects/{project_id}/models/{model_id}/training_metrics")


@mcp.tool()
async def get_training_logs(project_id: str, model_id: str) -> str:
    """Returns the training log of a model revision as plain text.

    Args:
        project_id: Id of the project.
        model_id: Id of the model revision.
    """
    return await _request(
        "GET",
        f"/api/projects/{project_id}/models/{model_id}/logs",
        headers={"Accept": "text/plain"},
    )


@mcp.tool()
async def list_model_architectures(task: str) -> str:
    """Lists the architectures that can be trained for a task.

    Args:
        task: Task type, such as ``classification``, ``detection``,
            ``instance_segmentation``, ``semantic_segmentation`` or
            ``keypoint_detection``.
    """
    return await _get("/api/model_architectures", {"task": task})


@mcp.tool()
async def list_training_devices() -> str:
    """Lists the devices available for training, with the ids that `start_training` expects."""
    return await _get("/api/system/devices/training")


@mcp.tool()
async def get_system_info() -> str:
    """Returns the version, platform and accelerator information of the Geti server."""
    return await _get("/api/system/info")


@mcp.tool()
async def list_jobs() -> str:
    """Lists all jobs, running and finished."""
    return await _get("/api/jobs")


@mcp.tool()
async def get_job(job_id: str) -> str:
    """Returns one job, including its state and progress.

    Args:
        job_id: Id of the job.
    """
    return await _get(f"/api/jobs/{job_id}")


@mcp.tool()
async def start_training(
    project_id: str,
    model_architecture_id: str,
    device: str,
    parent_model_revision_id: str | None = None,
    dataset_revision_id: str | None = None,
) -> str:
    """Starts a training job and returns the created job.

    Confirm the architecture with `list_model_architectures` and the device with
    `list_training_devices` before calling this.

    Args:
        project_id: Id of the project to train in.
        model_architecture_id: Architecture to train, for example
            ``object-detection-atss-mobilenet-v2``.
        device: Device id, for example ``cpu``, ``xpu-0`` or ``cuda-0``.
        parent_model_revision_id: Optional model revision to fine-tune from.
        dataset_revision_id: Optional dataset revision; the latest data is used when omitted.
    """
    body = {
        "job_type": "train",
        "project_id": project_id,
        "parameters": _without_none(
            {
                "device": device,
                "model_architecture_id": model_architecture_id,
                "parent_model_revision_id": parent_model_revision_id,
                "dataset_revision_id": dataset_revision_id,
            }
        ),
    }

    return await _request("POST", "/api/jobs", json=body)


@mcp.tool()
async def start_quantization(
    project_id: str,
    model_id: str,
    model_architecture_id: str,
    max_calibration_subset_size: int = 100,
    max_drop: float | None = None,
    max_num_iterations: int | None = None,
) -> str:
    """Starts a post-training quantization job and returns the created job.

    Args:
        project_id: Id of the project the model belongs to.
        model_id: Id of the model revision to quantize.
        model_architecture_id: Architecture of that model revision.
        max_calibration_subset_size: Number of samples used for calibration.
        max_drop: Optional accuracy drop budget as a fraction, for example ``0.03`` for 3%.
        max_num_iterations: Optional iteration cap for accuracy-aware quantization.
    """
    body = {
        "job_type": "quantize",
        "project_id": project_id,
        "parameters": _without_none(
            {
                "model_id": model_id,
                "model_architecture_id": model_architecture_id,
                "max_calibration_subset_size": max_calibration_subset_size,
                "max_drop": max_drop,
                "max_num_iterations": max_num_iterations,
            }
        ),
    }

    return await _request("POST", "/api/jobs", json=body)


@mcp.tool()
async def cancel_job(job_id: str) -> str:
    """Cancels a running job.

    Args:
        job_id: Id of the job to cancel.
    """
    return await _request("POST", f"/api/jobs/{job_id}:cancel")


if __name__ == "__main__":
    mcp.run()
