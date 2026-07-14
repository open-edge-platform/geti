# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for application-data version tracking."""

from pathlib import Path

import pytest

from app.upgrade.data_version import (
    DATA_VERSION_FILE,
    INITIAL_DATA_VERSION,
    is_newer,
    parse_version,
    read_data_version,
    write_data_version,
)


class TestParseVersion:
    @pytest.mark.parametrize(
        ("version", "expected"),
        [
            ("3.0.0", (3, 0, 0)),
            ("3.1.0", (3, 1, 0)),
            ("10.2.3", (10, 2, 3)),
            ("3.1.0rc1", (3, 1, 0)),  # pre-release suffix ignored
            ("3.1.0+cuda", (3, 1, 0)),  # build metadata ignored
            ("  4.0.1  ", (4, 0, 1)),  # surrounding whitespace stripped
            ("garbage", (0,)),  # no numeric component
        ],
    )
    def test_parse_version(self, version: str, expected: tuple[int, ...]) -> None:
        assert parse_version(version) == expected

    def test_ordering(self) -> None:
        assert parse_version("3.2.0") > parse_version("3.1.9")
        assert parse_version("3.1.0") == parse_version("3.1.0rc2")

    def test_is_newer(self) -> None:
        assert is_newer("3.1.0", "3.0.0") is True
        assert is_newer("3.0.0", "3.0.0") is False
        assert is_newer("3.0.0", "3.1.0") is False


class TestDataVersionRoundtrip:
    def test_write_then_read(self, tmp_path: Path) -> None:
        db_path = tmp_path / "geti.db"
        write_data_version(tmp_path, "3.1.0")
        assert (tmp_path / DATA_VERSION_FILE).read_text(encoding="utf-8").strip() == "3.1.0"
        assert read_data_version(tmp_path, db_path) == "3.1.0"

    def test_write_is_atomic_no_tmp_leftover(self, tmp_path: Path) -> None:
        write_data_version(tmp_path, "3.1.0")
        leftovers = list(tmp_path.glob(f"{DATA_VERSION_FILE}.tmp"))
        assert leftovers == []


class TestReadDataVersion:
    def test_fresh_install_returns_none(self, tmp_path: Path) -> None:
        db_path = tmp_path / "geti.db"  # does not exist
        assert read_data_version(tmp_path, db_path) is None

    def test_existing_db_without_stamp_uses_baseline(self, tmp_path: Path) -> None:
        db_path = tmp_path / "geti.db"
        db_path.write_bytes(b"SQLite format 3\x00")  # DB exists, no stamp
        assert read_data_version(tmp_path, db_path) == INITIAL_DATA_VERSION

    def test_stamp_takes_precedence_over_baseline(self, tmp_path: Path) -> None:
        db_path = tmp_path / "geti.db"
        db_path.write_bytes(b"SQLite format 3\x00")
        write_data_version(tmp_path, "3.2.0")
        assert read_data_version(tmp_path, db_path) == "3.2.0"

    def test_empty_stamp_falls_back_to_baseline_when_db_exists(self, tmp_path: Path) -> None:
        db_path = tmp_path / "geti.db"
        db_path.write_bytes(b"SQLite format 3\x00")
        (tmp_path / DATA_VERSION_FILE).write_text("   \n", encoding="utf-8")
        assert read_data_version(tmp_path, db_path) == INITIAL_DATA_VERSION
