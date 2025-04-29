"""Module for handling storage."""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import shutil
from pathlib import Path


def parse_size_to_bytes(size: str) -> int:
    """Parses the provided size string to bytes."""
    unit_to_bytes = {
        "K": 10**3,
        "M": 10**6,
        "G": 10**9,
        "T": 10**12,
        "P": 10**15,
        "Ki": 2**10,
        "Mi": 2**20,
        "Gi": 2**30,
        "Ti": 2**40,
        "Pi": 2**50,
    }
    size_no_b = size.strip().removesuffix("B")

    try:
        for unit, factor in unit_to_bytes.items():
            if size_no_b.endswith(unit):
                number = size_no_b.rstrip(unit).strip() or "1"
                return int(float(number) * factor)

        return int(size_no_b)
    except ValueError as err:
        raise ValueError(f"Failed to parse {repr(size)} as memory size.") from err


def get_disk_free(path: Path) -> int:
    """Returns free disk space for the provided path, expressed in bytes."""
    return shutil.disk_usage(path)[2]
