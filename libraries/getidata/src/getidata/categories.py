# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Categories definitions for the dataset system.

This module provides category management functionality using standard dataclasses
instead of attrs, taking inspiration from the original Categories implementation.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from enum import IntEnum
from functools import cache
from typing import TYPE_CHECKING, Any, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Iterator


class LabelSemantic(IntEnum):
    """
    Semantic meaning of a label for classification tasks.
    NORMAL: Indicates a label representing normal/expected data.
    ANOMALOUS: Indicates a label representing anomalous/outlier data.
    """

    NORMAL = 1
    ANOMALOUS = 2


class GroupType(IntEnum):
    """Types of label groups for organizing labels."""

    EXCLUSIVE = 0  # Only one label from the group can be assigned
    INCLUSIVE = 1  # Multiple labels from the group can be assigned
    RESTRICTED = 2  # For empty labels

    def to_str(self) -> str:
        return self.name.lower()

    @classmethod
    def from_str(cls, text: str) -> GroupType:
        try:
            return cls[text.upper()]
        except KeyError:
            raise ValueError(f"Invalid GroupType: {text}")


@dataclass(frozen=True)
class Categories:
    """
    A base class for annotation metainfo. It is supposed to include
    dataset-wide metainfo like available labels, label colors,
    label attributes etc.
    """

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize this Categories instance to a JSON-compatible dictionary.

        This default implementation should be overridden by subclasses that have
        specific serialization needs. Returns just the type by default.

        Returns:
            Dictionary representation of this Categories instance
        """
        return {"type": self.__class__.__name__}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Categories:
        """
        Deserialize a Categories instance from a JSON dictionary.

        This method uses polymorphic dispatch to create the correct subclass
        based on the "type" field in the dictionary.

        Args:
            data: Dictionary containing serialized Categories data

        Returns:
            Reconstructed Categories instance of the appropriate subclass
        """
        cat_type = data.get("type")

        if not cat_type:
            raise ValueError("Categories dictionary must have a 'type' field")

        # Import subclasses to make them available
        subclass_map = {
            "LabelCategories": LabelCategories,
            "HierarchicalLabelCategories": HierarchicalLabelCategories,
            "MaskCategories": MaskCategories,
            "KeypointCategories": KeypointCategories,
        }

        if cat_type in subclass_map:
            return subclass_map[cat_type].from_dict(data)
        # Unknown type - return base Categories with just the type info
        # This allows forward compatibility with new category types
        raise ValueError(f"Unknown categories type: {cat_type}")

    def __getitem__(self, idx: int) -> Any:
        """Get category by index"""
        raise NotImplementedError

    def __len__(self) -> int:
        """Get the number of categories"""
        raise NotImplementedError

    def __iter__(self):
        """Iterate over the categories"""
        raise NotImplementedError


@dataclass(frozen=True)
class BaseLabelCategories(Categories):
    """
    Base label categories class.

    This class ensures fields related to labels will have a label categories attached to the attributes spec.
    """


@dataclass(frozen=True)
class LabelCategories(BaseLabelCategories):
    """
    Represents a group of labels with a specific group type and semantics.
    Use this for simple, non-hierarchical tasks.
    """

    labels: tuple[str, ...] = field(default_factory=tuple)
    group_type: GroupType = GroupType.EXCLUSIVE
    label_semantics: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate that there are no duplicate labels."""
        if isinstance(self.labels, list):
            object.__setattr__(self, "labels", tuple(self.labels))
        elif not isinstance(self.labels, tuple):
            raise TypeError("labels must be a tuple of strings")

        seen = set()
        for label in self.labels:
            if label in seen:
                raise ValueError(f"Duplicate label: {label}")
            seen.add(label)

    @property
    @cache
    def _index_map(self) -> dict[str, int]:
        """Cached mapping from label names to indices."""
        return {label: idx for idx, label in enumerate(self.labels)}

    def find(self, name_or_semantic: str) -> tuple[int | None, str | None]:
        """
        Find a label by name or LabelSemantic.

        Args:
            name_or_semantic: The label name or LabelSemantic to find

        Returns:
            A tuple of (index, category) or (None, None) if not found
        """
        if isinstance(name_or_semantic, LabelSemantic):
            label = self.label_semantics.get(name_or_semantic)
            if label is None:
                return None, None
        else:
            label = name_or_semantic

        index = self._index_map.get(label)
        if index is not None:
            return index, self.labels[index]
        return None, None

    def __getitem__(self, idx: int) -> str:
        """Get category by index."""
        return self.labels[idx]

    def __contains__(self, value: int | str | LabelSemantic) -> bool:
        """Check if a label exists by name, index, or semantic."""
        if isinstance(value, LabelSemantic):
            return value in self.label_semantics
        if isinstance(value, str):
            return value in self.labels
        return 0 <= value < len(self.labels)

    def __len__(self) -> int:
        """Get the number of labels."""
        return len(self.labels)

    def __iter__(self):
        """Iterate over label."""
        return iter(self.labels)

    def __hash__(self):
        # Include label_semantics in the hash
        return hash((self.labels, self.group_type, frozenset(self.label_semantics.items())))

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize to a JSON-compatible dictionary.

        Returns:
            Dictionary representation of this LabelCategories instance
        """
        return {
            "type": "LabelCategories",
            "labels": list(self.labels),
            "group_type": self.group_type.name,
            "label_semantics": {
                k.name if isinstance(k, LabelSemantic) else str(k): v for k, v in self.label_semantics.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LabelCategories:
        """
        Deserialize from a JSON dictionary.

        Args:
            data: Dictionary containing serialized LabelCategories data

        Returns:
            Reconstructed LabelCategories instance
        """
        # Reconstruct label_semantics with proper LabelSemantic keys
        label_semantics = {}
        for k, v in data.get("label_semantics", {}).items():
            try:
                key = LabelSemantic[k]
            except KeyError:
                key = k
            label_semantics[key] = v

        return cls(
            labels=tuple(data["labels"]),
            group_type=GroupType[data["group_type"]],
            label_semantics=label_semantics,
        )


@dataclass(frozen=True)
class HierarchicalLabelCategory:
    """Represents a single label category with hierarchical support."""

    name: str
    parent: str = field(default="")
    label_semantics: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate that name is not empty."""
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Label name cannot be empty and must be a string")

    def __hash__(self):
        return hash((self.name, self.parent, frozenset(self.label_semantics.items())))


