"""Tests the storage module."""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from pathlib import Path

import pytest

import storage

_PATCHING_TARGET = "app.storage"


@pytest.mark.parametrize(
    "size, bytes_expected",
    [
        ("0", 0),
        ("0B", 0),
        ("1", 1),
        ("1B", 1),
        ("123", 123),
        ("123B", 123),
        ("0 Ki", 0),
        ("0G", 0),
        ("1K", 10**3),
        ("1M", 10**6),
        ("1G", 10**9),
        ("1T", 10**12),
        ("1P", 10**15),
        ("1Ki", 2**10),
        ("1Mi", 2**20),
        ("1Gi", 2**30),
        ("1Ti", 2**40),
        ("1Pi", 2**50),
        ("K", 10**3),
        ("M", 10**6),
        ("G", 10**9),
        ("T", 10**12),
        ("P", 10**15),
        ("Ki", 2**10),
        ("Mi", 2**20),
        ("Gi", 2**30),
        ("Ti", 2**40),
        ("Pi", 2**50),
        ("2K", 2 * 10**3),
        ("2M", 2 * 10**6),
        ("2G", 2 * 10**9),
        ("2T", 2 * 10**12),
        ("2P", 2 * 10**15),
        ("2Ki", 2 * 2**10),
        ("2Mi", 2 * 2**20),
        ("2Gi", 2 * 2**30),
        ("2Ti", 2 * 2**40),
        ("2Pi", 2 * 2**50),
        ("2 Pi", 2 * 2**50),
        (" 2   Pi  ", 2 * 2**50),
    ],
)
def test_parse_size_to_bytes_positive(size: str, bytes_expected: int):
    """Tests the parse_size_to_bytes function, positive scenario."""
    bytes_actual: int = storage.parse_size_to_bytes(size)

    assert bytes_actual == bytes_expected


@pytest.mark.parametrize("size", ["", "foo", "1Kfoo", "123 Gi bar", "foo2M", "1fooMi"])
def test_parse_size_to_bytes_negative(size: str):
    """Tests the parse_size_to_bytes function, negative scenario."""
    with pytest.raises(ValueError):
        storage.parse_size_to_bytes(size)


def test_get_disk_free(mocker):
    """Tests the get_disk_free function."""
    disk_free_expected = 456
    mock_disk_usage = mocker.patch(f"{_PATCHING_TARGET}.shutil.disk_usage", side_effect=[(1, 2, disk_free_expected)])
    path = Path("some/path")

    disk_free_actual = storage.get_disk_free(path)

    assert disk_free_actual == disk_free_expected
    mock_disk_usage.assert_called_once_with(path)
