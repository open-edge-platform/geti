# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import copy
import heapq
import itertools
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, NamedTuple, get_type_hints, overload

import polars as pl

from getidata.categories import Categories
from getidata.converters.base import AttributeRemapperConverter, ConversionError, Converter, MediaBridgeConverter
from getidata.fields.base import Field
from getidata.polars_utils import prepare_dataframe_for_pickle, restore_dataframe_from_pickle
from getidata.schema import AttributeSpec, Schema
from getidata.transform import Transform
from getidata.type_registry import is_type_optional

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence


class ConversionPaths(NamedTuple):
    """
    Container for separated batch and lazy conversion paths.

    The batch converters can be applied immediately to the entire DataFrame,
    while lazy converters must be deferred and applied at sample access time.
    """

    converters: dict[str, list[Converter]]
    lazy_outputs: dict[str, list[Converter]]
    required_inputs_by_output: dict[str, set[str]]
    dependent_outputs_by_input: dict[str, set[str]]


class ConverterRegistry:
    """
    Registry for managing and discovering data converters.

    This class maintains a global registry of converter classes and provides
    functionality for finding and instantiating appropriate converters for
    schema transformations.
    """

    _converter_registry: list[type[Converter]] = []

    @classmethod
    def add_converter(cls, converter: type[Converter]):
        """Add a converter class to the registry."""
        cls._converter_registry.append(converter)

    @classmethod
    def remove_converter(cls, converter: type[Converter]) -> None:
        """Remove a converter class from the registry.

        Args:
            converter: The converter class to remove

        Raises:
            ValueError: If the converter is not found in the registry
        """
        cls._converter_registry.remove(converter)

    @classmethod
    def list_converters(cls) -> Sequence[type[Converter]]:
        """List all registered converter classes as an immutable sequence."""
        return cls._converter_registry


@dataclass(frozen=True)
class _SchemaState:
    """Represents a schema state during A* search."""

    field_to_attr_spec: dict[type[Field], AttributeSpec[Field]]  # Map field types to their AttributeSpec

    def __hash__(self):
        # Hash only field types and their properties, not names
        field_items = []
        for field_type, attr_spec in self.field_to_attr_spec.items():
            # Hash field type, field properties, and categories,
            # but not the attribute name
            field_items.append((field_type, attr_spec.field, attr_spec.categories))
        return hash(tuple(field_items))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _SchemaState):
            return False

        # Compare only field types and their properties, not names
        if set(self.field_to_attr_spec.keys()) != set(other.field_to_attr_spec.keys()):
            return False

        for field_type in self.field_to_attr_spec:
            self_attr_spec = self.field_to_attr_spec[field_type]
            other_attr_spec = other.field_to_attr_spec[field_type]

            # Compare field properties
            if self_attr_spec.field != other_attr_spec.field:
                return False

            # Compare categories only if both are not None (per requirements)
            # This is because None categories mean "don't care" in this context
            if (
                self_attr_spec.categories is not None
                and other_attr_spec.categories is not None
                and self_attr_spec.categories != other_attr_spec.categories
            ):
                return False

        return True

    def get_attr_spec_for_field_type(self, field_type: type[Field]) -> AttributeSpec[Field] | None:
        """Get AttributeSpec for a specific field type."""
        return self.field_to_attr_spec.get(field_type)

    def merge_categories_from(self, other: _SchemaState) -> _SchemaState:
        """
        Create a new state where None categories are filled from another state.

        This is used to propagate categories from the source schema to the target
        schema when the target doesn't have explicit categories defined.

        Args:
            other: The state to take categories from when this state has None

        Returns:
            A new _SchemaState with merged categories
        """
        merged_field_to_attr_spec = {}
        for field_type, attr_spec in self.field_to_attr_spec.items():
            if attr_spec.categories is None and field_type in other.field_to_attr_spec:
                other_attr_spec = other.field_to_attr_spec[field_type]
                if other_attr_spec.categories is not None:
                    # Create a new AttributeSpec with the categories from the source
                    merged_attr_spec = AttributeSpec(
                        name=attr_spec.name,
                        field=attr_spec.field,
                        categories=other_attr_spec.categories,
                    )
                    merged_field_to_attr_spec[field_type] = merged_attr_spec
                    continue
            merged_field_to_attr_spec[field_type] = attr_spec
        return _SchemaState(merged_field_to_attr_spec)


