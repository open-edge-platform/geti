"""Module for handling telemetry-related artifacts."""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os
import re
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

import storage
from configuration import ENABLE_TELEMETRY_CLEANUP, PATH_LOGS_DIR
from geti_logger_tools.logger_config import initialize_logger

logger = initialize_logger(__name__)


def _parse_env_variable_to_int(env_variable_name: str, default_value: str) -> int:
    """
    Parses the provided environment variable to an int,
    if the given environment variable is an empty string sets default value
    """
    env_variable = os.environ.get(env_variable_name, default=default_value)
    if env_variable.strip() == "":
        logger.debug(f"{env_variable_name} variable is empty, assign a default value to variable")
        return int(default_value)
    return int(env_variable)


_GETI_TELEMETRY_RETENTION_DAYS = _parse_env_variable_to_int(
    env_variable_name="GETI_TELEMETRY_RETENTION_DAYS", default_value="30"
)
_K8S_TELEMETRY_RETENTION_DAYS = _parse_env_variable_to_int(
    env_variable_name="K8S_TELEMETRY_RETENTION_DAYS", default_value="10"
)

_MIN_FREE_DISK_SPACE_GIB = _parse_env_variable_to_int(env_variable_name="MIN_FREE_DISK_SPACE_GIB", default_value="5")
_TELEMETRY_CLEANUP_THRESHOLD_EXTRA_GIB = _parse_env_variable_to_int(
    env_variable_name="TELEMETRY_CLEANUP_THRESHOLD_EXTRA_GIB", default_value="10"
)
_TELEMETRY_CLEANUP_THRESHOLD: int = (
    _MIN_FREE_DISK_SPACE_GIB + _TELEMETRY_CLEANUP_THRESHOLD_EXTRA_GIB
) * storage.parse_size_to_bytes("GiB")
_TELEMETRY_CLEANUP_LIMIT: timedelta = timedelta(
    hours=_parse_env_variable_to_int(env_variable_name="TELEMETRY_CLEANUP_LIMIT_HOURS", default_value="24")
)

_OTEL_DATE_PARSE_FORMAT = "%Y-%m-%dT%H-%M-%S.%f"
_OTEL_DATE_REGEX = r"\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.\d{3}"

_FILE_EXT_JSON_GZ = "json.gz"


class BackupDir(Enum):
    """Represents a telemetry samples parent backup directory path."""

    K8S = PATH_LOGS_DIR / "k8s"
    GETI = PATH_LOGS_DIR / "geti"


class BackupSubDir(Enum):
    """Represents a telemetry samples backup subdirectory path."""

    TRACES_GETI = BackupDir.GETI.value / "traces"
    METRICS_GETI = BackupDir.GETI.value / "metrics"
    LOGS_GETI = BackupDir.GETI.value / "logs"

    METRICS_K8S = BackupDir.K8S.value / "metrics"
    LOGS_K8S = BackupDir.K8S.value / "logs"


def _datetime_from_otel_file_name(name: str) -> datetime:
    """Parses timestamp from OpenTelemetry-exported file name.

    :param name: Name of the file exported by OpenTelemetry Collector, e.g. "metrics-2023-01-20T15-20-09.412.json".
    :returns datetime: The parsed timestamp.
    :raises ValueError: On failure to parse the timestamp from the provided file name.
    """
    match = re.search(string=name, pattern=_OTEL_DATE_REGEX)
    if match:
        return datetime.strptime(match.group(0), _OTEL_DATE_PARSE_FORMAT)
    raise ValueError(f"Failed to find a valid timestamp in {repr(name)}")


def _get_path_to_datetime(path_dir: Path, pattern: str) -> Mapping[Path, datetime]:
    """Returns Map of Path to datetime for the provided directory.

    The provided directory is traversed recursively.

    :param path_dir: Path to the target directory.
    :param pattern: Glob pattern for filtering files.
    :returns Mapping[Path, datetime]: Map of path to datetime
    """
    path_to_timestamp: dict[Path, datetime] = {}
    for path in path_dir.rglob(pattern):
        try:
            path_to_timestamp[path] = _datetime_from_otel_file_name(path.name)
        except ValueError:
            logger.debug(
                "Ignoring %s, no valid timestamp in file name.",
                repr(str(path.absolute())),
            )

    return path_to_timestamp


def _get_datetime_to_paths(path_dir: Path, pattern: str) -> Mapping[datetime, set[Path]]:
    """Returns Map of date to Paths for the provided directory.

    The provided directory is traversed recursively.

    :param path_dir: Path to the target directory.
    :param pattern: Glob pattern for filtering files.
    :returns Mapping[date, Set[Path]]: Map of date to Paths.
    """
    dt_to_paths: dict[datetime, set[Path]] = {}
    for path in path_dir.rglob(pattern):
        try:
            dtime = _datetime_from_otel_file_name(path.name)
        except ValueError:
            logger.debug(
                "Ignoring %s, no valid timestamp in file name.",
                repr(str(path.absolute())),
            )
            continue

        if dtime in dt_to_paths:
            dt_to_paths[dtime].add(path)
        else:
            dt_to_paths[dtime] = {path}

    return dt_to_paths


