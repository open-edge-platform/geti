# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from io import BytesIO
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute
from PIL import Image as PILImage

from app.api.dependencies import get_ome_rendering_service
from app.api.routers import media, ome
from app.api.schemas.media import OmeChannelViewResponse
from app.models.ome import GrayscaleProjection, OmeChannelView, OmeImageMetadata, RgbChannelAssignment, RgbProjection
from app.services import ResourceNotFoundError, ResourceType
from app.services.base import InvalidImageError
from app.services.ome.rendering import (
    InvalidChannelViewError,
    InvalidRenderSelectionError,
    OmeRenderingService,
    parse_channel_override,
)


@pytest.fixture
def fxt_rendering_service(fxt_app: FastAPI) -> MagicMock:
    service = MagicMock(spec=OmeRenderingService)
    fxt_app.dependency_overrides[get_ome_rendering_service] = lambda: service
    return service


@pytest.mark.parametrize(
    ("suffix", "method", "handler"),
    [
        ("ome", "get", "get_ome_image_info"),
        ("channel-view", "get", "get_ome_channel_view"),
        ("channel-view", "put", "set_ome_channel_view"),
        ("render", "get", "render_ome_plane"),
    ],
)
def test_ome_routes_preserve_api_contract(fxt_app: FastAPI, suffix: str, method: str, handler: str) -> None:
    path = f"/api/projects/{{project_id}}/dataset/media/{{media_id}}/{suffix}"
    routes = [
        route
        for route in ome.router.routes
        if isinstance(route, APIRoute)
        and route.path == path
        and route.methods is not None
        and method.upper() in route.methods
    ]
    assert len(routes) == 1
    assert routes[0].endpoint.__module__ == "app.api.routers.ome"
    assert all(route.path != path for route in media.router.routes if isinstance(route, APIRoute))
    operation = fxt_app.openapi()["paths"][path][method]
    assert operation["operationId"] == (
        f"{handler}_api_projects__project_id__dataset_media__media_id__{suffix.replace('-', '_')}_{method}"
    )
    assert operation["tags"] == ["Media"]


@pytest.mark.parametrize(
    "projection",
    [RgbProjection(channels=(RgbChannelAssignment(channel=0, target="red"),)), GrayscaleProjection(channel=1)],
)
def test_get_ome_structure(fxt_get_project, fxt_media_service, fxt_client, projection):
    media_id = uuid4()
    info = OmeImageMetadata(
        size_x=5,
        size_y=4,
        size_c=3,
        dimension_order="XYCZT",
        pixel_type="uint16",
        channel_projection=projection,
        raw_metadata="<OME/>",
    )
    fxt_media_service.get_ome_image_info.return_value = info
    response = fxt_client.get(f"/api/projects/{fxt_get_project.id}/dataset/media/{media_id}/ome")
    assert response.status_code == 200
    assert response.json() == info.model_dump(mode="json")
    assert response.json()["channel_projection"] == projection.model_dump(mode="json")
    assert "channel_mapping" not in response.json()
    fxt_media_service.get_ome_image_info.assert_called_once_with(fxt_get_project.id, media_id)


def test_ome_structure_openapi_uses_channel_projection(fxt_app):
    spec = fxt_app.openapi()
    response = spec["paths"]["/api/projects/{project_id}/dataset/media/{media_id}/ome"]["get"]["responses"]["200"]
    schema_name = response["content"]["application/json"]["schema"]["$ref"].rsplit("/", 1)[1]
    schema = spec["components"]["schemas"][schema_name]
    assert "channel_projection" in schema["required"]
    assert "channel_mapping" not in schema["properties"]
    assert schema["properties"]["channel_projection"]["discriminator"]["propertyName"] == "mode"


@pytest.mark.parametrize("expected", [400, 404])
def test_get_ome_structure_errors(fxt_get_project, fxt_media_service, fxt_client, expected):
    media_id = uuid4()
    fxt_media_service.get_ome_image_info.side_effect = (
        ValueError("Media is not an OME image.")
        if expected == 400
        else ResourceNotFoundError(ResourceType.MEDIA, str(media_id))
    )
    response = fxt_client.get(f"/api/projects/{fxt_get_project.id}/dataset/media/{media_id}/ome")
    assert response.status_code == expected