@dataclass
class _SearchNode:
    """Node in the A* search tree."""

    state: _SchemaState
    path: list[Converter]  # Now stores Converter instances directly
    g_cost: float  # Actual cost from start
    h_cost: float  # Heuristic cost to goal

    @property
    def f_cost(self) -> float:
        """Total cost (g + h)."""
        return self.g_cost + self.h_cost

    def __lt__(self, other: _SearchNode) -> bool:
        return self.f_cost < other.f_cost


def _heuristic_cost(current_state: _SchemaState, target_state: _SchemaState) -> float:
    """
    Heuristic function for A* search.
    Returns the number of missing target fields plus field differences as a heuristic.

    This counts both:
    1. Missing field types that need to be created
    2. Field differences where the type exists but properties differ (dtype, format, semantic, etc.)
    3. Category differences where both input and output categories are not None but differ

    Note: Attribute names are ignored in the heuristic as they can be fixed in post-processing.
    """
    cost = 0.0

    current_field_types = set(current_state.field_to_attr_spec.keys())
    target_field_types = set(target_state.field_to_attr_spec.keys())

    # Count missing field types
    missing_field_types = target_field_types - current_field_types
    cost += len(missing_field_types)

    # Count field differences for types that exist in both states
    common_field_types = current_field_types & target_field_types
    for field_type in common_field_types:
        current_attr_spec = current_state.field_to_attr_spec[field_type]
        target_attr_spec = target_state.field_to_attr_spec[field_type]

        # Compare field properties (ignoring names) - if they differ, we need conversion
        if current_attr_spec.field != target_attr_spec.field or (
            current_attr_spec.categories is not None
            and target_attr_spec.categories is not None
            and current_attr_spec.categories != target_attr_spec.categories
        ):
            cost += 1

    return cost


def _resolve_output_attr_spec(
    field_type: type[Field],
    target_state: _SchemaState,
    semantic: str,
    iteration: int,
) -> AttributeSpec[Field]:
    """Resolve the output AttributeSpec for a converter output field type.

    If the target state has a matching field type, use its name/field/categories.
    Otherwise, create a temporary AttributeSpec with a generated name.
    """
    if field_type in target_state.field_to_attr_spec:
        target_attr_spec = target_state.field_to_attr_spec[field_type]
        return AttributeSpec(
            name=target_attr_spec.name,
            field=target_attr_spec.field,
            categories=target_attr_spec.categories,
        )

    # The field does not exist, use a temporary name and create a new instance
    output_name = f"{field_type.__name__.lower()}_temp_{iteration}"
    return AttributeSpec(
        name=output_name,
        field=field_type(semantic=semantic),
        categories=None,
    )


def _get_applicable_converters(
    semantic: str,
    state: _SchemaState,
    target_state: _SchemaState,
    iteration: int = 0,
    direct_only: bool = False,
) -> list[tuple[Converter, _SchemaState]]:
    """Get all converters that can be applied to the current state along with their resulting states.

    Args:
        semantic: The semantic tag being processed
        state: Current schema state
        target_state: Target schema state
        iteration: Current iteration count for uniqueness
        direct_only: If True, only consider converters where all output field types
            are a subset of the input field types (no cross-field-type conversions).
            :class:`MediaBridgeConverter` subclasses are exempt from this restriction
            because they represent format-level narrowing/widening of media
            representations rather than semantic transformations.
    """
    applicable: list[tuple[Converter, _SchemaState]] = []

    # Get available field types
    available_field_types = set(state.field_to_attr_spec.keys())

    for converter_class in ConverterRegistry.list_converters():
        # Check if all required input types are available
        from_types = converter_class.get_from_types()

        # Check if we have the required input types
        if not available_field_types.issuperset(from_types.values()):
            continue

        # Skip cross-field-type converters when direct_only is True,
        # but always allow media bridge converters (e.g. MediaPath→ImagePath).
        if direct_only and not issubclass(converter_class, MediaBridgeConverter):
            to_types = converter_class.get_to_types()
            input_field_types = set(from_types.values())
            output_field_types = set(to_types.values())
            if not output_field_types.issubset(input_field_types):
                continue

        # Collect available input AttributeSpec instances
        converter_kwargs = {
            attr_name: state.field_to_attr_spec[field_type] for attr_name, field_type in from_types.items()
        }

        # Collect desired output AttributeSpec instances
        to_types = converter_class.get_to_types()
        for attr_name, field_type in to_types.items():
            converter_kwargs[attr_name] = _resolve_output_attr_spec(field_type, target_state, semantic, iteration)

        # Create converter instance with all AttributeSpec instances as kwargs
        converter_instance = converter_class(**converter_kwargs)
        if not converter_instance.filter_output_spec():
            continue

        # Fetch the updated output AttributeSpec instances after filter_output_spec()
        updated_output_attr_specs = converter_instance.get_output_attr_specs()

        # Apply converter to get new state
        new_field_to_attr_spec = dict(state.field_to_attr_spec)

        # Keep old attributes instead of removing them
        # (Later we can work on cleanup/rename logic separately)

        # Add produced output types using the updated output_attr_specs
        for attr_spec in updated_output_attr_specs:
            field_type = type(attr_spec.field)
            new_field_to_attr_spec[field_type] = attr_spec

        new_state = _SchemaState(new_field_to_attr_spec)

        applicable.append((converter_instance, new_state))

    return applicable


