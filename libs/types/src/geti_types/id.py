from dataclasses import dataclass
from uuid import UUID

from bson import ObjectId


class ID(str):
    """
    Generic identifier for entities.

    ID wraps other identifier formats, such as UUID and ObjectId, but is also
    compatible with raw strings.

    :param value: Value to initialize the identifier; if unspecified,
        it defaults to an empty string
    """

    # The class directly subclasses the str builtin type rather than using composition.
    # Doing so, it can reuse most of the builtin functions of the str type, and avoid
    # the overhead of Python function calls for hashing and comparison; hash and
    # equality can be up to 5x faster than using composition.
    # Since the str type is immutable, the object construction arguments cannot be
    # handled in __init__ as usual; __new__ is used instead.
    # The __init__ function is still left for typing correctness.

    def __new__(cls, value: str | ObjectId | UUID = "") -> "ID":
        str_value = str(value).strip().lower()
        return super().__new__(cls, str_value)

    def __init__(self, value: str | ObjectId | UUID = "") -> None:
        pass

    def __repr__(self) -> str:
        return f"ID({self})"


@dataclass(frozen=True, eq=True)
class ProjectIdentifier:
    """Group of identifiers that uniquely identify a Geti project."""

    workspace_id: ID
    project_id: ID


@dataclass(frozen=True, eq=True)
class DatasetStorageIdentifier:
    """Group of identifiers that uniquely identify a Geti dataset storage."""

    workspace_id: ID
    project_id: ID
    dataset_storage_id: ID


@dataclass(frozen=True, eq=True)
class DatasetIdentifier:
    """Group of identifiers that uniquely identify a Geti dataset."""

    workspace_id: ID
    project_id: ID
    dataset_storage_id: ID
    dataset_id: ID


@dataclass(frozen=True, eq=True)
class ModelStorageIdentifier:
    """Group of identifiers that uniquely identify a Geti model storage."""

    workspace_id: ID
    project_id: ID
    model_storage_id: ID
