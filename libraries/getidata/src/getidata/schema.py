# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
Schema definitions for the dataset system.
"""

import copy
import importlib
import types
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from functools import reduce
from typing import Any, Generic, Optional, TypeVar, Union, get_args, get_origin

from getidata.categories import Categories
from getidata.fields.base import Field


@dataclass
class AttributeInfo:
    """
    Container for attribute type and field annotation information.
    """

    type: type
    field: Field
    categories: Optional["Categories"] = None


TField = TypeVar("TField", bound=Field)


@dataclass(frozen=True)
class AttributeSpec(Generic[TField]):
    """
    Specification for an attribute used in converters, tilers, etc.

    This class is not part of the schema, but rather used a convenient container
    for passing attribute specifications around in transforms.

    Links an attribute name with its corresponding field type definition,
    providing the complete specification needed for converter operations.

    Args:
        TField: The specific Field type, defaults to Field

    Attributes:
        name: The attribute name
        field: The field type specification
        categories: Optional categories information (e.g., LabelCategories, MaskCategories)
    """

    name: str
    field: TField
    categories: Categories | None = None


BUILTIN_TYPES = {
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
    "list": list,
    "dict": dict,
    "tuple": tuple,
    "NoneType": type(None),
}

# Schemas can be loaded from untrusted dataset files (e.g. a getidata-format
# dataset received from an external source). Resolving a type module/name pair
# read from such a file must never be allowed to import and return an arbitrary
# importable object since that value is later invoked as a callable elsewhere
# (see Field.from_polars implementations).
# Only these trusted top-level packages are ever imported here.
_ALLOWED_TYPE_PACKAGES = frozenset({"numpy", "torch", "torchvision", "getidata"})
_TYPE_MODULE_ALIASES: dict[str, str] = {}


def _is_allowed_type_module(type_module: str) -> bool:
    """Check whether a module is trusted to be imported when resolving a serialized type."""
    return type_module.split(".", 1)[0] in _ALLOWED_TYPE_PACKAGES


def register_type_module_alias(old_module: str, new_module: str) -> None:
    """Register a former schema module prefix with a trusted replacement package."""
    if not old_module or not _is_allowed_type_module(new_module):
        raise ValueError("Schema module aliases must target a trusted package")
    _TYPE_MODULE_ALIASES[old_module] = new_module


def _remap_type_module(module_name: str) -> str:
    for old_module, new_module in _TYPE_MODULE_ALIASES.items():
        if module_name == old_module or module_name.startswith(old_module + "."):
            return new_module + module_name[len(old_module) :]
    return module_name


def _resolve_type(type_name: str, type_module: str | None) -> type:
    """Resolve a type from its name and module."""
    if type_module and type_module != "builtins":
        type_module = _remap_type_module(type_module)
        if not _is_allowed_type_module(type_module):
            return object
        try:
            module = importlib.import_module(type_module)
            resolved = getattr(module, type_name, object)
        except (ImportError, AttributeError):
            return object
        # Only ever return an actual class, never an arbitrary callable (e.g. a function).
        return resolved if isinstance(resolved, type) else object
    if type_name in BUILTIN_TYPES:
        return BUILTIN_TYPES.get(type_name, object)
    return object


def _resolve_type_from_qualified_name(qualified_name: str) -> type:
    """Resolve a type from a qualified name like 'numpy.ndarray' or 'None'."""
    qualified_name = qualified_name.strip()
    if qualified_name == "None":
        return type(None)
    if qualified_name in BUILTIN_TYPES:
        return BUILTIN_TYPES[qualified_name]
    # Try to split into module and attribute (e.g., "numpy.ndarray")
    parts = qualified_name.rsplit(".", 1)
    if len(parts) == 2:
        module_name, attr_name = parts
        module_name = _remap_type_module(module_name)
        if not _is_allowed_type_module(module_name):
            return object
        try:
            module = importlib.import_module(module_name)
            resolved = getattr(module, attr_name, object)
        except (ImportError, AttributeError):
            return object
        # Only ever return an actual class, never an arbitrary callable (e.g. a function).
        return resolved if isinstance(resolved, type) else object
    return object


@dataclass
class Schema:
    """
    Represents the schema of a dataset with attribute definitions.
    Enforces that only one field of each type exists per semantic context.
    """

    attributes: dict[str, AttributeInfo] = dataclass_field(default_factory=dict[str, AttributeInfo])

    def __post_init__(self):
        """Validate that only one field of each type exists per semantic context."""
        seen: dict[tuple[type[Field], str], str] = {}
        for name, attr in self.attributes.items():
            key = type(attr.field), attr.field.semantic
            if key in seen:
                raise ValueError(
                    f"Duplicate field type {key[0]} for semantic {key[1]} in schema. "
                    f"Fields '{seen[key]}' and '{name}' conflict."
                )
            seen[key] = name

        self._fields_with_categories: dict[str, Categories] | None = None
        self._required_columns_cache: dict[str, set[str]] | None = None

    def get_categories_for_field(self, attr_name: str) -> Categories | None:
        """
        Get the categories for a specific field, resolving category references.

        If the field has `categories_from` set, this method will return the
        categories from the referenced field.

        Args:
            attr_name: The attribute name to get categories for

        Returns:
            The Categories for this field, or None if not set
        """
        if attr_name not in self.attributes:
            raise ValueError(f"Attribute '{attr_name}' not found in schema")

        attr_info = self.attributes[attr_name]
        categories = attr_info.categories

        # If this field references categories from another field, resolve it
        categories_from = attr_info.field.get_categories_from()
        if categories is None and categories_from is not None and categories_from in self.attributes:
            categories = self.attributes[categories_from].categories

        return categories

    def get_required_columns(self, attr_name: str) -> set[str]:
        """
        Get the required Polars column names for a given attribute.

        This method caches the results to avoid repeated computation of
        to_polars_schema() on hot paths like __getitem__.

        Args:
            attr_name: The attribute name to get required columns for

        Returns:
            Set of column names required for this attribute
        """
        if self._required_columns_cache is None:
            self._required_columns_cache = {}

        if attr_name not in self._required_columns_cache:
            attr_info = self.attributes[attr_name]
            self._required_columns_cache[attr_name] = set(attr_info.field.to_polars_schema(attr_name).keys())

        return self._required_columns_cache[attr_name]

    def with_categories(self, categories: dict[str, "Categories"]) -> "Schema":
        """
        Create a new schema with categories applied to specific attributes.

        Args:
            categories: Dictionary mapping attribute names to categories

        Returns:
            A new Schema instance with categories applied

        Raises:
            ValueError: If an attribute name is not found in the schema
        """
        # Make a shallow copy of this schema
        new_schema = copy.copy(self)

        # Reset caches to avoid sharing references with the original schema
        new_schema._fields_with_categories = None
        new_schema._required_columns_cache = None

        # Also copy the attributes dict to avoid modifying the original AttributeInfo objects
        new_schema.attributes = {name: copy.copy(attr_info) for name, attr_info in self.attributes.items()}

        # Add categories to specific attributes
        for attr_name, category in categories.items():
            if attr_name in new_schema.attributes:
                new_schema.attributes[attr_name].categories = category
            else:
                raise ValueError(f"Attribute '{attr_name}' not found in schema")

        # Validate that category references point to valid fields
        for attr_name, attr_info in new_schema.attributes.items():
            categories_from = attr_info.field.get_categories_from()
            if categories_from is not None and categories_from not in new_schema.attributes:
                raise ValueError(
                    f"Field '{attr_name}' references categories from '{categories_from}', "
                    f"but '{categories_from}' is not found in the schema."
                )

        return new_schema

    def get_fields_with_required_categories(self) -> dict[str, Categories]:
        """
        Get the attributes that semantically require a category.

        Returns:
            dict mapping attribute names to the respective required categories.
            Attributes that do not strictly require categories are not returned.
        """
        if self._fields_with_categories is None:
            self._fields_with_categories = {}
            for attribute, attribute_info in self.attributes.items():
                if expected_categories_type := attribute_info.field.get_expected_categories_type():
                    categories = attribute_info.categories

                    # If this field references categories from another field, resolve it
                    categories_from = attribute_info.field.get_categories_from()
                    if categories is None and categories_from is not None and categories_from in self.attributes:
                        categories = self.attributes[categories_from].categories

                    if categories is None or not isinstance(categories, expected_categories_type):
                        raise ValueError(
                            f"Expected schema attribute '{attribute}' to have categories defined of type "
                            f"'{expected_categories_type}', found '{categories}' instead. "
                            f"Note that schemas (including ones that are attached to datasets) can be created without "
                            f"categories for fields that require them, but for certain operations like appending data "
                            f"categories have to be defined if fields require them in order to validate the data."
                        )
                    self._fields_with_categories[attribute] = categories

        return self._fields_with_categories

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize this Schema to a JSON-compatible dictionary.

        Returns:
            Dictionary representation of this Schema instance
        """

        attributes = {}
        categories = {}

        for name, attr_info in self.attributes.items():
            attr_type = attr_info.type

            # Check if this is a Union type (e.g., np.ndarray | None)
            if isinstance(attr_type, types.UnionType) or get_origin(attr_type) is Union:
                union_args = get_args(attr_type)
                type_info = [
                    {
                        "name": arg.__name__ if hasattr(arg, "__name__") else str(arg),
                        "module": arg.__module__ if hasattr(arg, "__module__") else None,
                    }
                    for arg in union_args
                ]
                attributes[name] = {
                    "type": type_info,
                    "type_module": "__union__",
                    "field": attr_info.field.to_dict(),
                }
            else:
                type_info = attr_type.__name__ if hasattr(attr_type, "__name__") else str(attr_type)
                type_module = attr_type.__module__ if hasattr(attr_type, "__module__") else None

                attributes[name] = {
                    "type": type_info,
                    "type_module": type_module,
                    "field": attr_info.field.to_dict(),
                }
            if attr_info.categories is not None:
                categories[name] = attr_info.categories.to_dict()

        return {
            "attributes": attributes,
            "categories": categories,
        }

    @classmethod
    def from_dict(cls, schema_dict: dict[str, Any]) -> "Schema":
        """
        Deserialize a Schema from a JSON dictionary.

        Args:
            schema_dict: Dictionary containing schema data

        Returns:
            Reconstructed Schema instance
        """

        attributes = {}

        for name, attr_dict in schema_dict["attributes"].items():
            field = Field.from_dict(attr_dict["field"])

            # Get categories if present
            categories = None
            if name in schema_dict.get("categories", {}):
                categories = Categories.from_dict(schema_dict["categories"][name])

            # Try to reconstruct the type
            type_name = attr_dict.get("type", "object")
            type_module = attr_dict.get("type_module")

            if type_module == "__union__":
                # Reconstruct Union type from list of component types (new format)
                union_types = []
                for component in type_name:
                    comp_name = component["name"]
                    comp_module = component.get("module")
                    resolved = _resolve_type(comp_name, comp_module)
                    union_types.append(resolved)
                attr_type = reduce(lambda a, b: a | b, union_types)
            else:
                attr_type = _resolve_type(type_name, type_module)

            attributes[name] = AttributeInfo(
                type=attr_type,
                field=field,
                categories=categories,
            )

        return cls(attributes=attributes)