def _get_optional_field_types_by_semantic(schema: Schema) -> dict[str, set[type[Field]]]:
    """
    Get the field types that are optional in the schema, grouped by semantic.

    There can be multiple optional fields with different field types in the same semantic.

    Args:
        schema: The schema to check

    Returns:
        Dictionary mapping semantic to set of optional field types for that semantic
    """
    result: dict[str, set[type[Field]]] = defaultdict(set)

    for attr_info in schema.attributes.values():
        if is_type_optional(attr_info.type):
            semantic = attr_info.field.semantic
            field_type = type(attr_info.field)
            result[semantic].add(field_type)

    return result


def _group_fields_by_semantic(schema: Schema) -> dict[str, _SchemaState]:
    """
    Group schema attributes by their semantic tags and return as SchemaState objects.

    Args:
        schema: Schema to group

    Returns:
        Dictionary mapping semantic tags to SchemaState objects
    """
    groups: dict[str, dict[type[Field], AttributeSpec[Field]]] = defaultdict(dict)

    for attr_name, attr_info in schema.attributes.items():
        semantic = attr_info.field.semantic

        field_type = type(attr_info.field)
        attr_spec = AttributeSpec(name=attr_name, field=attr_info.field, categories=attr_info.categories)
        groups[semantic][field_type] = attr_spec

    # Convert to SchemaState objects
    return {semantic: _SchemaState(field_to_attr_spec) for semantic, field_to_attr_spec in groups.items()}


def _create_initial_renaming_converter(
    start_state: _SchemaState, target_state: _SchemaState
) -> tuple[AttributeRemapperConverter | None, _SchemaState]:
    """
    Create an initial AttributeRemapperConverter to handle renaming at the beginning.

    Args:
        start_state: Starting state of the schema
        target_state: Target state for this semantic group

    Returns:
        Tuple of (optional AttributeRemapperConverter, updated_start_state after renaming)
    """

    attr_mappings = []
    converter_needed = False
    updated_field_to_attr_spec = dict(start_state.field_to_attr_spec)

    # Used to check for conflicts when renaming
    used_names = {updated_field_to_attr_spec[field_type].name for field_type in updated_field_to_attr_spec}

    for field_type, start_attr_spec in start_state.field_to_attr_spec.items():
        if field_type in target_state.field_to_attr_spec:
            target_attr_spec = target_state.field_to_attr_spec[field_type]
            if start_attr_spec.name != target_attr_spec.name:
                converter_needed = True
                new_name = target_attr_spec.name
                # If the new name would conflict with another attribute in the target_state, use a temporary name
                if new_name in used_names:
                    new_name = f"{new_name}_temp_{id(start_attr_spec)}"
                renamed_attr_spec = AttributeSpec(
                    name=new_name,
                    field=start_attr_spec.field,
                    categories=start_attr_spec.categories,
                )
                attr_mappings.append((start_attr_spec, renamed_attr_spec))
                updated_field_to_attr_spec[field_type] = renamed_attr_spec

    if converter_needed:
        converter = AttributeRemapperConverter(attr_mappings=attr_mappings)
        updated_start_state = _SchemaState(updated_field_to_attr_spec)
        return converter, updated_start_state
    return None, start_state


def _can_lazy_converter_handle_conversion(from_field_type: type[Field], to_field_type: type[Field]) -> bool:
    """
    Check if any lazy converter can handle the conversion from one field type to another.

    Args:
        from_field_type: Source field type
        to_field_type: Target field type
        semantic: The semantic context

    Returns:
        True if a lazy converter can handle this conversion, False otherwise
    """
    for converter_class in ConverterRegistry.list_converters():
        # Only consider lazy converters
        if not getattr(converter_class, "lazy", False):
            continue

        from_types = converter_class.get_from_types()
        to_types = converter_class.get_to_types()

        # Check if this converter takes the from_field_type as input and produces to_field_type as output
        if from_field_type in from_types.values() and to_field_type in to_types.values():
            return True

    return False


