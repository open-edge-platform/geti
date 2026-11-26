# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Tests for CachedStaticFiles class."""

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.applications import Starlette
from starlette.routing import Mount

from app.api.cache_utils import CachedStaticFiles, StaticGZipMiddleware


@pytest.fixture
def static_dir(tmp_path):
    """Create a temporary directory with test static files."""
    (tmp_path / "app.js").write_text("console.log('hello');")
    (tmp_path / "style.css").write_text("body { color: red; }")
    (tmp_path / "opencv.wasm").write_bytes(b"\x00wasm")
    (tmp_path / "model.data").write_bytes(b"model data")
    (tmp_path / "image.png").write_bytes(b"PNG")
    (tmp_path / "font.woff2").write_bytes(b"woff2")
    (tmp_path / "index.html").write_text("<html></html>")
    (tmp_path / "readme.txt").write_text("hello")
    return tmp_path


@pytest.fixture
def app(static_dir):
    """Create a Starlette app with CachedStaticFiles mounted."""
    return Starlette(
        routes=[
            Mount("/static", CachedStaticFiles(directory=static_dir), name="static"),
        ]
    )


@pytest.mark.asyncio
async def test_js_cache_control(app, static_dir):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/static/app.js")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "public, max-age=31536000, immutable"


@pytest.mark.asyncio
async def test_css_cache_control(app, static_dir):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/static/style.css")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "public, max-age=31536000, immutable"


@pytest.mark.asyncio
async def test_wasm_cache_control(app, static_dir):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/static/opencv.wasm")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "public, max-age=31536000, immutable"


@pytest.mark.asyncio
async def test_data_cache_control(app, static_dir):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/static/model.data")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "public, max-age=31536000, immutable"


@pytest.mark.asyncio
async def test_image_cache_control(app, static_dir):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/static/image.png")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "public, max-age=604800"


@pytest.mark.asyncio
async def test_font_cache_control(app, static_dir):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/static/font.woff2")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "public, max-age=2592000, immutable"


@pytest.mark.asyncio
async def test_html_cache_control(app, static_dir):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/static/index.html")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-cache"


@pytest.mark.asyncio
async def test_fallback_cache_control(app, static_dir):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/static/readme.txt")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "public, max-age=3600"


# Above GZipMiddleware's 500-byte minimum so compression actually kicks in.
LARGE_CONTENT = b"geti " * 400


@pytest.fixture
def gzip_app(tmp_path):
    """Create a Starlette app serving large static files through StaticGZipMiddleware."""
    for name in ("app.js", "style.css", "ort.wasm", "image.png", "font.woff2", "model.onnx"):
        (tmp_path / name).write_bytes(LARGE_CONTENT)
    return Starlette(
        routes=[
            Mount("/static", StaticGZipMiddleware(CachedStaticFiles(directory=tmp_path)), name="static"),
        ]
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("filename", ["app.js", "style.css", "ort.wasm"])
async def test_gzip_compresses_text_like_assets(gzip_app, filename):
    async with AsyncClient(transport=ASGITransport(app=gzip_app), base_url="http://test") as client:
        response = await client.get(f"/static/{filename}", headers={"Accept-Encoding": "gzip"})
    assert response.status_code == 200
    assert response.headers["content-encoding"] == "gzip"
    assert "Accept-Encoding" in response.headers["vary"]
    assert response.headers["cache-control"] == "public, max-age=31536000, immutable"
    assert response.content == LARGE_CONTENT


@pytest.mark.asyncio
@pytest.mark.parametrize("filename", ["image.png", "font.woff2", "model.onnx"])
async def test_gzip_skips_already_compressed_assets(gzip_app, filename):
    async with AsyncClient(transport=ASGITransport(app=gzip_app), base_url="http://test") as client:
        response = await client.get(f"/static/{filename}", headers={"Accept-Encoding": "gzip"})
    assert response.status_code == 200
    assert "content-encoding" not in response.headers
    assert response.content == LARGE_CONTENT


@pytest.mark.asyncio
async def test_gzip_skipped_when_client_does_not_accept_it(gzip_app):
    async with AsyncClient(transport=ASGITransport(app=gzip_app), base_url="http://test") as client:
        response = await client.get("/static/app.js", headers={"Accept-Encoding": "identity"})
    assert response.status_code == 200
    assert "content-encoding" not in response.headers
    assert response.content == LARGE_CONTENT


@pytest.mark.asyncio
async def test_gzip_skipped_for_range_requests(gzip_app):
    async with AsyncClient(transport=ASGITransport(app=gzip_app), base_url="http://test") as client:
        response = await client.get("/static/ort.wasm", headers={"Accept-Encoding": "gzip", "Range": "bytes=0-999"})
    assert response.status_code == 206
    assert "content-encoding" not in response.headers
    assert response.headers["content-range"] == f"bytes 0-999/{len(LARGE_CONTENT)}"
    assert response.content == LARGE_CONTENT[:1000]
