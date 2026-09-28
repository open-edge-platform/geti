# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient

import app.main as main


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


def test_api_error_schemas_cover_business_and_request_validation_errors():
    schema = main.create_app().openapi()
    error_response = schema["components"]["schemas"]["APIErrorResponse"]
    detail_types = {item.get("type") for item in error_response["properties"]["detail"]["anyOf"]}
    sink_items = schema["paths"]["/api/sinks"]["get"]["responses"]["200"]["content"]["application/json"]["schema"][
        "items"
    ]["oneOf"]

    assert detail_types == {"array", "string"}
    assert len(sink_items) == 5