def _format_field_sections(
    effective_start_state: _SchemaState,
    target_state: _SchemaState,
    optional_field_types: set[type[Field]],
) -> tuple[str, str]:
    """Format source and target fields into readable multi-line sections.

    Returns:
        Tuple of (source_section, target_section) strings.
    """
    source_lines = [f"  {asp.name}: {asp.field}" for asp in effective_start_state.field_to_attr_spec.values()]
    source_section = ("Source fields:\n" + "\n".join(source_lines)) if source_lines else "Source fields: (none)"

    target_lines = [
        f"  {asp.name}: {asp.field}{' (optional)' if ft in optional_field_types else ''}"
        for ft, asp in target_state.field_to_attr_spec.items()
    ]
    target_section = ("Target fields:\n" + "\n".join(target_lines)) if target_lines else "Target fields: (none)"

    return source_section, target_section


def _diagnose_conversion_issues(
    effective_start_state: _SchemaState,
    target_state: _SchemaState,
    optional_field_types: set[type[Field]],
    reachable_types: set[type[Field]],
) -> tuple[list[str], list[str]]:
    """Classify each unsatisfied target field as missing or property-incompatible.

    Returns:
        Tuple of (truly_missing_fields, type_conversion_issues) diagnostic line lists.
    """
    source_field_types = set(effective_start_state.field_to_attr_spec.keys())
    type_conversion_issues: list[str] = []
    truly_missing_fields: list[str] = []

    for target_field_type, target_attr_spec in target_state.field_to_attr_spec.items():
        optional_tag = " (optional)" if target_field_type in optional_field_types else ""

        if target_field_type in source_field_types:
            src_attr_spec = effective_start_state.field_to_attr_spec[target_field_type]
            if src_attr_spec.field != target_attr_spec.field and not _can_lazy_converter_handle_conversion(
                type(src_attr_spec.field),
                type(target_attr_spec.field),
            ):
                type_conversion_issues.append(
                    f"  - '{target_attr_spec.name}' ({target_field_type.__name__}){optional_tag}: "
                    f"source has {src_attr_spec.field}, target needs {target_attr_spec.field}"
                )
        elif target_field_type not in reachable_types:
            truly_missing_fields.append(
                f"  - '{target_attr_spec.name}' ({target_field_type.__name__}){optional_tag}: "
                f"no registered converter can produce this field type from the available source fields"
            )

    return truly_missing_fields, type_conversion_issues


def _assemble_diagnosis(truly_missing_fields: list[str], type_conversion_issues: list[str]) -> str:
    """Build the diagnosis section from classified issue lists."""
    parts: list[str] = []
    if truly_missing_fields:
        parts.append("Missing field types:\n" + "\n".join(truly_missing_fields))
    if type_conversion_issues:
        parts.append(
            "Incompatible field properties (no converter handles this conversion):\n"
            + "\n".join(type_conversion_issues)
        )
    if not parts:
        parts.append(
            "All required field types are present, but converters could not satisfy "
            "all target field properties simultaneously."
        )
    return "\n\n".join(parts)


def _create_conversion_error_message(
    effective_start_state: _SchemaState,
    target_state: _SchemaState,
    optional_field_types: set[type[Field]] | None = None,
    semantic: str | None = None,
) -> str:
    """
    Create a detailed error message when no conversion path is found.

    Args:
        effective_start_state: The effective source state after initial renaming
        target_state: Target state for this semantic
        optional_field_types: Set of optional field types (should not be reported as missing)
        semantic: The semantic tag being processed (included in message for context)

    Returns:
        Formatted error message string
    """
    if optional_field_types is None:
        optional_field_types = set()

    header = (
        f"No conversion path found for semantic group '{semantic}'."
        if semantic is not None
        else "No conversion path found."
    )

    source_section, target_section = _format_field_sections(
        effective_start_state,
        target_state,
        optional_field_types,
    )

    reachable_types = (
        _get_reachable_field_types(effective_start_state, semantic)
        if semantic is not None
        else set(effective_start_state.field_to_attr_spec.keys())
    )

    truly_missing, prop_issues = _diagnose_conversion_issues(
        effective_start_state,
        target_state,
        optional_field_types,
        reachable_types,
    )

    diagnosis_section = _assemble_diagnosis(truly_missing, prop_issues)

    return f"{header}\n\n{source_section}\n\n{target_section}\n\n{diagnosis_section}"