def _delete_in_single_backup_dir(backup_dir: Path, retention: int):
    """
    Deletes expired telemetry samples in the specified directory.

    :param backup_dir: Backup directory to delete outdated files in.
    :param retention: Retention period, expressed in days.
    """
    logger.info(
        "Scanning directory for expired telemetry files (assuming retention period of %d days): %s",
        retention,
        repr(str(backup_dir)),
    )
    path_to_dt = _get_path_to_datetime(backup_dir, pattern=f"*.{_FILE_EXT_JSON_GZ}")
    paths_expired = [
        path for path, timestamp in path_to_dt.items() if (datetime.utcnow().date() - timestamp.date()).days > retention
    ]
    if paths_expired:
        logger.info(
            "Found %d expired telemetry files in %s.",
            len(paths_expired),
            str(backup_dir.absolute()),
        )
        for path in paths_expired:
            logger.info("Removing %s", repr(str(path.resolve())))
            try:
                path.unlink()
            except FileNotFoundError:
                logger.warning(
                    "File vanished before it could be removed %s",
                    repr(str(path.resolve())),
                )
    else:
        logger.info("Did not find any expired telemetry files in %s.", repr(str(backup_dir)))


def _cleanup_expired_telemetry_samples():
    """
    Deletes all expired telemetry samples (logs, traces, metrics).
    """
    _delete_in_single_backup_dir(backup_dir=BackupDir.GETI.value, retention=_GETI_TELEMETRY_RETENTION_DAYS)
    _delete_in_single_backup_dir(backup_dir=BackupDir.K8S.value, retention=_K8S_TELEMETRY_RETENTION_DAYS)


def _get_deletable_telemetry_files(path_dir: Path, cleanup_time_limit: timedelta) -> Sequence[Path]:
    """Returns paths for telemetry backup files available for deletion, sorted chronologically.

    :param path_dir: Path to the target directory.
    :param cleanup_time_limit: Cleanup time limit. No files from this latest timedelta will be included in the result.
    """
    now = datetime.utcnow()
    dt_to_paths: Mapping[datetime, set[Path]] = _get_datetime_to_paths(path_dir, pattern=f"*.{_FILE_EXT_JSON_GZ}")

    paths_chrono: list[Path] = []
    for dtime in sorted(dt_to_paths):
        if dtime >= now - cleanup_time_limit:
            # Enforce the upper cleanup time limit.
            break
        paths_chrono.extend(dt_to_paths[dtime])

    return paths_chrono


def _force_cleanup_telemetry_samples(path_dir: Path, cleanup_size_threshold: int, cleanup_time_limit: timedelta):
    """
    Deletes excess telemetry samples from the oldest, until the desired free space is reached.

    :param path_dir: Path to the target directory.
    :param cleanup_size_threshold: Cleanup size threshold, expressed in bytes.
    :param cleanup_time_limit: Cleanup upper time limit. No data from this latest timedelta will be deleted.
    """
    paths_chrono = _get_deletable_telemetry_files(path_dir=path_dir, cleanup_time_limit=cleanup_time_limit)

    disk_free = storage.get_disk_free(path_dir)
    if disk_free >= cleanup_size_threshold:
        logger.info(
            f"Free disk space ({disk_free}B) meets the cleanup size threshold ({cleanup_size_threshold}B). "
            f"Skipping forced cleanup."
        )
        return

    # Remove one by one, beginning with oldest.
    for path in paths_chrono:
        logger.info(f"Removing {repr(str(path.resolve()))}.")
        path.unlink()

        disk_free = storage.get_disk_free(path_dir)
        if disk_free >= cleanup_size_threshold:
            logger.info(
                f"Free disk space ({disk_free}B) meets the cleanup size threshold ({cleanup_size_threshold}B). "
                f"Stopping forced cleanup."
            )
            return

    logger.warning(
        f"No rotated and compressed telemetry files left to delete before "
        f"{(datetime.utcnow() - cleanup_time_limit).isoformat()} ({cleanup_time_limit=}). "
        f"Free disk space ({disk_free}B) "
        f"is still below the cleanup threshold ({cleanup_size_threshold}B)."
    )


def _str_to_bool(str_to_check: str) -> bool:
    """
    Parses the provided string to boolean, if the given string is in the list of acceptable value, returns True
    """
    return str_to_check.lower() in ("true", "t", "1", "yes", "y")


async def cleanup_telemetry_samples():  # noqa: ANN201
    """Cleans up expired/excessive telemetry samples."""
    if _str_to_bool(str_to_check=ENABLE_TELEMETRY_CLEANUP):
        _cleanup_expired_telemetry_samples()
        _force_cleanup_telemetry_samples(
            path_dir=PATH_LOGS_DIR,
            cleanup_size_threshold=_TELEMETRY_CLEANUP_THRESHOLD,
            cleanup_time_limit=_TELEMETRY_CLEANUP_LIMIT,
        )
