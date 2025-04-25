"""Tests the telemetry module."""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock
from unittest.mock import Mock, call

import pytest

import telemetry

_PATCHING_TARGET = "telemetry"


@pytest.mark.parametrize(
    "name, datetime_expected",
    (
        ("2023-01-20T15-33-50.705", datetime(2023, 1, 20, 15, 33, 50, 705000)),
        ("2022-12-30T10-00-00.000", datetime(2022, 12, 30, 10, 00, 00, 0)),
    ),
)
def test_datetime_from_otel_file_name_positive(name: str, datetime_expected: datetime):
    """Tests the datetime_from_otel_file_name function, positive case."""
    datetime_actual = telemetry._datetime_from_otel_file_name(name)

    assert datetime_actual == datetime_expected


@pytest.mark.parametrize(
    "name",
    (
        pytest.param("", id="empty-str"),
        pytest.param("metrics.json", id="no-timestamp"),
        pytest.param("2022-12-30T10-00-00", id="no-microseconds"),
    ),
)
def test_datetime_from_otel_file_name_negative(name: str):
    """Tests the datetime_from_otel_file_name function, negative case."""
    with pytest.raises(ValueError):
        telemetry._datetime_from_otel_file_name(name)


@pytest.mark.parametrize(
    "file_names_present, pattern, name_to_datetime_expected",
    (
        pytest.param(
            (
                "not_an_otel_file",
                "metrics_2023-01-20T11-22-33.000.json.gz",
                "metrics.json",
                "metrics_2023-01-20T15-20-09.412.json",
            ),
            f"*.{telemetry._FILE_EXT_JSON_GZ}",
            {
                "metrics_2023-01-20T11-22-33.000.json.gz": datetime(2023, 1, 20, 11, 22, 33, 0),
            },
            id="non-empty-result",
        ),
        pytest.param(
            ("foo", "metrics.json", "metrics.json.zst"),
            f"*.{telemetry._FILE_EXT_JSON_GZ}",
            {},
            id="empty-result",
        ),
    ),
)
def test_get_path_to_datetime(
    tmp_path: Path,
    file_names_present: Sequence[str],
    pattern: str,
    name_to_datetime_expected: Mapping[str, datetime],
):
    """Tests the _get_path_to_datetime function."""
    for name in file_names_present:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()

    path_to_datetime_expected: Mapping[Path, datetime] = {
        tmp_path / name: timestamp for name, timestamp in name_to_datetime_expected.items()
    }

    path_to_datetime_actual: Mapping[Path, datetime] = telemetry._get_path_to_datetime(tmp_path, pattern=pattern)

    assert path_to_datetime_actual == path_to_datetime_expected


@pytest.mark.parametrize(
    "rel_paths_present, pattern, dt_to_rel_paths_expected",
    (
        pytest.param(
            (
                "not_an_otel_file",
                "metrics_2023-01-20T11-22-33.000.json.gz",
                "subdir/metrics_2023-01-20T11-22-33.000.json.gz",
                "metrics_2025-01-20T11-22-33.000.json.gz",
                "metrics.json",
                "metrics_2023-01-20T15-20-09.412.json",
            ),
            f"*.{telemetry._FILE_EXT_JSON_GZ}",
            {
                datetime(2023, 1, 20, 11, 22, 33, 0): {
                    "metrics_2023-01-20T11-22-33.000.json.gz",
                    "subdir/metrics_2023-01-20T11-22-33.000.json.gz",
                },
                datetime(2025, 1, 20, 11, 22, 33, 0): {"metrics_2025-01-20T11-22-33.000.json.gz"},
            },
            id="non-empty-result",
        ),
        pytest.param(
            ("foo", "metrics.json", "metrics.json.zst"),
            f"*.{telemetry._FILE_EXT_JSON_GZ}",
            {},
            id="empty-result",
        ),
    ),
)
def test_get_datetime_to_paths(
    tmp_path: Path,
    rel_paths_present: Sequence[str],
    pattern: str,
    dt_to_rel_paths_expected: Mapping[datetime, set[Path]],
):
    """Tests the _get_datetime_to_paths function."""
    for rel_path in rel_paths_present:
        path = tmp_path / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()

    dt_to_paths_expected: dict[datetime, set[Path]] = {}
    for dtime, rel_paths in dt_to_rel_paths_expected.items():
        abs_paths = {tmp_path / elem for elem in rel_paths}
        dt_to_paths_expected[dtime] = abs_paths

    dt_to_path_actual: Mapping[datetime, set[Path]] = telemetry._get_datetime_to_paths(tmp_path, pattern=pattern)

    assert dt_to_path_actual == dt_to_paths_expected