def _find_conversion_path_for_semantic(
    start_state: _SchemaState,
    target_state: _SchemaState,
    semantic: str,
    optional_field_types: set[type[Field]] | None = None,
    direct_only: bool = False,
) -> tuple[list[Converter], _SchemaState]:
    """
    Find conversion path for fields with a specific semantic tag.

    Args:
        start_state: Source state for this semantic
        target_state: Target state for this semantic
        semantic: The semantic tag being processed
        optional_field_types: Set of optional field types for this semantic
        direct_only: If True, only consider converters where all output field types
            are a subset of the input field types (no cross-field-type conversions).
            :class:`MediaBridgeConverter` subclasses are exempt from this restriction.

    Returns:
        Tuple of (list of converters needed for this semantic group, updated target state)

    Raises:
        ConversionError: If no conversion path is found for this semantic
    """
    # Apply initial renaming at the beginning if needed
    initial_converter, effective_start_state = _create_initial_renaming_converter(start_state, target_state)
    initial_converters = [initial_converter] if initial_converter else []

    # If we already have all required fields after initial renaming, we might be done
    if effective_start_state == target_state:
        # Merge categories from start state into target state where target has None
        merged_state = target_state.merge_categories_from(effective_start_state)
        return initial_converters, merged_state

    # Initialize A* search from the effective start state
    open_set: list[_SearchNode] = []
    closed_set: set[_SchemaState] = set()

    start_node = _SearchNode(
        state=effective_start_state,
        path=initial_converters,  # Add initial converters to the start node path
        g_cost=len(initial_converters),  # Account for initial converters in cost
        h_cost=_heuristic_cost(effective_start_state, target_state),
    )

    heapq.heappush(open_set, start_node)

    while open_set:
        current_node = heapq.heappop(open_set)

        if current_node.state in closed_set:
            continue

        closed_set.add(current_node.state)

        # Check if we've reached the goal - all target fields must match exactly
        if _heuristic_cost(current_node.state, target_state) == 0:
            # We've reached the goal, return the path
            # Merge categories from start state into the result state where it has None
            merged_state = current_node.state.merge_categories_from(effective_start_state)
            return current_node.path, merged_state

        # Explore neighbors
        for converter, new_state in _get_applicable_converters(
            semantic,
            current_node.state,
            target_state,
            current_node.g_cost,
            direct_only=direct_only,
        ):
            if new_state in closed_set:
                continue

            new_path = [*current_node.path, converter]
            # Base cost of 1 per converter, plus a small penalty for
            # cross-field-type converters (those that derive an output field
            # type from a different input field type).  This ensures that
            # direct in-place transformations (e.g. BBoxField→BBoxField for
            # format/dtype changes) are preferred over cross-type derivations
            # (e.g. KeypointsField→BBoxField) when integer costs are equal.
            input_field_types = {type(s.field) for s in converter.get_input_attr_specs()}
            output_field_types = {type(s.field) for s in converter.get_output_attr_specs()}
            is_cross_field_type = not output_field_types.issubset(input_field_types)
            new_g_cost = current_node.g_cost + 1 + (0.1 if is_cross_field_type else 0)
            new_h_cost = _heuristic_cost(new_state, target_state)

            new_node = _SearchNode(state=new_state, path=new_path, g_cost=new_g_cost, h_cost=new_h_cost)

            heapq.heappush(open_set, new_node)

    # No path found - create a more informative error message
    error_msg = _create_conversion_error_message(effective_start_state, target_state, optional_field_types, semantic)
    raise ConversionError(error_msg)


def _is_converter_lazy(
    converter: Converter,
    lazy_fields: dict[str, bool],
    input_specs: list[AttributeSpec[Field]],
    output_specs: list[AttributeSpec[Field]],
) -> None:
    if converter.lazy or any(attr_spec.name in lazy_fields for attr_spec in input_specs):
        # Mark all output fields as lazy
        for attr_spec in output_specs:
            lazy_fields[attr_spec.name] = True


