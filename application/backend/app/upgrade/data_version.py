# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Tracking of the application-data version on disk.

The *data version* records the application version whose schema/layout the
on-disk data (SQLite database + filesystem artifacts) currently conforms to. It
is stored in a small stamp file inside the data directory and is only advanced
once an upgrade has completed successfully. It is the anchor the upgrade
machinery uses to decide which migrations still have to run and, on failure, to
prove the data was rolled back to its original version.
"""

import re
from pathlib import Path

from loguru import logger

# Name of the stamp file kept in the data directory.
DATA_VERSION_FILE = ".geti_data_version"

# Version assumed for data directories that already contain a database but no
# stamp file. Such deployments predate the introduction of this upgrade system
# (Geti 3.0.x), so their data is treated as conforming to that baseline and any
# newer migration is applied on top of it.
INITIAL_DATA_VERSION = "3.0.0"


def parse_version(version: str) -> tuple[int, ...]:
    """Parse a version string into a comparable numeric release tuple.

    Only the leading numeric *release* segment is considered; any pre-release or
    build-metadata suffix (e.g. ``rc1``, ``+cuda``) is ignored, so ``3.1.0`` and
    ``3.1.0rc1`` compare equal. This is intentional: pre-release builds of a
    version share its data layout.

    Args:
        version: A version string such as ``"3.1.0"`` or ``"3.1.0rc1"``.

    Returns:
        A tuple of integers, e.g. ``(3, 1, 0)``. Returns ``(0,)`` when no numeric
        component can be found.
    """
    release = re.split(r"[-+]", version.strip(), maxsplit=1)[0]
    # Capture only the leading dotted-numeric release, stopping at the first
    # non-numeric component (e.g. the "rc1" in "3.1.0rc1").
    match = re.match(r"\d+(?:\.\d+)*", release)
    if not match:
        return (0,)
    parts = tuple(int(p) for p in match.group(0).split("."))
    return parts or (0,)


def is_newer(candidate: str, reference: str) -> bool:
    """Return ``True`` when ``candidate`` is a strictly newer version than ``reference``."""
    return parse_version(candidate) > parse_version(reference)


def _stamp_path(data_dir: Path) -> Path:
    return data_dir / DATA_VERSION_FILE


def read_data_version(data_dir: Path, database_path: Path) -> str | None:
    """Determine the version the on-disk data currently conforms to.

    Resolution order:

    1. The stamp file, when present, is authoritative.
    2. If there is no stamp file but a database already exists, the deployment
       predates the upgrade system and is treated as the :data:`INITIAL_DATA_VERSION`.
    3. Otherwise this is a fresh install and ``None`` is returned.

    Args:
        data_dir: The application data directory.
        database_path: Path to the SQLite database file.

    Returns:
        The current data version string, or ``None`` for a fresh install.
    """
    stamp = _stamp_path(data_dir)
    if stamp.exists():
        try:
            value = stamp.read_text(encoding="utf-8").strip()
            if value:
                return value
            logger.warning("Data version stamp {} is empty; treating as unknown", stamp)
        except OSError as e:
            logger.warning("Could not read data version stamp {}: {}", stamp, e)

    if database_path.exists():
        logger.info(
            "No data version stamp found but a database exists; assuming baseline version {}",
            INITIAL_DATA_VERSION,
        )
        return INITIAL_DATA_VERSION

    return None


def write_data_version(data_dir: Path, version: str) -> None:
    """Persist ``version`` as the current data version.

    The write is atomic (write-to-temp then ``os.replace``) so a crash mid-write
    can never leave a truncated stamp behind.
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    stamp = _stamp_path(data_dir)
    tmp = stamp.with_name(f"{stamp.name}.tmp")
    tmp.write_text(f"{version}\n", encoding="utf-8")
    tmp.replace(stamp)
    logger.info("✓ Recorded data version {} at {}", version, stamp)
