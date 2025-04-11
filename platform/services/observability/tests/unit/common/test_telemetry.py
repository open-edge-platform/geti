# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Unit tests for the common.telemetry module.
"""

from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from unittest import mock
from unittest.mock import Mock

import pytest

from common.telemetry import _PATH_TELEMETRY_ROOT as PATH_TELEMETRY_ROOT
from common.telemetry import DateError, LogType, _datetime_from_otel_file_name, get_archive
from common.telemetry import _archive_logs as archive_logs
from common.telemetry import _fallback_datetime_range as fallback_datetime_range
from common.telemetry import _filter_files_by_datetime as filter_files_by_datetime
from common.telemetry import _gen_archive_name as gen_archive_name
from common.telemetry import _get_archive_sources as get_archive_sources
from common.telemetry import _get_file_overlapping as get_file_overlapping
from common.telemetry import _get_rel_source_dirs as get_source_dirs
from common.telemetry import _sanitize_datetime_range as sanitize_date_range

_PATCHING_TARGET = "common.telemetry"


def test_get_archive_type_cluster(mocker):
    """Tests the _get_archive function against LogType.CLUSTER."""
    path_archive_mock = "/path/archive.tar.gz"
    prepare_cluster_info_dump_mock = mocker.patch(f"{_PATCHING_TARGET}.prepare_cluster_info_dump")
    prepare_cluster_info_dump_mock.return_value = path_archive_mock
    prepare_archive_logs = mocker.patch(f"{_PATCHING_TARGET}._archive_logs")

    path_archive_actual = get_archive(LogType.CLUSTER, start=None, end=None)

    prepare_cluster_info_dump_mock.assert_called_once_with()
    prepare_archive_logs.assert_not_called()
    assert path_archive_actual == Path(path_archive_mock)


@pytest.mark.parametrize(
    "log_type,archive_logs_log_types_expected",
    (
        pytest.param(LogType.GETI_LOGS, (LogType.GETI_LOGS,), id="logs"),
        pytest.param(LogType.GETI_TRACES, (LogType.GETI_TRACES,), id="traces"),
        pytest.param(LogType.GETI_METRICS, (LogType.GETI_METRICS,), id="metrics"),
        pytest.param(
            None,
            (LogType.GETI_LOGS, LogType.GETI_TRACES, LogType.GETI_METRICS, LogType.K8S_LOGS, LogType.K8S_METRICS),
            id="None",
        ),
    ),
)
def test_get_archive_type_non_cluster(mocker, log_type: LogType, archive_logs_log_types_expected: tuple[LogType]):
    """Tests the _get_archive function against non-cluster log types."""
    path_archive_mock = Path("/path/archive.tar.gz")
    prepare_cluster_info_dump_mock = mocker.patch(f"{_PATCHING_TARGET}.prepare_cluster_info_dump")
    start_dt_mock = Mock(datetime)
    end_dt_mock = Mock(datetime)
    start_dt_sanitized = Mock(datetime)
    end_dt_sanitized = Mock(datetime)
    sanitize_date_range_mock = mocker.patch(
        f"{_PATCHING_TARGET}._sanitize_datetime_range", side_effect=[(start_dt_sanitized, end_dt_sanitized)]
    )
    prepare_archive_logs = mocker.patch(f"{_PATCHING_TARGET}._archive_logs")
    prepare_archive_logs.return_value = path_archive_mock

    path_archive_actual = get_archive(log_type=log_type, start=start_dt_mock, end=end_dt_mock)

    sanitize_date_range_mock.assert_called_once_with(start=start_dt_mock, end=end_dt_mock)
    prepare_archive_logs.assert_called_once_with(
        telemetry_root=PATH_TELEMETRY_ROOT,
        log_types=archive_logs_log_types_expected,
        start=start_dt_sanitized,
        end=end_dt_sanitized,
    )
    prepare_cluster_info_dump_mock.assert_not_called()
    assert path_archive_actual == path_archive_mock


@pytest.mark.parametrize(
    "log_types,start,end,prefix_expected",
    (
        pytest.param(
            (LogType.GETI_LOGS,),
            datetime(10, 1, 1).astimezone(),
            datetime(20, 2, 2).astimezone(),
            "logs",
            id="logs_start-None_end-None",
        ),
        pytest.param(
            (LogType.GETI_TRACES,),
            datetime(10, 1, 1).astimezone(),
            datetime(20, 2, 2).astimezone(),
            "traces",
            id="traces",
        ),
        pytest.param(
            (LogType.GETI_METRICS,),
            datetime(10, 1, 1).astimezone(),
            datetime(20, 2, 2).astimezone(),
            "metrics",
            id="metrics",
        ),
        pytest.param(
            (LogType.K8S_LOGS,),
            datetime(10, 1, 1).astimezone(),
            datetime(20, 2, 2).astimezone(),
            "k8s_logs",
            id="k8s_logs",
        ),
        pytest.param(
            (LogType.K8S_METRICS,),
            datetime(10, 1, 1).astimezone(),
            datetime(20, 2, 2).astimezone(),
            "k8s_metrics",
            id="k8s_metrics",
        ),
        pytest.param(
            (LogType.GETI_LOGS, LogType.GETI_TRACES, LogType.GETI_METRICS),
            None,
            None,
            "logs-traces-metrics",
            id="logs-traces-metrics",
        ),
        pytest.param(
            (LogType.K8S_LOGS, LogType.K8S_METRICS), None, None, "k8s_logs-k8s_metrics", id="k8s_logs-k8s_metrics"
        ),
    ),
)
def test_archive_logs(log_types: tuple[LogType], start: datetime, end: datetime, prefix_expected: str, mocker):
    """Tests the _archive_logs function."""
    archive_name_mock = "archive_name_mock.tar.gz"
    path_archive_mock = Path(f"/tmp/{archive_name_mock}")
    sources_mock = {"/abs/src_a": "/rel/src_a", "/abs/src_b": "/rel/src_b"}

    gen_archive_name_mock = mocker.patch(f"{_PATCHING_TARGET}._gen_archive_name", return_value=archive_name_mock)
    get_archive_sources_mock = mocker.patch(f"{_PATCHING_TARGET}._get_archive_sources", return_value=sources_mock)
    create_archive_mock = mocker.patch(f"{_PATCHING_TARGET}._create_archive")

    path_archive_actual = archive_logs(telemetry_root=PATH_TELEMETRY_ROOT, log_types=log_types, start=start, end=end)

    assert path_archive_actual == path_archive_mock
    gen_archive_name_mock.assert_called_once_with(prefix=prefix_expected)
    create_archive_mock.assert_called_once_with(path_archive=path_archive_mock, path_src_to_arc=sources_mock)
    get_archive_sources_mock.assert_called_once_with(
        telemetry_root=PATH_TELEMETRY_ROOT, log_types=log_types, start=start, end=end
    )


@pytest.mark.parametrize(
    "start, end, install_dt",
    [
        pytest.param(
            datetime.today().astimezone() + timedelta(days=2),
            datetime.today().astimezone() + timedelta(days=3),
            datetime.today().astimezone() + timedelta(days=4),
            id="end-before-install",
        ),
        pytest.param(
            datetime.today().astimezone() + timedelta(days=2),
            datetime.today().astimezone() + timedelta(days=3),
            datetime.today().astimezone(),
            id="start-after-today",
        ),
    ],
)
def test_get_archive_sources_outside_date_bounds(
    mocker, tmp_path: Path, start: datetime, end: datetime, install_dt: date
):
    """Tests the _get_archive_sources function.

    Covers the scenario in which the provided date range ends before the platform installation date.
    """
    get_installation_dt_mock = mocker.patch(f"{_PATCHING_TARGET}.get_installation_datetime", side_effect=[install_dt])
    actual = get_archive_sources(telemetry_root=tmp_path, log_types=[], start=start, end=end)

    assert actual == {}

    get_installation_dt_mock.assert_called_once_with()


@pytest.mark.parametrize(
    "install_dt, now_dt, start_input, end_input, start_trimmed, end_trimmed",
    [
        pytest.param(
            datetime.combine(date.today(), time.min).astimezone() + timedelta(days=-6),
            datetime.combine(date.today(), time.min).astimezone() + timedelta(days=-2),
            datetime.combine(date.today(), time.min).astimezone() + timedelta(days=-4),
            datetime.combine(date.today(), time.min).astimezone() + timedelta(days=-2),
            datetime.combine(date.today(), time.min).astimezone() + timedelta(days=-4),
            datetime.combine(date.today(), time.min).astimezone() + timedelta(days=-2),
            id="no-trim",
        ),
        pytest.param(
            datetime.combine(date.today(), time.min).astimezone() + timedelta(days=-4),
            datetime.combine(date.today(), time.min).astimezone() + timedelta(days=-2),
            datetime.combine(date.today(), time.min).astimezone() + timedelta(days=-8),
            datetime.combine(date.today(), time.min).astimezone() + timedelta(days=-3),
            datetime.combine(date.today(), time.min).astimezone() + timedelta(days=-4),
            datetime.combine(date.today(), time.min).astimezone() + timedelta(days=-3),
            id="trim-start",
        ),
        pytest.param(
            datetime.combine(date.today(), time.min).astimezone() + timedelta(days=-4),
            datetime.combine(date.today(), time.min).astimezone() + timedelta(days=0),
            datetime.combine(date.today(), time.min).astimezone() + timedelta(days=-2),
            datetime.combine(date.today(), time.min).astimezone() + timedelta(days=4),
            datetime.combine(date.today(), time.min).astimezone() + timedelta(days=-2),
            datetime.combine(date.today(), time.min).astimezone() + timedelta(days=0),
            id="trim-end",
        ),
        pytest.param(
            datetime.combine(date.today(), time.min).astimezone() + timedelta(days=-4),
            datetime.combine(date.today(), time.min).astimezone() + timedelta(days=0),
            datetime.combine(date.today(), time.min).astimezone() + timedelta(days=-8),
            datetime.combine(date.today(), time.min).astimezone() + timedelta(days=10),
            datetime.combine(date.today(), time.min).astimezone() + timedelta(days=-4),
            datetime.combine(date.today(), time.min).astimezone() + timedelta(days=0),
            id="trim-start-and-end",
        ),
    ],
)
def test_get_archive_sources_valid_dates(
    mocker,
    tmp_path: Path,
    install_dt: datetime,
    now_dt: datetime,
    start_input: datetime,
    end_input: datetime,
    start_trimmed: datetime,
    end_trimmed: datetime,
):
    """Tests the _get_archive_sources function, valid dates scenario."""
    log_types_mock = [LogType.GETI_LOGS, LogType.GETI_TRACES]

    path_dir_1 = Path("src_dir_1")
    path_dir_2 = Path("src_dir_2")
    telemetry_root_mock = tmp_path
    rel_src_dirs_mock = (path_dir_1, path_dir_2)
    for path in rel_src_dirs_mock:
        (telemetry_root_mock / path).mkdir()

    path_src_1 = Path("1_1.json")
    path_src_2 = Path("2_1.json")

    get_rel_src_dirs = mocker.patch(f"{_PATCHING_TARGET}._get_rel_source_dirs", side_effect=[rel_src_dirs_mock])
    get_installation_dt_mock = mocker.patch(
        f"{_PATCHING_TARGET}.get_installation_datetime",
        side_effect=[install_dt],
    )
    filter_files_by_dt_mock = mocker.patch(
        f"{_PATCHING_TARGET}._filter_files_by_datetime",
        side_effect=[[telemetry_root_mock / path_src_1], [telemetry_root_mock / path_src_2]],
    )
    get_now_tz_aware_mock = mocker.patch(f"{_PATCHING_TARGET}._get_now_tz_aware", side_effect=[now_dt])

    actual = get_archive_sources(
        telemetry_root=telemetry_root_mock, log_types=log_types_mock, start=start_input, end=end_input
    )

    assert actual == {telemetry_root_mock / path_src_1: path_src_1, telemetry_root_mock / path_src_2: path_src_2}
    get_rel_src_dirs.assert_called_once_with(log_types=log_types_mock)
    get_installation_dt_mock.assert_called_once_with()
    get_now_tz_aware_mock.assert_called_once_with()
    filter_files_by_dt_mock.assert_has_calls(
        [
            mock.call(path_dir=telemetry_root_mock / path_dir_1, start=start_trimmed, end=end_trimmed),
            mock.call(path_dir=telemetry_root_mock / path_dir_2, start=start_trimmed, end=end_trimmed),
        ]
    )


@pytest.mark.parametrize(
    "start_dt_input, end_dt_input, err_msg_sub_str",
    (
        pytest.param(
            datetime.max.replace(tzinfo=timezone.utc),
            datetime.min.replace(tzinfo=timezone.utc),
            "cannot be later than end date",
            id="out-of-order",
        ),
        pytest.param(
            datetime.min,
            datetime.max.replace(tzinfo=timezone.utc),
            "must be timezone-aware",
            id="bounds-defined-but-missing-tz",
        ),
        pytest.param(
            datetime.min.replace(tzinfo=timezone.utc),
            datetime.max,
            "must be timezone-aware",
            id="bounds-defined-but-missing-tz",
        ),
        pytest.param(
            datetime.min,
            datetime.max,
            "must be timezone-aware",
            id="bounds-defined-but-missing-tz",
        ),
    ),
)
def test_sanitize_datetime_range_invalid(
    mocker,
    start_dt_input: datetime | None,
    end_dt_input: datetime | None,
    err_msg_sub_str: str,
):
    """Tests the sanitize_date_range function against invalid inputs."""
    fallback_range_mock = mocker.patch(
        f"{_PATCHING_TARGET}._fallback_datetime_range",
        side_effect=[(start_dt_input, end_dt_input)],
    )

    with pytest.raises(DateError) as err_info:
        sanitize_date_range(start=start_dt_input, end=end_dt_input)

    assert err_msg_sub_str in str(err_info.value)
    fallback_range_mock.assert_called_once_with(start=start_dt_input, end=end_dt_input)


def test_sanitize_datetime_range_fallback_err(
    mocker,
):
    """Tests the sanitize_date_range function against fallback errors."""
    fallback_range_mock = mocker.patch(
        f"{_PATCHING_TARGET}._fallback_datetime_range",
        side_effect=DateError,
    )

    start_dt_input = Mock(datetime)
    end_dt_input = Mock(datetime)

    with pytest.raises(DateError) as err_info:
        sanitize_date_range(start=start_dt_input, end=end_dt_input)

    assert "Failed to fallback" in str(err_info.value)
    fallback_range_mock.assert_called_once_with(start=start_dt_input, end=end_dt_input)


@pytest.mark.parametrize(
    "start_dt_input, end_dt_input, install_dt, now_dt, err_msg_sub_str",
    (
        pytest.param(
            None,
            datetime.min.replace(tzinfo=timezone.utc),
            datetime.max.replace(tzinfo=timezone.utc),
            datetime.max.replace(tzinfo=timezone.utc),
            "Cannot fallback to default for start date",
            id="err-start-date-fallback",
        ),
        pytest.param(
            datetime.max.replace(tzinfo=timezone.utc),
            None,
            datetime.min.replace(tzinfo=timezone.utc),
            datetime.min.replace(tzinfo=timezone.utc),
            "Cannot fallback to default for end date",
            id="err-end-date-fallback",
        ),
    ),
)
def test_fallback_datetime_range_negative(
    mocker,
    start_dt_input: datetime | None,
    end_dt_input: datetime | None,
    install_dt: datetime,
    now_dt: datetime,
    err_msg_sub_str: str,
):
    """Tests the _fallback_datetime_range function, negative case."""
    mocker.patch(
        f"{_PATCHING_TARGET}.get_installation_datetime",
        side_effect=[install_dt],
    )
    mocker.patch(
        f"{_PATCHING_TARGET}._get_now_tz_aware",
        side_effect=[now_dt],
    )

    with pytest.raises(DateError) as err_info:
        fallback_datetime_range(start=start_dt_input, end=end_dt_input)

    assert err_msg_sub_str in str(err_info.value)


@pytest.mark.parametrize(
    "start_input, end_input, install_dt, start_expected, end_expected",
    (
        pytest.param(
            None,
            None,
            datetime.combine(date(2000, 1, 1), time.min, tzinfo=timezone.utc),
            datetime.combine(date(2000, 1, 1), time.min, tzinfo=timezone.utc),
            datetime.combine(date.today(), time(12, 34, 56), tzinfo=timezone.utc),
            id="fallback-all",
        ),
        pytest.param(
            None,
            datetime.combine(date(2010, 1, 1), time.min, tzinfo=timezone.utc),
            datetime.combine(date(2000, 1, 1), time.min, tzinfo=timezone.utc),
            datetime.combine(date(2000, 1, 1), time.min, tzinfo=timezone.utc),
            datetime.combine(date(2010, 1, 1), time.min, tzinfo=timezone.utc),
            id="fallback-start",
        ),
        pytest.param(
            datetime.combine(date(2000, 1, 1), time.min, tzinfo=timezone.utc),
            None,
            datetime.combine(date(2000, 1, 1), time.min, tzinfo=timezone.utc),
            datetime.combine(date(2000, 1, 1), time.min, tzinfo=timezone.utc),
            datetime.combine(date.today(), time(12, 34, 56), tzinfo=timezone.utc),
            id="fallback-end",
        ),
        pytest.param(
            datetime.combine(date(2000, 1, 1), time.min, tzinfo=timezone.utc),
            datetime.combine(date(2010, 1, 1), time.min, tzinfo=timezone.utc),
            datetime.combine(date(2005, 1, 1), time.min, tzinfo=timezone.utc),
            datetime.combine(date(2000, 1, 1), time.min, tzinfo=timezone.utc),
            datetime.combine(date(2010, 1, 1), time.min, tzinfo=timezone.utc),
            id="identity",
        ),
    ),
)
def test_sanitize_datetime_range_valid(
    mocker,
    start_input: datetime | None,
    end_input: datetime | None,
    install_dt: datetime,
    start_expected: datetime,
    end_expected: datetime,
):
    """Tests the sanitize_date_range function."""
    mocker.patch(
        f"{_PATCHING_TARGET}.get_installation_datetime",
        side_effect=[install_dt],
    )
    mocker.patch(
        f"{_PATCHING_TARGET}._get_now_tz_aware",
        side_effect=[datetime.combine(date.today(), time(12, 34, 56), tzinfo=timezone.utc)],
    )

    start_actual, end_actual = sanitize_date_range(start=start_input, end=end_input)

    assert start_actual == start_expected and end_actual == end_expected


@pytest.mark.parametrize(
    "start, end, path_to_datetime, expected",
    [
        pytest.param(
            datetime(2023, 1, 21).astimezone(),
            datetime(2100, 1, 1).astimezone(),
            {
                Path("/logs/metrics/metrics.json"): None,
                Path("/logs/metrics/metrics-2000-01-20T02-47-43.619.json"): datetime(
                    2000, 1, 20, 2, 47, 43, 619000
                ).astimezone(),
                Path("/logs/metrics/metrics-2023-01-22T02-09-43.119.json"): datetime(
                    2023, 1, 22, 2, 9, 43, 119000
                ).astimezone(),
            },
            [
                Path("/logs/metrics/metrics.json"),
                Path("/logs/metrics/metrics-2023-01-22T02-09-43.119.json"),
            ],
            id="all-but-oldest",
        ),
        pytest.param(
            datetime(1900, 1, 21).astimezone(),
            datetime(2100, 1, 1).astimezone(),
            {
                Path("/logs/metrics/metrics.json"): None,
                Path("/logs/metrics/metrics-2000-01-20T02-47-43.619.json"): datetime(
                    2000, 1, 20, 2, 47, 43, 619000
                ).astimezone(),
                Path("/logs/metrics/metrics-2023-01-22T02-09-43.119.json"): datetime(
                    2023, 1, 22, 2, 9, 43, 119000
                ).astimezone(),
            },
            [
                Path("/logs/metrics/metrics.json"),
                Path("/logs/metrics/metrics-2000-01-20T02-47-43.619.json"),
                Path("/logs/metrics/metrics-2023-01-22T02-09-43.119.json"),
            ],
            id="all",
        ),
        pytest.param(
            datetime(1900, 1, 21).astimezone(),
            datetime(2010, 1, 1).astimezone(),
            {
                Path("/logs/metrics/metrics.json"): None,
                Path("/logs/metrics/metrics-2000-01-20T02-47-43.619.json"): datetime(
                    2000, 1, 20, 2, 47, 43, 619000
                ).astimezone(),
                Path("/logs/metrics/metrics-2023-01-22T02-09-43.119.json"): datetime(
                    2023, 1, 22, 2, 9, 43, 119000
                ).astimezone(),
            },
            [
                Path("/logs/metrics/metrics-2000-01-20T02-47-43.619.json"),
                Path("/logs/metrics/metrics-2023-01-22T02-09-43.119.json"),
            ],
            id="oldest-with-overlap-without-rolling",
        ),
        pytest.param(
            datetime(2010, 1, 21).astimezone(),
            datetime(2100, 1, 1).astimezone(),
            {
                Path("/logs/metrics/metrics.json"): None,
                Path("/logs/metrics/metrics-2000-01-20T02-47-43.619.json"): datetime(
                    2000, 1, 20, 2, 47, 43, 619000
                ).astimezone(),
                Path("/logs/metrics/metrics-2023-01-22T02-09-43.119.json"): datetime(
                    2023, 1, 22, 2, 9, 43, 119000
                ).astimezone(),
            },
            [
                Path("/logs/metrics/metrics.json"),
                Path("/logs/metrics/metrics-2023-01-22T02-09-43.119.json"),
            ],
            id="newest-with-rolling-overlap",
        ),
        pytest.param(
            datetime(2050, 1, 1).astimezone(),
            datetime(2100, 1, 1).astimezone(),
            {
                Path("/logs/metrics/metrics.json"): None,
                Path("/logs/metrics/metrics-2000-01-20T02-47-43.619.json"): datetime(
                    2000, 1, 20, 2, 47, 43, 619000
                ).astimezone(),
                Path("/logs/metrics/metrics-2023-01-22T02-09-43.119.json"): datetime(
                    2023, 1, 22, 2, 9, 43, 119000
                ).astimezone(),
            },
            [
                Path("/logs/metrics/metrics.json"),
            ],
            id="only-rolling",
        ),
    ],
)
def test_filter_files_by_datetime(
    start: datetime,
    end: datetime,
    path_to_datetime: Mapping[Path, datetime | None],
    expected: Sequence[Path],
    mocker,
    tmp_path: Path,
):
    """Tests the _filter_files_by_datetime function."""
    mock_get_path_to_dt = mocker.patch(
        f"{_PATCHING_TARGET}._get_path_to_datetime_from_dir", side_effect=[path_to_datetime]
    )

    actual = filter_files_by_datetime(path_dir=tmp_path, start=start, end=end)

    assert sorted(actual) == sorted(expected)
    mock_get_path_to_dt.assert_called_with(tmp_path)


@pytest.mark.parametrize(
    "path_to_datetime,end_date,overlap_expected",
    (
        pytest.param(
            {Path("rolling.json"): None, Path("foo.json"): datetime(2023, 1, 2, 1, 1, 1).astimezone()},
            datetime(2023, 1, 1).astimezone(),
            Path("foo.json"),
            id="one-timestamped-after-end",
        ),
        pytest.param(
            {
                Path("foo.json"): datetime(2023, 1, 2, 1, 1, 1).astimezone(),
                Path("bar.json"): datetime(2023, 1, 2, 2, 2, 2).astimezone(),
            },
            datetime(2023, 1, 1).astimezone(),
            Path("foo.json"),
            id="many-timestamped-after-end",
        ),
    ),
)
def test_get_file_overlapping_positive(
    path_to_datetime: Mapping[Path, datetime | None], end_date, overlap_expected: Path
):
    """Test the _get_file_overlapping function against an existing overlap scenario."""
    overlap_actual = get_file_overlapping(path_to_datetime=path_to_datetime, end=end_date)

    assert overlap_actual == overlap_expected


@pytest.mark.parametrize(
    "path_to_datetime, end",
    (
        pytest.param({}, datetime(2023, 1, 1).astimezone(), id="empty_map"),
        pytest.param(
            {
                Path("mock.json"): None,
            },
            datetime(2023, 1, 1).astimezone(),
            id="map_without_timestamps",
        ),
        pytest.param(
            {
                Path("notimestamp.json"): None,
                Path("mock.json"): datetime(2022, 1, 1, 1, 1, 1).astimezone(),
            },
            datetime(2023, 1, 1).astimezone(),
            id="no_files_after_end_date",
        ),
    ),
)
def test_get_file_overlapping_negative(path_to_datetime: Mapping[Path, datetime | None], end: datetime):
    """Test the _get_file_overlapping function against a missing overlap scenario."""
    with pytest.raises(FileNotFoundError):
        get_file_overlapping(path_to_datetime=path_to_datetime, end=end)


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("logs.json", id="non-rotated"),
        pytest.param("logs-2023-05-29.json", id="invalid-timestamp"),
    ],
)
def test_datetime_from_otel_file_name_negative(name: str):
    """Tests the _datetime_from_otel_file_name function, negative scenario."""
    with pytest.raises(ValueError) as err_info:
        _datetime_from_otel_file_name(name)

    assert "Failed to find a valid timestamp in" in str(err_info.value) and name in str(err_info.value)


@pytest.mark.parametrize(
    "name, dt_expected",
    [
        pytest.param(
            "logs-2023-05-29T13-45-30.224.json.gz",
            datetime(2023, 5, 29, 13, 45, 30, 224000, tzinfo=timezone.utc),
            id="json-gz",
        ),
        pytest.param(
            "metrics-2023-05-30T08-35-57.997.json",
            datetime(2023, 5, 30, 8, 35, 57, 997000, tzinfo=timezone.utc),
            id="json-non-compressed",
        ),
    ],
)
def test_datetime_from_otel_file_name_positive(name: str, dt_expected: datetime):
    """Tests the _datetime_from_otel_file_name function."""
    dt_actual = _datetime_from_otel_file_name(name)

    assert dt_actual == dt_expected


@pytest.mark.parametrize(
    "log_types,paths_expected",
    (
        pytest.param((LogType.GETI_LOGS,), {Path("geti/logs")}, id="geti-logs-only"),
        pytest.param((LogType.GETI_LOGS, LogType.GETI_LOGS), {Path("geti/logs")}, id="geti-logs-duplicate"),
        pytest.param((LogType.K8S_METRICS, LogType.GETI_LOGS), {Path("geti/logs"), Path("k8s/metrics")}, id="some-mix"),
        pytest.param((), set(), id="empty"),
        pytest.param(
            (LogType.GETI_LOGS, LogType.GETI_TRACES, LogType.GETI_METRICS, LogType.K8S_LOGS, LogType.K8S_METRICS),
            {Path("geti/logs"), Path("geti/metrics"), Path("geti/traces"), Path("k8s/logs"), Path("k8s/metrics")},
            id="all-once",
        ),
    ),
)
def test_get_rel_source_dirs(log_types: Iterable[LogType], paths_expected):
    """Tests the _get_rel_source_dirs function."""
    paths_actual = get_source_dirs(log_types=log_types)

    assert paths_actual == paths_expected


def test_gen_archive_name(mocker):
    """Tests the _gen_archive_name function."""
    datetime_mock = mocker.patch(f"{_PATCHING_TARGET}.datetime")
    datetime_mock.today.return_value = datetime(2000, 1, 2, 3, 4, 5)
    secrets_choice_mock = mocker.patch(f"{_PATCHING_TARGET}.secrets.choice", return_value=12345)

    archive_name_actual = gen_archive_name("foobar")

    assert archive_name_actual == "foobar-20000102030405_12345.tar.gz"
    assert secrets_choice_mock.call_count == 1 and secrets_choice_mock.call_args.args[0] == range(10000, 99999)
    datetime_mock.today.assert_called_once_with()