def test_get_channel_view(fxt_get_project, fxt_rendering_service, fxt_client):
    media_id = uuid4()
    view = OmeChannelView(**parse_channel_override("0|0:255$ffffff").model_dump(), is_default=True)
    fxt_rendering_service.get_channel_view.return_value = view
    response = fxt_client.get(f"/api/projects/{fxt_get_project.id}/dataset/media/{media_id}/channel-view")
    assert response.status_code == 200
    assert response.json() == view.model_dump(mode="json")
    fxt_rendering_service.get_channel_view.assert_called_once_with(fxt_get_project.id, media_id)


def test_set_channel_view(fxt_get_project, fxt_rendering_service, fxt_client):
    media_id = uuid4()
    body = parse_channel_override("0|0:255$ffffff")
    view = OmeChannelView(**body.model_dump(), is_default=False)
    fxt_rendering_service.set_channel_view.return_value = view
    response = fxt_client.put(
        f"/api/projects/{fxt_get_project.id}/dataset/media/{media_id}/channel-view",
        json=body.model_dump(mode="json"),
    )
    assert response.status_code == 200
    assert response.json() == view.model_dump(mode="json")
    fxt_rendering_service.set_channel_view.assert_called_once_with(fxt_get_project.id, media_id, body)


@pytest.mark.parametrize("is_default", [False, True])
def test_channel_view_response_preserves_domain_fields(is_default):
    view = OmeChannelView(**parse_channel_override("0|0:255$ffffff").model_dump(), is_default=is_default)
    response = OmeChannelViewResponse.model_validate(view, from_attributes=True)
    assert response.model_dump(mode="json") == view.model_dump(mode="json")
    assert type(response) is OmeChannelViewResponse


def test_channel_view_openapi_uses_api_response_schema(fxt_app):
    spec = fxt_app.openapi()
    path = spec["paths"]["/api/projects/{project_id}/dataset/media/{media_id}/channel-view"]
    for method in ("get", "put"):
        response = path[method]["responses"]["200"]["content"]["application/json"]["schema"]
        assert response == {"$ref": "#/components/schemas/OmeChannelViewResponse"}
    schema = spec["components"]["schemas"]["OmeChannelViewResponse"]
    assert set(schema["properties"]) == {"settings", "is_default"}
    assert set(schema["required"]) == {"settings", "is_default"}


@pytest.mark.parametrize(
    "settings",
    [
        [{"channel": -1, "color": "#FFFFFF", "window_min": 0, "window_max": 1}],
        [{"channel": 0, "color": "#FFFFFF", "window_min": 1, "window_max": 1}],
        [{"channel": 0, "color": "#FFFFFF", "window_min": 2, "window_max": 1}],
        [{"channel": 0, "color": "white", "window_min": 0, "window_max": 1}],
        [{"channel": 0, "color": "#FFFFFF", "window_min": 0, "window_max": 1}] * 2,
    ],
)
def test_set_channel_view_validation(fxt_get_project, fxt_rendering_service, fxt_client, settings):
    response = fxt_client.put(
        f"/api/projects/{fxt_get_project.id}/dataset/media/{uuid4()}/channel-view", json={"settings": settings}
    )
    assert response.status_code == 422
    fxt_rendering_service.set_channel_view.assert_not_called()


@pytest.mark.parametrize(
    ("method", "error", "expected"),
    [
        ("get", ValueError("not OME"), 400),
        ("put", ValueError("not OME"), 400),
        ("get", ResourceNotFoundError(ResourceType.MEDIA, str(uuid4())), 404),
        ("put", ResourceNotFoundError(ResourceType.MEDIA, str(uuid4())), 404),
        ("put", InvalidChannelViewError("outside SizeC"), 422),
        ("get", InvalidImageError("unreadable pixels"), 422),
    ],
)
def test_channel_view_errors(fxt_get_project, fxt_rendering_service, fxt_client, method, error, expected):
    service_method = (
        fxt_rendering_service.get_channel_view if method == "get" else fxt_rendering_service.set_channel_view
    )
    service_method.side_effect = error
    response = fxt_client.request(
        method,
        f"/api/projects/{fxt_get_project.id}/dataset/media/{uuid4()}/channel-view",
        **({"json": {"settings": []}} if method == "put" else {}),
    )
    assert response.status_code == expected