@pytest.mark.parametrize(
    "names_present, names_expected_post_delete, retention",
    (
        pytest.param(
            (
                "not_an_otel_file",
                "metrics.json",
                "subdir/metrics.json",
                "metrics-2023-01-10T11-22-33.000.json.gz",
                "metrics-2023-01-09T11-22-33.000.json.gz",
                "metrics-2023-01-08T11-22-33.000.json.gz",
                "metrics-2023-01-05T11-22-33.000.json.gz",
                "metrics-2023-01-01T11-22-33.000.json",
                "metrics-2023-01-09T11-22-33.000.json",
                "subdir/metrics-2023-01-05T11-22-33.000.json.gz",
                "subdir/metrics-2023-01-09T11-22-33.000.json",
            ),
            (
                # Should persist due to not containing a timestamp to evaluate retention against.
                "not_an_otel_file",
                "metrics.json",
                "subdir/metrics.json",
                # Should persist due to being within the retention time period (+1 day)
                "metrics-2023-01-10T11-22-33.000.json.gz",
                "metrics-2023-01-09T11-22-33.000.json.gz",
                "subdir/metrics-2023-01-09T11-22-33.000.json",
                # Should persist due to not being compressed.
                "metrics-2023-01-01T11-22-33.000.json",
                "metrics-2023-01-09T11-22-33.000.json",
            ),
            1,
            id="non-empty-result",
        ),
        pytest.param(
            ("foo", "metrics.json", "metrics.json.zst"),
            ("foo", "metrics.json", "metrics.json.zst"),
            1,
            id="empty-result",
        ),
    ),
)
def test_delete_in_single_backup_dir(
    mocker,
    tmp_path: Path,
    names_present: Sequence[str],
    names_expected_post_delete: Sequence[str],
    retention: int,
):
    """Tests the _delete_in_single_backup_dir function."""
    datetime_mock = mocker.patch.object(telemetry, "datetime", Mock(wraps=datetime))
    datetime_mock.utcnow.return_value = datetime(2023, 1, 10, 1, 1, 1, 0)
    paths_expected_post_delete: Sequence[Path] = [tmp_path / name for name in names_expected_post_delete]
    for name in names_present:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()

    telemetry._delete_in_single_backup_dir(backup_dir=tmp_path, retention=retention)

    paths_actual_post_delete = {path for path in tmp_path.rglob("*") if path.is_file()}

    assert set(paths_actual_post_delete) == set(paths_expected_post_delete)


def test_cleanup_expired_telemetry_samples(mocker):
    """Tests the _cleanup_expired_telemetry_samples function."""
    del_in_single_dir_mock = mocker.patch(f"{_PATCHING_TARGET}._delete_in_single_backup_dir")
    retention_days_geti = timedelta(days=123)
    mocker.patch(f"{_PATCHING_TARGET}._GETI_TELEMETRY_RETENTION_DAYS", retention_days_geti)
    retention_days_k8s = timedelta(days=456)
    mocker.patch(f"{_PATCHING_TARGET}._K8S_TELEMETRY_RETENTION_DAYS", retention_days_k8s)

    telemetry._cleanup_expired_telemetry_samples()

    calls_expected = [
        call(backup_dir=Path("/mnt/logs/geti"), retention=retention_days_geti),
        call(backup_dir=Path("/mnt/logs/k8s"), retention=retention_days_k8s),
    ]

    del_in_single_dir_mock.assert_has_calls(
        calls_expected,
        any_order=True,
    )
    assert del_in_single_dir_mock.call_count == len(calls_expected)