def _separate_batch_and_lazy_converters(
    conversion_path: list[Converter],
) -> ConversionPaths:
    """
    Separate converters into batch and lazy lists based on dependencies.

    If a converter is lazy, all converters that depend on its output must also be lazy.
    Also tracks which lazy converters are required for each output attribute.

    Args:
        conversion_path: The complete conversion path from A* search

    Returns:
        ConversionPaths with separated batch and lazy converter lists
    """
    if not conversion_path:
        return ConversionPaths(
            converters={},
            lazy_outputs={},
            required_inputs_by_output={},
            dependent_outputs_by_input={},
        )

    # Track which outputs must be lazy
    lazy_fields: dict[str, bool] = defaultdict(bool)  # Maps fields whether they were produced lazily

    required_inputs_by_output: dict[str, set[str]] = defaultdict(set)

    for converter in conversion_path:
        input_specs = converter.get_input_attr_specs()
        output_specs = converter.get_output_attr_specs()
        _is_converter_lazy(
            converter=converter,
            lazy_fields=lazy_fields,
            input_specs=input_specs,
            output_specs=output_specs,
        )

        required_inputs = [required_inputs_by_output.get(attr_spec.name, {attr_spec.name}) for attr_spec in input_specs]
        flattened_required_inputs = set(itertools.chain(*required_inputs))
        for attr_spec in output_specs:
            required_inputs_by_output[attr_spec.name] = flattened_required_inputs

    # Collect lazy converters by output attribute
    converters_by_output: dict[str, list[Converter]] = defaultdict(list)

    # Iterate through converters in reverse to propagate output dependencies
    dependents_by_output: dict[str, set[str]] = defaultdict(set)

    for converter in reversed(conversion_path):
        # This is a lazy converter - track its outputs
        dependents = set()

        output_specs = converter.get_output_attr_specs()
        for attr_spec in output_specs:
            dependents.update(dependents_by_output.get(attr_spec.name, []))
            dependents.add(attr_spec.name)

        for dependent in dependents:
            converters_by_output[dependent].append(converter)

        # Propagate dependencies from outputs to inputs
        input_specs = converter.get_input_attr_specs()
        for input_spec in input_specs:
            dependents_by_output[input_spec.name].update(dependents)

    # Reverse all chains to get dependencies-first order
    for output_name, chain in converters_by_output.items():
        converters_by_output[output_name] = list(reversed(chain))

    return ConversionPaths(
        converters=converters_by_output,
        lazy_outputs=lazy_fields,
        required_inputs_by_output=required_inputs_by_output,
        dependent_outputs_by_input=dependents_by_output,
    )


@overload
def converter(cls: type[Converter], /) -> type[Converter]:
    """Overload for @converter (no parentheses)."""


@overload
def converter(*, lazy: bool = False) -> Callable[[type[Converter]], type[Converter]]:
    """Overload for @converter() or @converter(lazy=True)."""


def converter(
    cls: type[Converter] | None = None, /, *, lazy: bool = False
) -> type[Converter] | Callable[[type[Converter]], type[Converter]]:
    """Register a converter class and configure its lazy loading behavior.

    This decorator automatically registers converter classes with the global
    converter registry and sets their lazy evaluation mode. The converter
    class must define at least one output_* attribute with type hints.

    Args:
        lazy: If True, this converter will only be applied during lazy
              evaluation in Dataset.__getitem__. If False, it will be
              applied during batch conversion operations. Lazy converters
              automatically make all dependent converters lazy as well.

    Usage:
        @converter
        class ImageToTensorConverter(Converter):
            input_image: AttributeSpec
            output_tensor: AttributeSpec

            def convert(self, df: pl.DataFrame) -> pl.DataFrame:
                # conversion logic
                return df

        @converter(lazy=True)
        class ImagePathToImageConverter(MediaBridgeConverter):
            input_path: AttributeSpec
            output_image: AttributeSpec

            def convert(self, df: pl.DataFrame) -> pl.DataFrame:
                # lazy conversion logic
                return df
    """

    def decorator(cls: type[Converter]) -> type[Converter]:
        # Validate converter class by checking for required attributes
        hints = get_type_hints(cls)

        # Ensure at least one output attribute is defined
        output_attrs = [name for name in hints if name.startswith("output_")]
        if not output_attrs:
            raise TypeError(f"{cls.__name__} must define at least one 'output_*' attribute")

        # Set the lazy attribute directly on the class
        cls.lazy = lazy

        # Register with the global converter registry for discovery
        ConverterRegistry.add_converter(cls)

        return cls

    # Handle both @converter and @converter() syntax patterns
    if cls is None:
        # Called with parentheses: @converter() or @converter(lazy=True)
        return decorator

    # Called without parentheses: @converter
    return decorator(cls)