@pytest.mark.parametrize("override", [None, "", "0|0:255$FFFFFF"])
def test_render_png_and_cache_headers(fxt_get_project, fxt_rendering_service, fxt_client, override):
    media_id = uuid4()
    buffer = BytesIO()
    PILImage.new("RGB", (4, 3), "red").save(buffer, format="PNG")
    content = buffer.getvalue()
    fxt_rendering_service.resolve_render.return_value.etag = '"render-key"'
    fxt_rendering_service.render.return_value = content
    params = {"z": 1, "t": 2, "level": 3, "max_size": 256}
    if override is not None:
        params["c"] = override
    response = fxt_client.get(
        f"/api/projects/{fxt_get_project.id}/dataset/media/{media_id}/render",
        params=params,
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 200
    assert response.content == content
    assert response.headers["content-type"] == "image/png"
    assert response.headers["etag"] == '"render-key"'
    assert "ETag" in response.headers["access-control-expose-headers"]
    assert response.headers["cache-control"] == (
        "private, no-cache" if override is None else "private, max-age=31536000, immutable"
    )
    fxt_rendering_service.resolve_render.assert_called_once_with(
        fxt_get_project.id,
        media_id,
        z=1,
        t=2,
        level=3,
        max_size=256,
        override=None if override is None else parse_channel_override(override),
    )


@pytest.mark.parametrize("etag", ['"render-key"', 'W/"render-key"', '"old", W/"render-key"', "*"])
def test_render_revalidation_skips_rendering(fxt_get_project, fxt_rendering_service, fxt_client, etag):
    fxt_rendering_service.resolve_render.return_value.etag = '"render-key"'
    response = fxt_client.get(
        f"/api/projects/{fxt_get_project.id}/dataset/media/{uuid4()}/render", headers={"If-None-Match": etag}
    )
    assert response.status_code == 304
    assert response.content == b""
    assert response.headers["etag"] == '"render-key"'
    assert response.headers["cache-control"] == "private, no-cache"
    fxt_rendering_service.render.assert_not_called()


@pytest.mark.parametrize("override", ["bad", "0|1:0$FFFFFF", "0|0:1$INVALID"])
def test_render_bad_override(fxt_get_project, fxt_rendering_service, fxt_client, override):
    response = fxt_client.get(
        f"/api/projects/{fxt_get_project.id}/dataset/media/{uuid4()}/render", params={"c": override}
    )
    assert response.status_code == 400
    fxt_rendering_service.resolve_render.assert_not_called()


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (InvalidRenderSelectionError("out of range"), 422),
        (InvalidChannelViewError("outside SizeC"), 400),
        (ValueError("not OME"), 400),
        (ResourceNotFoundError(ResourceType.MEDIA, str(uuid4())), 404),
        (InvalidImageError("unreadable pixels"), 422),
    ],
)
def test_render_errors(fxt_get_project, fxt_rendering_service, fxt_client, error, expected):
    fxt_rendering_service.resolve_render.side_effect = error
    response = fxt_client.get(f"/api/projects/{fxt_get_project.id}/dataset/media/{uuid4()}/render")
    assert response.status_code == expected
    fxt_rendering_service.render.assert_not_called()


def test_render_decode_failure(fxt_get_project, fxt_rendering_service, fxt_client):
    fxt_rendering_service.resolve_render.return_value.etag = '"render-key"'
    fxt_rendering_service.render.side_effect = InvalidImageError("Cannot decode pixels.")
    response = fxt_client.get(f"/api/projects/{fxt_get_project.id}/dataset/media/{uuid4()}/render")
    assert response.status_code == 422
    assert response.json()["detail"] == "Cannot decode pixels."
