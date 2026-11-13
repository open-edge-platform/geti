# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Static asset serving: Cache-Control headers and on-the-fly gzip compression."""

from fastapi.staticfiles import StaticFiles
from starlette.datastructures import Headers
from starlette.middleware.gzip import GZipMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

# Images, fonts and ONNX weights are already compressed; gzipping them burns CPU for little to no gain.
GZIP_EXTENSIONS = (".html", ".js", ".mjs", ".css", ".json", ".svg", ".txt", ".wasm")


class CachedStaticFiles(StaticFiles):
    """StaticFiles subclass that sets Cache-Control headers based on file extension."""

    CACHE_RULES: list[tuple[tuple[str, ...], str]] = [
        # Fingerprinted JS/CSS bundles — safe to cache for one year
        ((".js", ".css"), "public, max-age=31536000, immutable"),
        # WebAssembly + OpenCV — large binary assets cached immutably for one year
        ((".wasm",), "public, max-age=31536000, immutable"),
        # OpenCV data files (e.g. haarcascades, trained models)
        ((".data", ".mem"), "public, max-age=31536000, immutable"),
        # Images
        ((".png", ".jpg", ".jpeg", ".webp", ".svg", ".ico"), "public, max-age=604800"),
        # Fonts — rarely change, safe to cache for 30 days
        ((".woff", ".woff2", ".ttf", ".otf"), "public, max-age=2592000, immutable"),
        # HTML — always revalidate so users get fresh asset references
        ((".html",), "no-cache"),
    ]

    async def get_response(self, path: str, scope: Scope) -> Response:
        """Get response with appropriate Cache-Control header based on file extension."""
        response = await super().get_response(path, scope)
        for extensions, cache_value in self.CACHE_RULES:
            if path.endswith(extensions):
                response.headers["Cache-Control"] = cache_value
                break
        else:
            # Fallback for anything not explicitly matched
            response.headers["Cache-Control"] = "public, max-age=3600"
        return response


class StaticGZipMiddleware(GZipMiddleware):
    """Gzip text-like static assets for clients that accept it; other requests pass through untouched."""

    def __init__(self, app: ASGIApp) -> None:
        # Level 6 compresses as well as the default 9 for our bundles at roughly half the CPU cost.
        super().__init__(app, compresslevel=6)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Compress only whole-file responses of compressible asset types."""
        # GZipMiddleware would compress a 206 body while keeping the identity Content-Range.
        if scope["type"] == "http" and scope["path"].endswith(GZIP_EXTENSIONS) and "range" not in Headers(scope=scope):
            await super().__call__(scope, receive, send)
        else:
            await self.app(scope, receive, send)