def _get_reachable_field_types(
    start_state: _SchemaState,
    semantic: str,
    direct_only: bool = False,
) -> set[type[Field]]:
    """
    Get all field types that can be reached from the start state through converters.

    This performs a breadth-first search to find all field types that can be
    produced by applying converters starting from the available field types,
    respecting semantic boundaries.

    Args:
        start_state: Starting state with available field types
        semantic: The semantic tag to filter by (only fields with matching semantic are considered)
        direct_only: If True, only consider converters where all output field types
            are a subset of the input field types (no cross-field-type conversions).
            :class:`MediaBridgeConverter` subclasses are exempt from this restriction.

    Returns:
        Set of all reachable field types (including those already in start_state)
    """
    reachable: set[type[Field]] = {
        field_type
        for field_type, attr_spec in start_state.field_to_attr_spec.items()
        if attr_spec.field.semantic == semantic
    }
    frontier: set[type[Field]] = set(reachable)

    while frontier:
        new_frontier: set[type[Field]] = set()

        for converter_class in ConverterRegistry.list_converters():
            from_types = converter_class.get_from_types()
            to_types = converter_class.get_to_types()

            # Skip cross-field-type converters when direct_only is True,
            # but always allow media bridge converters.
            if direct_only and not issubclass(converter_class, MediaBridgeConverter):
                input_field_types = set(from_types.values())
                output_field_types = set(to_types.values())
                if not output_field_types.issubset(input_field_types):
                    continue

            # Check if all required input types are available
            if reachable.issuperset(from_types.values()):
                # Add all output types that we haven't seen yet
                for field_type in to_types.values():
                    if field_type not in reachable:
                        new_frontier.add(field_type)
                        reachable.add(field_type)

        frontier = new_frontier

    return reachable


def _filter_unreachable_optional_fields(
    target_state: _SchemaState,
    reachable_types: set[type[Field]],
    optional_field_types: set[type[Field]],
) -> _SchemaState:
    """
    Filter out optional fields from target state if they cannot be reached.

    Args:
        target_state: The target state to filter
        reachable_types: Set of field types that can be reached from source
        optional_field_types: Set of optional field types for this semantic

    Returns:
        A new _SchemaState with unreachable optional fields removed
    """
    if not optional_field_types:
        return target_state

    filtered_field_to_attr_spec = {}

    for field_type, attr_spec in target_state.field_to_attr_spec.items():
        # Keep the field if it's reachable OR if it's not optional (required fields must be kept)
        if field_type in reachable_types or field_type not in optional_field_types:
            filtered_field_to_attr_spec[field_type] = attr_spec

    return _SchemaState(filtered_field_to_attr_spec)


def find_conversion_path(
    from_schema: Schema,
    to_schema: Schema,
    direct_only: bool = False,
) -> tuple[ConversionPaths, dict[str, Categories]]:
    """
    Find an optimal sequence of converters using A* search, grouped by semantic.

    Fields with the same semantic can be converted between each other, but
    conversion across semantic boundaries is not allowed.

    Optional fields (those with Union[..., None] type) that cannot be reached
    from the source schema are automatically skipped.

    Args:
        from_schema: Source schema
        to_schema: Target schema
        direct_only: If True, only consider converters where all output field types
            are a subset of the input field types (no cross-field-type conversions).
            For example, BBoxField→BBoxField format/dtype converters are allowed,
            but BBoxField→PolygonField converters are skipped.
            :class:`MediaBridgeConverter` subclasses (e.g., MediaPathField→ImagePathField)
            are always allowed regardless of this flag.

    Returns:
        Tuple of (ConversionPaths with separated batch and lazy converter lists,
                 dictionary of attribute names to inferred categories)

    Raises:
        ConversionError: If no conversion path is found for required fields
    """
    # Group fields by semantic in both schemas
    start_groups = _group_fields_by_semantic(from_schema)
    target_groups = _group_fields_by_semantic(to_schema)

    # Get optional field types from target schema, grouped by semantic
    optional_field_types_by_semantic = _get_optional_field_types_by_semantic(to_schema)

    # Collect all converters needed across all semantic groups
    all_converters: list[Converter] = []

    # Process each semantic group in the target schema
    for semantic, target_state in target_groups.items():
        # Get corresponding source state for this semantic (if any)
        start_state = start_groups.get(semantic, _SchemaState({}))

        # Determine which field types are reachable from the start state
        reachable_types = _get_reachable_field_types(start_state, semantic, direct_only=direct_only)

        # Get optional field types for this specific semantic
        optional_field_types = optional_field_types_by_semantic.get(semantic, set())

        # Filter out optional fields that cannot be reached
        filtered_target_state = _filter_unreachable_optional_fields(target_state, reachable_types, optional_field_types)

        # Find conversion path for this semantic group (with filtered target)
        semantic_converters, updated_target_state = _find_conversion_path_for_semantic(
            start_state, filtered_target_state, semantic, optional_field_types, direct_only=direct_only
        )

        # Update the target state with any inferred categories
        target_groups[semantic] = updated_target_state

        all_converters.extend(semantic_converters)

    # Reconstruct the updated schema with inferred categories
    # Use the list of attributes from to_schema rather than just the target_groups
    # because the target_groups may include attributes which are deleted in the final to_schema.
    # We do not want to include those attributes into the inferred_categories.
    inferred_categories: dict[str, Categories] = {}
    for attr_name, attr_info in to_schema.attributes.items():
        semantic = attr_info.field.semantic
        field_type = type(attr_info.field)
        # Only add categories for fields that were actually converted (not filtered out)
        if field_type in target_groups[semantic].field_to_attr_spec:
            attr_spec = target_groups[semantic].field_to_attr_spec[field_type]
            if attr_spec.categories is not None:
                inferred_categories[attr_name] = attr_spec.categories

    # Separate batch and lazy converters
    conversion_paths = _separate_batch_and_lazy_converters(all_converters)

    return conversion_paths, inferred_categories