@pytest.mark.parametrize(
    "dt_to_paths_rel, cleanup_time_limit, paths_rel_expected",
    (
        pytest.param(
            {
                datetime.utcnow() - timedelta(days=3): ["foo_minus_3d", "bar_minus_3d"],
                datetime.utcnow() - timedelta(days=2): ["foo_minus_2d", "bar_minus_2d"],
                datetime.utcnow() - timedelta(days=1, hours=1): ["foo_minus_1d1h", "bar_minus_1d1h"],
                datetime.utcnow() - timedelta(hours=1): ["foo_minus_1h", "bar_minus_1h"],
                datetime.utcnow(): ["foo_now", "bar_now"],
                datetime.utcnow() + timedelta(hours=1): ["foo_plus_1h", "bar_plus_1h"],
            },
            timedelta(days=1),
            [
                "foo_minus_3d",
                "bar_minus_3d",
                "foo_minus_2d",
                "bar_minus_2d",
                "foo_minus_1d1h",
                "bar_minus_1d1h",
            ],
            id="filter-out-some",
        ),
        pytest.param(
            {
                datetime.utcnow() - timedelta(days=3): ["foo_minus_3d", "bar_minus_3d"],
                datetime.utcnow() - timedelta(days=2): ["foo_minus_2d", "bar_minus_2d"],
                datetime.utcnow() - timedelta(days=1, hours=1): ["foo_minus_1d1h", "bar_minus_1d1h"],
            },
            timedelta(hours=1),
            [
                "foo_minus_3d",
                "bar_minus_3d",
                "foo_minus_2d",
                "bar_minus_2d",
                "foo_minus_1d1h",
                "bar_minus_1d1h",
            ],
            id="filter-out-none",
        ),
        pytest.param(
            {
                datetime.utcnow() - timedelta(days=3): ["foo_minus_3d", "bar_minus_3d"],
                datetime.utcnow() - timedelta(days=1, hours=1): ["foo_minus_1d1h", "bar_minus_1d1h"],
                datetime.utcnow() - timedelta(hours=1): ["foo_minus_1h", "bar_minus_1h"],
                datetime.utcnow(): ["foo_now", "bar_now"],
                datetime.utcnow() + timedelta(hours=1): ["foo_plus_1h", "bar_plus_1h"],
            },
            timedelta(days=100),
            [],
            id="filter-out-all",
        ),
        pytest.param(
            {},
            timedelta(days=1),
            [],
            id="empty-dt-to-paths",
        ),
    ),
)
def test_get_deletable_telemetry_files(
    mocker,
    tmp_path: Path,
    dt_to_paths_rel: Mapping[datetime, Sequence[str]],
    cleanup_time_limit: timedelta,
    paths_rel_expected: Sequence[Path],
):
    """Tests the _get_deletable_telemetry_files function."""
    dt_to_paths = {}
    for dtime, paths_rel in dt_to_paths_rel.items():
        dt_to_paths[dtime] = [tmp_path / rel_path for rel_path in paths_rel]

    paths_expected = [tmp_path / path_rel for path_rel in paths_rel_expected]

    mock_get_dt_to_paths = mocker.patch(f"{_PATCHING_TARGET}._get_datetime_to_paths", side_effect=[dt_to_paths])

    paths_actual = telemetry._get_deletable_telemetry_files(path_dir=tmp_path, cleanup_time_limit=cleanup_time_limit)

    assert list(paths_actual) == list(paths_expected)
    mock_get_dt_to_paths.assert_called_once_with(tmp_path, pattern="*.json.gz")


@pytest.mark.parametrize(
    "rel_paths_present, rel_paths_expected_post_delete, df_side_effects",
    (
        pytest.param(
            (
                "subdir_A/metrics-2000-01-10T11-22-33.000.json.gz",
                "subdir_B/metrics-2001-01-09T11-22-33.000.json.gz",
                "subdir_C/metrics-2002-01-08T11-22-33.000.json.gz",
                "subdir_A/metrics-2003-01-05T11-22-33.000.json.gz",
                "subdir_B/metrics-2004-01-05T11-22-33.000.json.gz",
            ),
            ("subdir_B/metrics-2004-01-05T11-22-33.000.json.gz",),
            (0, 1, 2, 3, 100),
            id="delete-some",
        ),
        pytest.param(
            (
                "subdir_A/metrics-2000-01-10T11-22-33.000.json.gz",
                "subdir_B/metrics-2001-01-09T11-22-33.000.json.gz",
                "subdir_C/metrics-2002-01-08T11-22-33.000.json.gz",
                "subdir_A/metrics-2003-01-05T11-22-33.000.json.gz",
                "subdir_B/metrics-2004-01-05T11-22-33.000.json.gz",
            ),
            (
                "subdir_A/metrics-2000-01-10T11-22-33.000.json.gz",
                "subdir_B/metrics-2001-01-09T11-22-33.000.json.gz",
                "subdir_C/metrics-2002-01-08T11-22-33.000.json.gz",
                "subdir_A/metrics-2003-01-05T11-22-33.000.json.gz",
                "subdir_B/metrics-2004-01-05T11-22-33.000.json.gz",
            ),
            (101,),
            id="delete-none",
        ),
        pytest.param(
            (
                "subdir_A/metrics-2000-01-10T11-22-33.000.json.gz",
                "subdir_B/metrics-2001-01-09T11-22-33.000.json.gz",
                "subdir_C/metrics-2002-01-08T11-22-33.000.json.gz",
                "subdir_A/metrics-2003-01-05T11-22-33.000.json.gz",
                "subdir_B/metrics-2004-01-05T11-22-33.000.json.gz",
            ),
            (),
            (1, 2, 3, 4, 5, 6),
            id="delete-all",
        ),
        pytest.param(
            (),
            (),
            (0,),
            id="nothing-to-delete",
        ),
    ),
)
def test_force_cleanup_telemetry_samples(
    mocker,
    rel_paths_present: Sequence[str],
    rel_paths_expected_post_delete: Sequence[str],
    df_side_effects: Sequence[int],
    tmp_path: Path,
):
    """Tests the _force_cleanup_telemetry_samples function."""
    cleanup_size_threshold = 100
    cleanup_time_limit = timedelta(days=-1)

    mock_get_disk_free = mocker.patch(f"{_PATCHING_TARGET}.storage.get_disk_free", side_effect=df_side_effects)
    paths_present = [tmp_path / rel_path for rel_path in rel_paths_present]
    mock_get_del_files = mocker.patch(
        f"{_PATCHING_TARGET}._get_deletable_telemetry_files",
        side_effect=[paths_present],
    )
    paths_remaining_expected = [tmp_path / rel_path for rel_path in rel_paths_expected_post_delete]

    for path in paths_present:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()

    telemetry._force_cleanup_telemetry_samples(
        path_dir=tmp_path,
        cleanup_size_threshold=cleanup_size_threshold,
        cleanup_time_limit=cleanup_time_limit,
    )

    paths_remaining_actual = [path for path in tmp_path.rglob("*") if path.is_file()]

    assert set(paths_remaining_actual) == set(paths_remaining_expected)
    mock_get_disk_free.assert_has_calls([mock.call(tmp_path)] * len(df_side_effects))
    mock_get_del_files.assert_called_once_with(path_dir=tmp_path, cleanup_time_limit=cleanup_time_limit)


