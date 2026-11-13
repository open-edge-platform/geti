# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import multiprocessing
import runpy
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.main as main

MAIN_SCRIPT = str(Path(main.__file__))


@pytest.fixture
def frozen_app(monkeypatch):
    """Run app/main.py as the PyInstaller-frozen executable would, without touching the real multiprocessing setup."""
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(multiprocessing, "freeze_support", lambda: None)

    def run(*args: str) -> None:
        monkeypatch.setattr(sys, "argv", ["geti-backend.exe", *args])
        runpy.run_path(MAIN_SCRIPT, run_name="__main__")

    return run


@pytest.mark.parametrize(
    "args",
    [
        ("-m", "pip", "install", "--no-cache-dir", "onnxruntime"),
        ("-c", "import sys; print(sys.version)"),
        ("script.py",),
    ],
)
def test_frozen_executable_refuses_python_interpreter_invocations(frozen_app, args):
    with pytest.raises(SystemExit) as exc_info:
        frozen_app(*args)

    assert "not a Python interpreter" in str(exc_info.value.code)
    assert str(list(args)) in str(exc_info.value.code)


def test_frozen_executable_handles_multiprocessing_children_before_refusing_arguments(frozen_app, monkeypatch):
    def child_freeze_support() -> None:
        # PyInstaller's freeze_support() runs a spawned child and exits before the argument guard is reached.
        raise SystemExit(0)

    monkeypatch.setattr(multiprocessing, "freeze_support", child_freeze_support)

    with pytest.raises(SystemExit) as exc_info:
        frozen_app("--multiprocessing-fork", "parent_pid=1", "pipe_handle=2")

    assert exc_info.value.code == 0


def test_openapi_metadata_matches_generated_spec(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "app"))
    from create_openapi import create_openapi

    schema = main.create_app().openapi()
    assert schema["info"]["contact"] == {"name": "Intel Geti", "url": "https://github.com/open-edge-platform/geti"}
    assert schema["info"]["license"] == {"name": "Apache-2.0", "url": "https://www.apache.org/licenses/LICENSE-2.0"}

    output = tmp_path / "openapi.json"
    create_openapi(str(output))
    assert json.loads(output.read_text()) == schema


def test_spa_fallback_does_not_handle_api_paths(tmp_path, monkeypatch):
    (tmp_path / "index.html").write_text("spa shell")
    monkeypatch.setattr(main.settings, "static_files_dir", tmp_path)
    client = TestClient(main.create_app())

    unsupported_method = client.get("/api/license/accept")
    get_only_method = client.post("/api/system/info")
    action_method = client.options("/api/sinks/not-a-uuid:test")
    unknown_api_path = client.get("/api/not-a-route")
    frontend_route = client.get("/projects")

    assert unsupported_method.status_code == 405
    assert unsupported_method.headers["allow"] == "POST"
    assert get_only_method.status_code == 405
    assert get_only_method.headers["allow"] == "GET, HEAD"
    assert action_method.status_code == 405
    assert action_method.headers["allow"] == "POST"
    assert unknown_api_path.status_code == 404
    assert unknown_api_path.json() == {"detail": "Not Found"}
    assert frontend_route.status_code == 200
    assert frontend_route.text == "spa shell"


def test_uuid_path_parameters_are_documented_as_uuids():
    schema = main.create_app().openapi()
    parameters = schema["paths"]["/api/projects/{project_id}/dataset/views"]["get"]["parameters"]
    project_id = next(parameter for parameter in parameters if parameter["name"] == "project_id")

    assert project_id["schema"]["type"] == "string"
    assert project_id["schema"]["format"] == "uuid"


def test_sink_response_schema_remains_unambiguous():
    schema = main.create_app().openapi()
    sink_items = schema["paths"]["/api/sinks"]["get"]["responses"]["200"]["content"]["application/json"]["schema"][
        "items"
    ]["oneOf"]

    assert "APIErrorResponse" not in schema["components"]["schemas"]
    assert len(sink_items) == 5
