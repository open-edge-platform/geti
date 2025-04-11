# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Platform telemetry handling utilities.
"""

import logging
import re
import secrets
import tarfile
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from opentelemetry import trace  # type: ignore[attr-defined]
from service_connection.k8s_client.cluster_info import create_cluster_info_dump

import config as cfg
from common.platform import get_installation_datetime
from common.utils import make_tarfile

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

_PATH_TELEMETRY_ROOT = Path(cfg.LOGS_DIR)

_OTEL_DATE_PARSE_FORMAT = "%Y-%m-%dT%H-%M-%S.%f"
_OTEL_DATE_REGEX = r"\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.\d{3}"


class LogType(str, Enum):
    """Represents the telemetry type (logs, traces, metrics, cluster) and origin (Geti, K8S)."""

    GETI_LOGS = "logs"
    GETI_TRACES = "traces"
    GETI_METRICS = "metrics"

    K8S_LOGS = "k8s_logs"
    K8S_METRICS = "k8s_metrics"

    CLUSTER = "cluster"


_SUB_PATH_TELEMETRY_GETI = Path("geti")
_SUB_PATH_TELEMETRY_K8S = Path("k8s")

_LOG_TYPE_TO_SOURCE_DIR: Mapping[LogType, Path] = {
    LogType.GETI_LOGS: _SUB_PATH_TELEMETRY_GETI / "logs",
    LogType.GETI_METRICS: _SUB_PATH_TELEMETRY_GETI / "metrics",
    LogType.GETI_TRACES: _SUB_PATH_TELEMETRY_GETI / "traces",
    LogType.K8S_LOGS: _SUB_PATH_TELEMETRY_K8S / "logs",
    LogType.K8S_METRICS: _SUB_PATH_TELEMETRY_K8S / "metrics",
}


class DateError(ValueError):
    """Raised for invalid date ranges."""


def get_archive(log_type: LogType | None, start: datetime | None, end: datetime | None) -> Path:
    """Returns path to generated archive for the provided log type."""
    if log_type == LogType.CLUSTER:
        logger.debug("Returning cluster logs")
        return Path(prepare_cluster_info_dump())

    start, end = _sanitize_datetime_range(start=start, end=end)

    log_types: tuple[LogType, ...]
    if log_type:
        log_types = (log_type,)
    else:
        log_types = (
            LogType.GETI_LOGS,
            LogType.GETI_TRACES,
            LogType.GETI_METRICS,
            LogType.K8S_LOGS,
            LogType.K8S_METRICS,
        )
        logger.debug("Log type undefined, falling back to all types of logs.")

    # Must be a single, known, non-cluster log type.
    return _archive_logs(telemetry_root=_PATH_TELEMETRY_ROOT, log_types=log_types, start=start, end=end)


def _archive_logs(telemetry_root: Path, log_types: Iterable[LogType], start: datetime, end: datetime) -> Path:
    """Archives logs for the provided log types.

    :param telemetry_root: Path to root telemetry backup directory.
    :param log_types: Types of logs to include in the created archive.
    :param start: Start of the datetime range to filter logs against.
    :param end: End of the datetime range to filter logs against.
    :return Path: Path to the created archive.
    """
    logger.debug(f"Archiving for log types: {log_types}.")
    path_archive = Path("/tmp") / _gen_archive_name(prefix="-".join(log_types))  # noqa: S108

    with tracer.start_as_current_span("filter-logs-by-dates"):
        path_src_to_arc: Mapping[Path, Path] = _get_archive_sources(
            telemetry_root=telemetry_root, log_types=log_types, start=start, end=end
        )

    logger.debug(f"Source files to be archived: {', '.join(repr(str(src)) for src in path_src_to_arc)}")
    logger.info(f"Archiving {', '.join(log_types)} at {repr(str(path_archive))}.")

    with tracer.start_as_current_span("make-tar-gz"):
        _create_archive(path_archive=path_archive, path_src_to_arc=path_src_to_arc)

    return path_archive


def _create_archive(path_archive: Path, path_src_to_arc: Mapping[Path, Path]):
    """Creates tar.gz archive reflecting the provided path mapping.

    :param path_archive:
    :param path_src_to_arc: Map of filesystem source paths to their corresponding in-archive relative paths (1:1).
    """
    with tarfile.open(name=path_archive, mode="w:gz", format=tarfile.PAX_FORMAT, compresslevel=1) as tar:
        for path_fs, path_rel in path_src_to_arc.items():
            logger.debug(f"Adding {repr(str(path_fs))} to the archive as {repr(str(path_rel))}")
            tar.add(name=path_fs, arcname=path_rel, recursive=True)


def _get_archive_sources(
    telemetry_root: Path, log_types: Iterable[LogType], start: datetime, end: datetime
) -> Mapping[Path, Path]:
    """Returns sources to archive, based on the provided log_types, start_date and end_date.

    :param telemetry_root: Path to root telemetry backup directory.
    :param log_types: Log types to include in the archive sources.
    :param start: Start datetime for filtering the sources, inclusive.
    :param end: End datetime for filtering the sources, inclusive.
    :returns Mapping[Path, Path]: Mapping of absolute, filesystem source path, to target, relative, in-archive path.
    """
    now = _get_now_tz_aware()
    install_dt = get_installation_datetime()

    if end < install_dt or start > now:
        logger.debug(
            f"Provided datetime range ({start.isoformat()}; {end.isoformat()}) "
            f"is fully outside of the platform's lifetime ({install_dt.isoformat()}; {now.isoformat()})."
            f"Returning empty archive sources."
        )
        return {}

    if start < install_dt:
        logger.debug(
            f"Start datetime {start.isoformat()} is earlier than installation datetime "
            f"({install_dt.isoformat()}), falling back to: {install_dt.isoformat()}."
        )
        start = install_dt

    if end > now:
        logger.debug(f"End datetime {end.isoformat()} is in the future, falling back to now: {now.isoformat()}.")
        end = now

    logger.debug(
        f"Filtering sources against datetime range: start={repr(start.isoformat())}, end={repr(end.isoformat())}."
    )
    paths_filtered: list[Path] = []
    rel_source_dirs: Iterable[Path] = _get_rel_source_dirs(log_types=log_types)
    for rel_dir in rel_source_dirs:
        path_rel_dir = telemetry_root / rel_dir
        if path_rel_dir.is_dir():
            paths_filtered.extend(_filter_files_by_datetime(path_dir=path_rel_dir, start=start, end=end))
        else:
            logger.debug(f"Ignoring non-existent source directory: {repr(str(path_rel_dir.absolute()))}")

    return {path_fs: path_fs.relative_to(telemetry_root) for path_fs in paths_filtered}


def _sanitize_datetime_range(start: datetime | None, end: datetime | None) -> tuple[datetime, datetime]:
    """Sanitizes the provided date range.

    :param start: Datetime range start, inclusive. Expecting timezone-aware datetime.
    :param end: Datetime range end, inclusive. Expecting timezone-aware datetime.
    :raises InvalidDateRangeError: If the provided start date is later than the provided end date.
    """
    try:
        start, end = _fallback_datetime_range(start=start, end=end)
    except DateError as err:
        raise DateError("Failed to fallback to datetime range defaults.") from err

    if not (start.tzinfo and end.tzinfo):
        raise DateError("Start and end datetime must be timezone-aware.")

    if start > end:
        # Handle out of order dates.
        raise DateError(f"Start datetime ({start.isoformat()}) cannot be later than end datetime ({end.isoformat()}).")

    return start, end


def _fallback_datetime_range(start: datetime | None, end: datetime | None) -> tuple[datetime, datetime]:
    """Falls back to safe defaults for undefined (None) boundary values.

    Does not modify already defined bounds.

    :param start: Datetime range start, inclusive. Expecting timezone-aware datetime.
    :param end: Datetime range end, inclusive. Expecting timezone-aware datetime.
    :return Tuple[datetime, datetime]: The fallback datetime range.
    :raises InvalidDateRangeError: If end is undefined and the provided start datetime is in the future.
    :raises InvalidDateRangeError: If start is undefined and the provided end datetime is earlier than
        the platform installation datetime.
    """
    now = _get_now_tz_aware()
    install_dt = get_installation_datetime()

    if not start and end and end < install_dt:
        # Handle impossible start date fallback to default.
        raise DateError(
            f"Cannot fallback to default for start datetime. Provided end datetime ({end.isoformat()}) "
            f"is earlier than the default (platform installation datetime {install_dt.isoformat()})."
        )

    if start and not end and start > now:
        # Handle impossible end date fallback to default.
        raise DateError(
            f"Cannot fallback to default for end datetime. "
            f"Provided start datetime ({start.isoformat()}) is in the future (now is {now.isoformat()})."
        )

    if not start:
        start = install_dt
        logger.debug(
            f"Start datetime not defined, falling back to platform installation datetime: {start.isoformat()}."
        )

    if not end:
        end = now
        logger.debug(f"End datetime not defined, falling back to now: {end.isoformat()}.")

    return start, end


def _filter_files_by_datetime(path_dir: Path, start: datetime, end: datetime) -> Sequence[Path]:
    """Filters files in the target directory based on the provided time range.
    If the specified date range includes today, non-rotated files (files without timestamps)
    are also included in the filtering result.
    :param path_dir: Path to the target directory.
    :param start: Datetime range start, inclusive. Must be timezone-aware.
    :param end: Datetime range end, inclusive. Must be timezone-aware.
    :returns Iterable[Path]: Paths to files matching the search criteria.
    """
    path_to_datetime: Mapping[Path, datetime | None] = _get_path_to_datetime_from_dir(path_dir)
    now: datetime = _get_now_tz_aware()

    paths_filtered = []
    for path, file_dt in path_to_datetime.items():
        if file_dt and start <= file_dt <= end:
            logger.debug(f"Found file matching range: {repr(str(path))}.")
            paths_filtered.append(path)

    paths_no_timestamp = [path for path, timestamp in path_to_datetime.items() if not timestamp]
    if end < now:
        try:
            # Include one rotated file after the end datetime, as it likely contains partial logs from the end datetime.
            overlap = _get_file_overlapping(path_to_datetime, end)
            paths_filtered.append(overlap)
            logger.debug(f"Including datetime overlapping file: {repr(str(overlap))}")
        except FileNotFoundError:
            # Latest overlapping file is the current non-rotated file.
            paths_filtered.extend(paths_no_timestamp)
            logger.debug(f"Including rolling file as the overlapping file: {paths_no_timestamp}")
    else:
        # Include non-rotated files, as they contain today's latest data.
        paths_filtered.extend(paths_no_timestamp)
        logger.debug(f"Including rolling files: {[str(path) for path in paths_no_timestamp]}")

    return paths_filtered


def _get_file_overlapping(path_to_datetime: Mapping[Path, datetime | None], end: datetime) -> Path:
    """Returns path to the earliest file rotated right after the specified end date.

    :param path_to_datetime: Map of file path to the corresponding timestamp (optional).
    :end_date date: Target end date, for which the overlapping file is to be found.
    :returns Path: Path to the file containing data overlapping the end date.
    :raises FileNotFoundError: If the overlapping file is not found.
    """
    path_to_datetime_after_end: Mapping[Path, datetime] = {
        path: dtime for path, dtime in path_to_datetime.items() if dtime and dtime > end
    }

    # Find the path of the file with the earliest timestamp.
    try:
        return min(path_to_datetime_after_end.items(), key=lambda elem: elem[1])[0]
    except ValueError as err:
        raise FileNotFoundError(f"Failed to find datetime overlapping file for end datetime: {end}.") from err


def _datetime_from_otel_file_name(name: str) -> datetime:
    """Parses timestamp from OpenTelemetry-exported file name.

    :param name: Name of the file exported by OpenTelemetry Collector, e.g. "metrics-2023-01-20T15-20-09.412.json".
    :returns datetime: The parsed timestamp, timezone-aware.
    :raises ValueError: On failure to parse the timestamp from the provided file name.
    """
    match = re.search(string=name, pattern=_OTEL_DATE_REGEX)
    if match:
        tz_naive = datetime.strptime(match.group(0), _OTEL_DATE_PARSE_FORMAT)
        return tz_naive.replace(tzinfo=timezone.utc)
    raise ValueError(f"Failed to find a valid timestamp in {repr(name)}")


def _get_path_to_datetime_from_dir(path_dir: Path) -> Mapping[Path, datetime | None]:
    """Returns OpenTelemetry Collector telemetry backup files in the provided directory.

    :param path_dir: Path to the target directory.
    :returns Mapping[Path, Optional[datetime]]: Map of Path to datetime or None.
    """
    path_to_datetime: dict[Path, datetime | None] = {}
    for path in path_dir.glob("*"):
        try:
            path_to_datetime[path] = _datetime_from_otel_file_name(path.name)
            logger.debug(f"Found timestamp in file name {repr(path.name)}: {path_to_datetime[path]}")
        except ValueError:
            path_to_datetime[path] = None
            logger.debug(f"No valid timestamp found in file name {repr(path.name)}, falling back to {None}.")

    return path_to_datetime


def _get_rel_source_dirs(log_types: Iterable[LogType]) -> Iterable[Path]:
    """Returns relative source directories for the provided telemetry types."""
    return {_LOG_TYPE_TO_SOURCE_DIR[log_type] for log_type in log_types}


def _get_now_tz_aware() -> datetime:
    """Returns timezone-aware datetime, with respect to local time."""
    return datetime.now().astimezone()


def _gen_archive_name(prefix: str) -> str:
    """Generates unique archive name with the specified prefix."""
    return f"{prefix}-{datetime.today().strftime('%Y%m%d%H%M%S')}_{secrets.choice(range(10**4, (10**5) - 1))}.tar.gz"


def prepare_cluster_info_dump() -> str:
    """
    Creates archive with cluster info.
    :return str: Path to the created archive.
    """
    logger.info("Retrieving cluster-info data")
    name = f"cluster_info_{datetime.today().strftime('%Y%m%d%H%M%S')}_{secrets.choice(range(10**4, (10**5) - 1))}"
    source_path = f"/tmp/{name}"  # noqa: S108
    with tracer.start_as_current_span("create-cluster-info-tarfile"):
        create_cluster_info_dump(directory=source_path)
        output_tarfile_path = f"{source_path}.tar.gz"
        make_tarfile(output_filename=output_tarfile_path, paths=[source_path])
    return output_tarfile_path
