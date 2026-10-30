# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import pytest

from app.api.io_utils import file_etag, is_not_modified, write_bytes_to_response

OPAQUE_TAG = '"display-png-v1-abc-10"'
ETAG = f"W/{OPAQUE_TAG}"


@pytest.mark.parametrize(
    "filename, expected",
    [
        pytest.param("image.png", 'inline; filename="image.png"', id="ascii"),
        pytest.param("my image.png", "inline; filename*=utf-8''my%20image.png", id="space"),
        pytest.param("a/b.png", "inline; filename*=utf-8''a%2Fb.png", id="slash"),
        pytest.param("café.png", "inline; filename*=utf-8''caf%C3%A9.png", id="latin1"),
        pytest.param("图像.png", "inline; filename*=utf-8''%E5%9B%BE%E5%83%8F.png", id="non_latin1"),
    ],
)
def test_write_bytes_to_response_content_disposition(filename: str, expected: str) -> None:
    response = write_bytes_to_response(content=b"data", filename=filename, media_type="image/png")

    assert response.headers["content-disposition"] == expected


def test_file_etag_changes_with_file_and_variant(tmp_path: Path) -> None:
    path = tmp_path / "image.tif"
    path.write_bytes(b"original")
    etag = file_etag(path, variant="a")

    assert etag.startswith('W/"a-') and etag.endswith('"')
    assert file_etag(path, variant="a") == etag
    assert file_etag(path, variant="b") != etag

    path.write_bytes(b"modified content")
    assert file_etag(path, variant="a") != etag


@pytest.mark.parametrize(
    "if_none_match, expected",
    [
        pytest.param(None, False, id="no_header"),
        pytest.param(ETAG, True, id="exact"),
        pytest.param(OPAQUE_TAG, True, id="without_weak_prefix"),
        pytest.param(f'"other", {ETAG}', True, id="list"),
        pytest.param("*", True, id="wildcard"),
        pytest.param('"other"', False, id="mismatch"),
    ],
)
def test_is_not_modified(if_none_match: str | None, expected: bool) -> None:
    assert is_not_modified(if_none_match, ETAG) is expected
