# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Tests for CachedStaticFiles class."""

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.applications import Starlette
from starlette.routing import Mount

from app.api.cache_utils import CachedStaticFiles

IMMUTABLE = "public, max-age=31536000, immutable"
REVALIDATE = "no-cache"


@pytest.fixture
def client(tmp_path):
    """Serve a temporary directory that mirrors the UI build output."""
    for name in (
        "static/js/index.be24d2808a.js",
        "static/css/index.88bedbc0a4.css",
        "static/svg/selection.478715623d.svg",
        "static/assets/sam_vit_h_4b8939.decoder.a1d6775264.onnx",
        "static/js/lib-react.8cd563e1f5.js.LICENSE.txt",
        "opencv/opencv.js",
        "ort/ort-wasm-simd-threaded.jsep.wasm",
        "favicon.ico",
        "index.html",
    ):
        file = tmp_path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(b"content")

    app = Starlette(routes=[Mount("/static", CachedStaticFiles(directory=tmp_path), name="static")])
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "cache_control"),
    [
        ("static/js/index.be24d2808a.js", IMMUTABLE),
        ("static/css/index.88bedbc0a4.css", IMMUTABLE),
        ("static/svg/selection.478715623d.svg", IMMUTABLE),
        ("static/assets/sam_vit_h_4b8939.decoder.a1d6775264.onnx", IMMUTABLE),
        # Not fingerprinted: same URL across releases.
        ("static/js/lib-react.8cd563e1f5.js.LICENSE.txt", REVALIDATE),
        ("opencv/opencv.js", REVALIDATE),
        ("ort/ort-wasm-simd-threaded.jsep.wasm", REVALIDATE),
        ("favicon.ico", REVALIDATE),
        ("index.html", REVALIDATE),
    ],
)
async def test_cache_control(client, path, cache_control):
    async with client:
        response = await client.get(f"/static/{path}")

    assert response.status_code == 200
    assert response.headers["cache-control"] == cache_control


@pytest.mark.asyncio
async def test_unchanged_file_revalidates_without_body(client):
    async with client:
        first = await client.get("/static/ort/ort-wasm-simd-threaded.jsep.wasm")
        second = await client.get(
            "/static/ort/ort-wasm-simd-threaded.jsep.wasm", headers={"If-None-Match": first.headers["etag"]}
        )

    assert second.status_code == 304
    assert second.content == b""