@dataclass(frozen=True)
class LabelGroup:
    """Represents a group of labels with a specific group type."""

    name: str
    labels: tuple[str, ...] = field(default_factory=tuple)
    group_type: GroupType = GroupType.EXCLUSIVE

    def __post_init__(self):
        """Validate that name is not empty and labels is a tuple."""
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Label group name cannot be empty and must be a string")


@dataclass(frozen=True)
class HierarchicalLabelCategories(BaseLabelCategories):
    """
    Represents hierarchical label categories with groups and parent-child relationships.
    Use this for complex hierarchical classification tasks.
    """

    items: tuple[HierarchicalLabelCategory, ...] = field(default_factory=tuple)
    label_groups: tuple[LabelGroup, ...] = field(default_factory=tuple)
    label_semantics: dict = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.items, tuple):
            raise TypeError("items must be a tuple of HierarchicalLabelCategory")
        if not isinstance(self.label_groups, tuple):
            raise TypeError("label_groups must be a tuple of LabelGroup")

        # Validate no duplicate names
        all_label_names = self._get_all_label_names()

        # Validate that all parents exist
        for item in self.items:
            if item.parent and item.parent not in all_label_names:
                raise ValueError(f"Parent '{item.parent}' not found for label '{item.name}'")

        # Validate that all labels in groups exist
        for group in self.label_groups:
            for label_name in group.labels:
                if label_name not in all_label_names:
                    raise ValueError(f"Label '{label_name}' in group '{group.name}' not found in items")

    def _get_all_label_names(self) -> set[str]:
        """Get all label names and check for duplicates."""
        seen_names = set()
        for item in self.items:
            if item.name in seen_names:
                raise ValueError(f"Duplicate label name: {item.name}")
            seen_names.add(item.name)

            # Also check for name label_semantics
            # TODO: Remove this check after migrating completely to new system
            if "name" in item.label_semantics:
                name = item.label_semantics["name"]
                if name not in seen_names:
                    seen_names.add(name)
        return seen_names

    @property
    @cache
    def _index_map(self) -> dict[str, int]:
        """Cached mapping from label names to indices."""
        return {item.name: idx for idx, item in enumerate(self.items)}

    @property
    @cache
    def _children_map(self) -> dict[str, tuple[str, ...]]:
        """Cached mapping from parent names to child names."""
        children_map: defaultdict[str, list[str]] = defaultdict(list)
        for item in self.items:
            if item.parent:
                children_map[item.parent].append(item.name)
        return {parent: tuple(children) for parent, children in children_map.items()}

    @property
    def labels(self) -> tuple[str, ...]:
        """Get all label names for compatibility."""
        return tuple(item.name for item in self.items)

    def find(self, name: str) -> tuple[int | None, HierarchicalLabelCategory | None]:
        """
        Find a label by name.

        Args:
            name: The label name to find

        Returns:
            A tuple of (index, category) or (None, None) if not found
        """
        index = self._index_map.get(name)
        if index is not None:
            return index, self.items[index]
        return None, None

    def get_children(self, parent_name: str) -> tuple[str, ...]:
        """
        Get all children of a parent label.

        Args:
            parent_name: The name of the parent label

        Returns:
            Tuple of child label names
        """
        return self._children_map.get(parent_name, ())

    def get_parent(self, label_name: str) -> str | None:
        """
        Get the parent of a label.

        Args:
            label_name: The name of the label

        Returns:
            Parent name or None if no parent
        """
        index = self._index_map.get(label_name)
        if index is not None:
            return self.items[index].parent
        return None

    def get_hierarchy_level(self, label_name: str) -> int:
        """
        Get the hierarchy level of a label (0 for root, 1 for first level children, etc.)

        Args:
            label_name: The name of the label

        Returns:
            Hierarchy level
        """
        level = 0
        current = label_name
        while True:
            parent = self.get_parent(current)
            if not parent:
                break
            level += 1
            current = parent
        return level

    def __getitem__(self, idx: int) -> HierarchicalLabelCategory:
        """Get category by index."""
        return self.items[idx]

    def __contains__(self, value: int | str) -> bool:
        """Check if a label exists by name or index."""
        if isinstance(value, str):
            return value in self._index_map
        return 0 <= value < len(self.items)

    def __len__(self) -> int:
        """Get the number of labels."""
        return len(self.items)

    def __iter__(self) -> Iterator[HierarchicalLabelCategory]:
        """Iterate over label categories."""
        return iter(self.items)

    def __hash__(self):
        # Hash label_groups via value-based representation to avoid relying on their own hash implementation.
        lg_repr = tuple((lg.name, tuple(lg.labels), lg.group_type) for lg in self.label_groups)
        return hash((self.items, lg_repr, frozenset(self.label_semantics.items())))

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize to a JSON-compatible dictionary.

        Returns:
            Dictionary representation of this HierarchicalLabelCategories instance
        """
        return {
            "type": "HierarchicalLabelCategories",
            "items": [
                {
                    "name": item.name,
                    "parent": item.parent,
                    "label_semantics": {
                        k.name if isinstance(k, LabelSemantic) else str(k): v for k, v in item.label_semantics.items()
                    },
                }
                for item in self.items
            ],
            "label_groups": [
                {
                    "name": group.name,
                    "labels": list(group.labels),
                    "group_type": group.group_type.name,
                }
                for group in self.label_groups
            ],
            "label_semantics": {
                k.name if isinstance(k, LabelSemantic) else str(k): v for k, v in self.label_semantics.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HierarchicalLabelCategories:
        """
        Deserialize from a JSON dictionary.

        Args:
            data: Dictionary containing serialized HierarchicalLabelCategories data

        Returns:
            Reconstructed HierarchicalLabelCategories instance
        """
        # Reconstruct items
        items = []
        for item_dict in data["items"]:
            item_label_semantics = {}
            for k, v in item_dict.get("label_semantics", {}).items():
                try:
                    key = LabelSemantic[k]
                except KeyError:
                    key = k
                item_label_semantics[key] = v

            items.append(
                HierarchicalLabelCategory(
                    name=item_dict["name"],
                    parent=item_dict.get("parent", ""),
                    label_semantics=item_label_semantics,
                )
            )

        # Reconstruct label groups
        label_groups = []
        for group_dict in data.get("label_groups", []):
            label_groups.append(
                LabelGroup(
                    name=group_dict["name"],
                    labels=tuple(group_dict["labels"]),
                    group_type=GroupType[group_dict["group_type"]],
                )
            )

        # Reconstruct label_semantics
        label_semantics = {}
        for k, v in data.get("label_semantics", {}).items():
            try:
                key = LabelSemantic[k]
            except KeyError:
                key = k
            label_semantics[key] = v

        return cls(
            items=tuple(items),
            label_groups=tuple(label_groups),
            label_semantics=label_semantics,
        )


class RgbColor(NamedTuple):
    """RGB color representation with named fields."""

    r: int
    g: int
    b: int


@dataclass(frozen=True)
class Colormap:
    """
    A colormap that stores index-to-color mappings and provides efficient
    reverse lookup via an inverse colormap property.
    """

    data: dict[int, RgbColor] = field(default_factory=dict)

    def __post_init__(self):
        """Validate that there are no duplicate colors"""
        object.__setattr__(self, "_inverse_colormap", {v: k for k, v in self.data.items()})

    @property
    def inverse_colormap(self) -> dict[RgbColor, int]:
        """Get the inverse colormap (color -> index mapping)."""
        return getattr(self, "_inverse_colormap")

    def __hash__(self):
        """Compute a hash based on the colormap data."""
        return hash(frozenset(self.data.items()))

    def __getitem__(self, index: int) -> RgbColor:
        """Get color by index."""
        return self.data[index]

    def __contains__(self, index: int) -> bool:
        """Check if an index exists in the colormap."""
        return index in self.data

    def __len__(self) -> int:
        """Get the number of colors in the colormap."""
        return len(self.data)

    def __iter__(self) -> Iterator[tuple[int, RgbColor]]:
        """Iterate over colormap items."""
        return iter(self.data.items())

    def get(self, index: int, default: RgbColor | None = None) -> RgbColor | None:
        """Get color by index with default."""
        return self.data.get(index, default)

    def __eq__(self, other: object) -> bool:
        """Compare with another Colormap or dictionary."""
        if isinstance(other, Colormap):
            return self.data == other.data
        if isinstance(other, dict):
            return self.data == other
        return False


def generate_colormap(length: int = 256, *, include_background: bool = True) -> dict[int, tuple[int, int, int]]:
    """
    Generate an index -> (R, G, B) mapping using the PASCAL VOC colormap algorithm.

    Args:
        length: The number of colors to generate.
        include_background: If True, the result includes the item "0: (0, 0, 0)",
            typically used as background color. Otherwise, indices still start from 0
            but (0, 0, 0) is not included.

    Returns:
        Mapping from index to an (R, G, B) tuple.
    """
    offset = int(not include_background)
    colormap = {}
    for index in range(length):
        value = index + offset
        rgb = [0, 0, 0]
        for shift in range(7, -1, -1):
            for channel in range(3):
                rgb[channel] |= ((value >> channel) & 1) << shift
            value >>= 3
        colormap[index] = (rgb[0], rgb[1], rgb[2])
    return colormap


@dataclass(frozen=True)
class MaskCategories(Categories):
    """
    Describes a color map for segmentation masks.
    """

    labels: list[str] = field(default_factory=list)
    colormap: Colormap = field(default_factory=Colormap)

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize to a JSON-compatible dictionary.

        Returns:
            Dictionary representation of this MaskCategories instance
        """
        colormap_data = self.colormap.data if isinstance(self.colormap, Colormap) else self.colormap
        return {
            "type": "MaskCategories",
            "labels": list(self.labels),
            "colormap": {str(idx): [color.r, color.g, color.b] for idx, color in colormap_data.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MaskCategories:
        """
        Deserialize from a JSON dictionary.

        Args:
            data: Dictionary containing serialized MaskCategories data

        Returns:
            Reconstructed MaskCategories instance
        """
        labels = data.get("labels", [])

        # Reconstruct colormap
        colormap_data = {}
        for idx_str, color_list in data.get("colormap", {}).items():
            idx = int(idx_str)
            colormap_data[idx] = RgbColor(*color_list)

        colormap = Colormap(data=colormap_data)
        return cls(labels=labels, colormap=colormap)

    @classmethod
    def generate(
        cls,
        size: int = 255,
        include_background: bool = True,
        labels: list[str] | None = None,
    ) -> MaskCategories:
        """
        Generates MaskCategories with the specified size.

        Args:
            size: The number of colors to generate in the colormap.
            include_background: If True, the result will include the item
                "0: (0, 0, 0)", which is typically used as a background color.
            labels: Optional list of label names to associate with the mask categories.

        Returns:
            A MaskCategories instance with the generated colormap and optional labels.
        """
        # TODO: Refactor generate_colormap to return a Colormap.
        colormap_dict = generate_colormap(size, include_background=include_background)
        colormap_data = {}
        for index, color in colormap_dict.items():
            colormap_data[index] = RgbColor(*(int(x) for x in color)) if isinstance(color, tuple) else color

        colormap = Colormap(data=colormap_data)
        return cls(labels=labels if labels is not None else [], colormap=colormap)

    def __getitem__(self, idx: int) -> RgbColor:
        return self.colormap[idx]

    def __iter__(self):
        colormap_data = self.colormap.data if isinstance(self.colormap, Colormap) else self.colormap
        return iter(colormap_data.values())

    def __len__(self) -> int:
        return len(self.colormap)

    def __hash__(self):
        colormap_data = self.colormap.data if isinstance(self.colormap, Colormap) else self.colormap
        return hash((tuple(self.labels), frozenset(colormap_data.items())))


@dataclass(frozen=True)
class KeypointCategories(Categories):
    """
    Represents the set of keypoint names for a keypoint detection dataset.

    Each entry in ``labels`` corresponds to a single keypoint (e.g.
    ``("nose", "left_eye", ...)`` for the 17 COCO person keypoints).

    Attributes:
        labels: Ordered tuple of keypoint names.
    """

    labels: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if isinstance(self.labels, list):
            object.__setattr__(self, "labels", tuple(self.labels))
        elif not isinstance(self.labels, tuple):
            raise TypeError("labels must be a list or tuple of strings")

        # Ensure that keypoint labels are unique to keep index->name mapping unambiguous
        seen: set[str] = set()
        duplicates: set[str] = set()
        for name in self.labels:
            if name in seen:
                duplicates.add(name)
            else:
                seen.add(name)

        if duplicates:
            raise ValueError(f"Duplicate keypoint labels found: {sorted(duplicates)}")

    def __getitem__(self, idx: int) -> str:
        return self.labels[idx]

    def __contains__(self, value: int | str) -> bool:
        if isinstance(value, str):
            return value in self.labels
        return 0 <= value < len(self.labels)

    def __len__(self) -> int:
        return len(self.labels)

    def __iter__(self) -> Iterator[str]:
        return iter(self.labels)

    def __hash__(self):
        return hash(self.labels)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "type": "KeypointCategories",
            "labels": list(self.labels),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KeypointCategories:
        """Deserialize from a JSON dictionary."""
        return cls(labels=tuple(data["labels"]))
