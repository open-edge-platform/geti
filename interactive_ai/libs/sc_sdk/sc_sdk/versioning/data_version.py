# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module defines the DataVersion class"""

import pkgutil
import re
from enum import Enum, auto

from cachetools import cached


class SchemaChangeType(Enum):
    """Type of schema changes (data breaking vs non-breaking)"""

    BREAKING = auto()
    NON_BREAKING = auto()


class DataVersion:
    """
    DataVersion represents the version of the Geti data. When the schema of the database
    or the object storage changes, the version changes as well.
    The adopted format is '<major>.<minor>', where <major> and <minor> are positive integers:
        - <major> increases when the schema changes in a *breaking* way (migration necessary)
          Any increment of major also resets the minor number to 0.
        - <minor> increases when the schema changes in a *non-breaking* way (no migration necessary)

    :param version_string: Version formatted as a string
    """

    def __init__(self, version_string: str) -> None:
        if not re.match(r"^\d+\.\d+$", version_string):
            raise ValueError(f"The version must be a string with format '<major>.<minor>', found '{version_string}'")
        self.version_string = version_string

    @property
    def major(self) -> int:
        """Get the major version number"""
        return int(self.version_string.split(".")[0])

    @property
    def minor(self) -> int:
        """Get the minor version number"""
        return int(self.version_string.split(".")[1])

    @staticmethod
    @cached(cache={})
    def get_current() -> "DataVersion":
        """Parse the current version from file"""
        try:
            raw_version_data = pkgutil.get_data(__name__, "data_version.txt")
        except FileNotFoundError:
            # TODO CVS-130512 workaround until bug is fixed; after that, raise the error
            return DataVersion(version_string="1.0")
        if raw_version_data is None:
            raise RuntimeError("Failed to parse data version from file")
        version_string = raw_version_data.decode().strip()
        return DataVersion(version_string=version_string)

    def get_next(self, schema_change_type: SchemaChangeType) -> "DataVersion":
        """
        Compute the next version, depending on the type of changes (breaking vs non-breaking)

        :param schema_change_type: Enum representing the type of data changes
        :return: DataVersion object corresponding to the next version with respect to this one
        """
        match schema_change_type:
            case SchemaChangeType.BREAKING:
                return DataVersion(f"{self.major + 1}.0")
            case SchemaChangeType.NON_BREAKING:
                return DataVersion(f"{self.major}.{self.minor + 1}")
            case _:
                raise ValueError("Unsupported SchemaChangeType")

    def get_previous_major(self) -> "DataVersion":
        """
        Compute the previous major version. The minor number is set to 0.

        :return: DataVersion object corresponding to the previous major version
        """
        return DataVersion(version_string=f"{self.major - 1}.0")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DataVersion):
            return False

        return self.version_string == other.version_string

    def __lt__(self, other: "DataVersion"):
        return self.major < other.major or (self.major == other.major and self.minor < other.minor)

    def __repr__(self) -> str:
        return f"DataVersion('{self.version_string}')"
