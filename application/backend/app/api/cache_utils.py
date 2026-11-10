# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Custom StaticFiles handler that adds Cache-Control headers to static asset responses."""

import re

from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from starlette.types import Scope

# The UI build (rsbuild) fingerprints its output as `<name>.<10-char content hash>.<ext>`.
_FINGERPRINTED_FILE = re.compile(r"\.[0-9a-f]{10}\.[^./]+$")


class CachedStaticFiles(StaticFiles):
    """StaticFiles subclass that caches fingerprinted assets forever and revalidates everything else.

    A fingerprinted file gets a new name whenever its content changes, so it can be cached immutably.
    Any other file (``index.html``, ``favicon.ico``, or files copied verbatim such as ``opencv/opencv.js``
    and ``ort/*.wasm``) keeps its URL across releases, so it must be revalidated via ETag; otherwise
    browsers keep serving a stale copy after an upgrade.
    """

    async def get_response(self, path: str, scope: Scope) -> Response:
        """Get the response with a Cache-Control header based on whether the file name is fingerprinted."""
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = (
            "public, max-age=31536000, immutable" if _FINGERPRINTED_FILE.search(path) else "no-cache"
        )
        return response