class ConverterTransform(Transform):
    def __init__(self, parent: Transform, schema: Schema, conversion_paths: ConversionPaths):
        super().__init__(schema)

        lazy_inputs = parent.get_lazy_attributes()

        lazy_outputs = set(conversion_paths.lazy_outputs)
        for input in lazy_inputs:
            lazy_outputs.update(conversion_paths.dependent_outputs_by_input[input])
        self._lazy_outputs = lazy_outputs

        batch_outputs = self.get_batch_attributes()

        self._parent = parent
        self._conversion_paths = conversion_paths
        self._df_input_columns = set()
        self._df = pl.DataFrame()
        self._applied_converters: set[Converter] = set()

        self.apply(batch_outputs)

    def __getstate__(self) -> dict:
        """Prepare the transform for pickling.

        Polars DataFrames with Object columns cannot be serialized using Polars' default
        serialization. This method extracts Object columns as Python lists before pickling.
        """
        state = self.__dict__.copy()
        return prepare_dataframe_for_pickle(self._df, "_df", state)

    def __setstate__(self, state: dict) -> None:
        """Restore the transform after unpickling.

        Reconstructs Object columns from the Python lists stored during pickling.
        """
        state["_df"] = restore_dataframe_from_pickle(state, "_df")
        self.__dict__.update(state)

    def apply(self, fields: Sequence[str]) -> pl.DataFrame:
        required_inputs = set()
        for field in fields:
            if field in self._conversion_paths.converters:
                required_inputs.update(self._conversion_paths.required_inputs_by_output[field])

        parent_df = self._parent.apply(required_inputs)
        input_columns = set(parent_df.columns)
        new_columns = set(parent_df.columns) - self._df_input_columns

        self._df = self._df.with_columns(parent_df.select(new_columns))
        self._df_input_columns = input_columns

        for field in fields:
            converters = self._conversion_paths.converters.get(field, None)

            if converters is not None:
                for converter in converters:
                    if converter not in self._applied_converters:
                        if not self._can_apply_converter(converter):
                            # Defer this converter; it will be attempted again on future apply() calls
                            # once the necessary input columns have been materialized.
                            continue

                        self._df = converter.convert(self._df)
                        self._applied_converters.add(converter)

        return self._df

    def _can_apply_converter(self, converter: Converter) -> bool:
        """
        Only apply the converter when all of its required input columns are present.
        This prevents race conditions when converters are evaluated lazily in
        multi-worker dataloaders, where some columns may not be materialized yet.
        """
        for attr_spec in converter.get_input_attr_specs():
            required_cols = attr_spec.field.to_polars_schema(attr_spec.name).keys()
            for col in required_cols:
                if col not in self._df.columns:
                    return False
        return True

    def get_lazy_attributes(self) -> set[str]:
        return self._lazy_outputs

    def slice(self, offset: int, length: int | None = None) -> Transform:
        instance = copy.copy(self)
        instance._parent = self._parent.slice(offset, length)
        instance._applied_converters = copy.copy(self._applied_converters)
        instance._df = self._df.slice(offset, length)
        return instance

    def __len__(self):
        return len(self._df)