@pytest.mark.asyncio
async def test_cleanup_telemetry_samples(mocker):
    """Tests the cleanup_telemetry_samples function."""
    del_expired_mock = mocker.patch(f"{_PATCHING_TARGET}._cleanup_expired_telemetry_samples")
    del_excess_mock = mocker.patch(f"{_PATCHING_TARGET}._force_cleanup_telemetry_samples")

    min_free_gib = 123
    mocker.patch(f"{_PATCHING_TARGET}._MIN_FREE_DISK_SPACE_GIB", min_free_gib)
    cleanup_thresh_gib = 456
    mocker.patch(f"{_PATCHING_TARGET}._TELEMETRY_CLEANUP_THRESHOLD", cleanup_thresh_gib)
    cleanup_limit = timedelta(hours=789)
    mocker.patch(f"{_PATCHING_TARGET}._TELEMETRY_CLEANUP_LIMIT", cleanup_limit)
    path_logs_dir = "some/path"
    mocker.patch(f"{_PATCHING_TARGET}.PATH_LOGS_DIR", path_logs_dir)
    telemetry_cleanup_enabled = "true"
    mocker.patch(f"{_PATCHING_TARGET}.ENABLE_TELEMETRY_CLEANUP", telemetry_cleanup_enabled)

    await telemetry.cleanup_telemetry_samples()

    del_expired_mock.assert_called_once_with()
    del_excess_mock.assert_called_once_with(
        path_dir=path_logs_dir,
        cleanup_size_threshold=cleanup_thresh_gib,
        cleanup_time_limit=cleanup_limit,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "enable_telemetry_cleanup",
    [
        "False",
        "0",
        "NOT TRUE",
    ],
)
async def test_do_not_cleanup_telemetry_samples(mocker, enable_telemetry_cleanup):
    cleanup_expired_telemetry_samples_mocker = mocker.patch(f"{_PATCHING_TARGET}._cleanup_expired_telemetry_samples")
    force_cleanup_telemetry_samples_mocker = mocker.patch(f"{_PATCHING_TARGET}._force_cleanup_telemetry_samples")

    telemetry_cleanup_enabled = enable_telemetry_cleanup
    mocker.patch(f"{_PATCHING_TARGET}.ENABLE_TELEMETRY_CLEANUP", telemetry_cleanup_enabled)

    await telemetry.cleanup_telemetry_samples()

    assert cleanup_expired_telemetry_samples_mocker.call_count == 0
    assert force_cleanup_telemetry_samples_mocker.call_count == 0


@pytest.mark.parametrize(
    "str_to_check,expected_result",
    [
        ("TRUE", True),
        ("YeS", True),
        ("1", True),
        ("0", False),
        ("NOT-TRUE", False),
        ("False", False),
    ],
)
def test_str_to_bool(str_to_check, expected_result):
    assert telemetry._str_to_bool(str_to_check=str_to_check) == expected_result


@pytest.mark.parametrize(
    "env_variable_value, default_value, expected_result",
    [
        ("", "5", 5),
        ("10", "5", 10),
    ],
)
def test_parse_env_variable_to_int(mocker, env_variable_value, default_value, expected_result):
    mocker.patch.dict(f"{_PATCHING_TARGET}.os.environ", {"SOME_ENV": env_variable_value}, clear=True)
    actual_result = telemetry._parse_env_variable_to_int(env_variable_name="SOME_ENV", default_value=default_value)

    assert expected_result == actual_result
