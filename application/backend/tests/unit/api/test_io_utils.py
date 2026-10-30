# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest

from app.api.io_utils import write_bytes_to_response


@pytest.mark.parametrize(
    "filename, expected",
    [
        pytest.param("image.png", 'inline; filename="image.png"', id="ascii"),
        pytest.param("my image.png", "inline; filename*=utf-8''my%20image.png", id="space"),
        pytest.param("café.png", "inline; filename*=utf-8''caf%C3%A9.png", id="latin1"),
        pytest.param("图像.png", "inline; filename*=utf-8''%E5%9B%BE%E5%83%8F.png", id="non_latin1"),
    ],
)
def test_write_bytes_to_response_content_disposition(filename: str, expected: str) -> None:
    response = write_bytes_to_response(content=b"data", filename=filename, media_type="image/png")

    assert response.headers["content-disposition"] == expected
