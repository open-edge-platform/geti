# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest

from getidata.categories import (
    Colormap,
    GroupType,
    HierarchicalLabelCategories,
    HierarchicalLabelCategory,
    KeypointCategories,
    LabelCategories,
    LabelGroup,
    MaskCategories,
    RgbColor,
)


def test_group_type_to_str():
    assert GroupType.EXCLUSIVE.to_str() == "exclusive"
    assert GroupType.INCLUSIVE.to_str() == "inclusive"


def test_group_type_from_str():
    assert GroupType.from_str("exclusive") == GroupType.EXCLUSIVE
    assert GroupType.from_str("INCLUSIVE") == GroupType.INCLUSIVE


def test_group_type_from_str_invalid():
    with pytest.raises(ValueError, match="Invalid GroupType: invalid"):
        GroupType.from_str("invalid")


def test_label_categories_empty_creation():
    categories = LabelCategories()
    assert len(categories) == 0
    assert list(categories) == []


def test_label_categories_add_label():
    categories = LabelCategories(labels=("person",))
    assert len(categories) == 1
    assert "person" in categories
    assert categories[0] == "person"


def test_label_categories_add_duplicate_name_raises_error():
    with pytest.raises(ValueError):
        LabelCategories(labels=("person", "person"))


def test_label_categories_find_existing_category():
    categories = LabelCategories(labels=("person",))

    index, category = categories.find("person")
    assert index == 0
    assert category == "person"


def test_label_categories_find_nonexistent_category():
    categories = LabelCategories(labels=())

    index, category = categories.find("nonexistent")
    assert index is None
    assert category is None


def test_label_categories_contains_by_name():
    categories = LabelCategories(labels=("person",))

    assert "person" in categories
    assert "nonexistent" not in categories


def test_label_categories_contains_by_index():
    categories = LabelCategories(labels=("person",))

    assert 0 in categories
    assert 1 not in categories
    assert -1 not in categories


def test_label_categories():
    categories = LabelCategories(labels=("person", "car", "bicycle"))

    assert len(categories) == 3
    assert "person" in categories
    assert "car" in categories
    assert "bicycle" in categories


def test_label_categories_iteration():
    categories = LabelCategories(labels=("person", "car"))

    names = [cat for cat in categories]
    assert names == ["person", "car"]


def test_mask_categories_empty_creation():
    categories = MaskCategories()
    assert len(categories.colormap) == 0


def test_mask_categories_manual_colormap():
    colormap = Colormap(data={0: RgbColor(0, 0, 0), 1: RgbColor(255, 0, 0), 2: RgbColor(0, 255, 0)})

    categories = MaskCategories(colormap=colormap)

    assert len(categories.colormap) == 3
    assert categories.colormap[0] == RgbColor(0, 0, 0)
    assert categories.colormap[1] == RgbColor(255, 0, 0)
    assert categories.colormap[2] == RgbColor(0, 255, 0)


def test_mask_categories_immutability():
    categories = MaskCategories(colormap=Colormap(data={0: RgbColor(255, 255, 255)}))

    assert categories.colormap[0] == RgbColor(255, 255, 255)
    assert 0 in categories.colormap

    # Test immutability
    with pytest.raises(Exception):
        categories.colormap[1] = RgbColor(0, 0, 0)


def test_mask_categories_inverse_colormap():
    colormap = Colormap(data={0: RgbColor(0, 0, 0), 1: RgbColor(255, 0, 0)})

    categories = MaskCategories(colormap=colormap)

    inverse = categories.colormap.inverse_colormap
    assert inverse[RgbColor(0, 0, 0)] == 0
    assert inverse[RgbColor(255, 0, 0)] == 1


def test_mask_categories_inverse_colormap_caching():
    categories = MaskCategories(colormap=Colormap(data={0: RgbColor(255, 255, 255), 1: RgbColor(0, 0, 0)}))

    # Access inverse colormap multiple times - should use cache
    inverse1 = categories.colormap.inverse_colormap
    inverse2 = categories.colormap.inverse_colormap

    assert len(inverse1) == 2
    assert inverse1[RgbColor(255, 255, 255)] == 0
    assert inverse1[RgbColor(0, 0, 0)] == 1
    assert inverse1 is inverse2  # Should return same cached object


def test_mask_categories_iteration():
    colormap = Colormap(data={0: RgbColor(0, 0, 0), 1: RgbColor(255, 0, 0)})

    categories = MaskCategories(colormap=colormap)

    items = list(categories.colormap)
    assert items == [(0, RgbColor(0, 0, 0)), (1, RgbColor(255, 0, 0))]


# HierarchicalLabelCategory Tests
def test_hierarchical_label_category_empty_name_raises_error():
    """Test that empty name raises ValueError."""
    with pytest.raises(ValueError, match="Label name cannot be empty"):
        HierarchicalLabelCategory(name="")


def test_hierarchical_label_category_hash():
    """Test that categories with same attributes have same hash."""
    cat1 = HierarchicalLabelCategory(name="person", parent="human", label_semantics={"type": "living"})
    cat2 = HierarchicalLabelCategory(name="person", parent="human", label_semantics={"type": "living"})
    cat3 = HierarchicalLabelCategory(name="person", parent="", label_semantics={"type": "living"})

    assert hash(cat1) == hash(cat2)
    assert hash(cat1) != hash(cat3)


# LabelGroup Tests
def test_label_group_empty_name_raises_error():
    """Test that empty name raises ValueError."""
    with pytest.raises(ValueError, match="Label group name cannot be empty"):
        LabelGroup(name="", labels=("a", "b"))


# HierarchicalLabelCategories Tests
def test_hierarchical_label_categories_empty_creation():
    """Test creation of empty hierarchical categories."""
    categories = HierarchicalLabelCategories()
    assert len(categories) == 0
    assert list(categories) == []
    assert categories.labels == ()


def test_hierarchical_label_categories_basic_creation():
    """Test creation with basic items."""
    items = (
        HierarchicalLabelCategory("animal"),
        HierarchicalLabelCategory("dog", parent="animal"),
        HierarchicalLabelCategory("cat", parent="animal"),
    )
    categories = HierarchicalLabelCategories(items=items)

    assert len(categories) == 3
    assert categories.labels == ("animal", "dog", "cat")
    assert "dog" in categories
    assert "cat" in categories


def test_hierarchical_label_categories_duplicate_names_raises_error():
    """Test that duplicate names raise ValueError."""
    items = (
        HierarchicalLabelCategory("duplicate"),
        HierarchicalLabelCategory("duplicate"),
    )
    with pytest.raises(ValueError, match="Duplicate label name: duplicate"):
        HierarchicalLabelCategories(items=items)


def test_hierarchical_label_categories_invalid_parent_raises_error():
    """Test that invalid parent raises ValueError."""
    items = (HierarchicalLabelCategory("child", parent="nonexistent"),)
    with pytest.raises(ValueError, match="Parent 'nonexistent' not found for label 'child'"):
        HierarchicalLabelCategories(items=items)


def test_hierarchical_label_categories_invalid_group_label_raises_error():
    """Test that invalid group label raises ValueError."""
    items = (HierarchicalLabelCategory("existing"),)
    groups = (LabelGroup("test_group", labels=("nonexistent",)),)

    with pytest.raises(ValueError, match="Label 'nonexistent' in group 'test_group' not found in items"):
        HierarchicalLabelCategories(items=items, label_groups=groups)


def test_hierarchical_label_categories_get_children():
    """Test getting children of a parent label."""
    items = (
        HierarchicalLabelCategory("animal"),
        HierarchicalLabelCategory("dog", parent="animal"),
        HierarchicalLabelCategory("cat", parent="animal"),
        HierarchicalLabelCategory("bird"),
    )
    categories = HierarchicalLabelCategories(items=items)

    children = categories.get_children("animal")
    assert set(children) == {"dog", "cat"}

    # Test label with no children
    children = categories.get_children("bird")
    assert children == ()

    # Test non-existing label
    children = categories.get_children("nonexistent")
    assert children == ()


def test_hierarchical_label_categories_get_parent():
    """Test getting parent of a label."""
    items = (
        HierarchicalLabelCategory("animal"),
        HierarchicalLabelCategory("dog", parent="animal"),
    )
    categories = HierarchicalLabelCategories(items=items)

    # Test label with parent
    parent = categories.get_parent("dog")
    assert parent == "animal"

    # Test root label
    parent = categories.get_parent("animal")
    assert parent == ""

    # Test non-existing label
    parent = categories.get_parent("nonexistent")
    assert parent is None


def test_hierarchical_label_categories_get_hierarchy_level():
    """Test getting hierarchy level of labels."""
    items = (
        HierarchicalLabelCategory("root"),
        HierarchicalLabelCategory("level1", parent="root"),
        HierarchicalLabelCategory("level2", parent="level1"),
    )
    categories = HierarchicalLabelCategories(items=items)

    assert categories.get_hierarchy_level("root") == 0
    assert categories.get_hierarchy_level("level1") == 1
    assert categories.get_hierarchy_level("level2") == 2


def test_hierarchical_label_categories_indexing():
    """Test indexing and contains operations."""
    items = (
        HierarchicalLabelCategory("first"),
        HierarchicalLabelCategory("second"),
    )
    categories = HierarchicalLabelCategories(items=items)

    # Test indexing
    assert categories[0].name == "first"
    assert categories[1].name == "second"

    # Test contains by name
    assert "first" in categories
    assert "second" in categories
    assert "nonexistent" not in categories

    # Test contains by index
    assert 0 in categories
    assert 1 in categories
    assert 2 not in categories
    assert -1 not in categories


def test_hierarchical_label_categories_iteration():
    """Test iteration over categories."""
    items = (
        HierarchicalLabelCategory("first"),
        HierarchicalLabelCategory("second"),
    )
    categories = HierarchicalLabelCategories(items=items)

    names = [cat.name for cat in categories]
    assert names == ["first", "second"]


def test_hierarchical_label_categories_hash():
    """Test hashing of hierarchical categories."""
    items = (HierarchicalLabelCategory("test"),)
    groups = (LabelGroup("group1", labels=("test",)),)

    cat1 = HierarchicalLabelCategories(items=items, label_groups=groups)
    cat2 = HierarchicalLabelCategories(items=items, label_groups=groups)
    cat3 = HierarchicalLabelCategories(items=items)

    assert hash(cat1) == hash(cat2)
    assert hash(cat1) != hash(cat3)


# ==================== Serialization Tests ====================


def test_label_categories_serialization_simple():
    """Test LabelCategories to_dict/from_dict serialization."""
    categories = LabelCategories(labels=("cat", "dog", "bird"))

    # Serialize to dict
    cat_dict = categories.to_dict()
    assert cat_dict["type"] == "LabelCategories"
    assert cat_dict["labels"] == ["cat", "dog", "bird"]
    assert cat_dict["group_type"] == "EXCLUSIVE"

    # Deserialize from dict
    from getidata.categories import Categories

    reconstructed = Categories.from_dict(cat_dict)
    assert isinstance(reconstructed, LabelCategories)

    # Compare with original
    assert reconstructed.labels == categories.labels
    assert reconstructed.group_type == categories.group_type
    assert reconstructed.labels == ("cat", "dog", "bird")


def test_label_categories_serialization_with_group_type():
    """Test LabelCategories serialization with different group types."""
    categories = LabelCategories(labels=("tag1", "tag2", "tag3"), group_type=GroupType.INCLUSIVE)

    # Serialize to dict
    cat_dict = categories.to_dict()
    assert cat_dict["group_type"] == "INCLUSIVE"

    # Deserialize from dict
    from getidata.categories import Categories

    reconstructed = Categories.from_dict(cat_dict)
    assert isinstance(reconstructed, LabelCategories)

    # Compare with original
    assert reconstructed.group_type == categories.group_type
    assert reconstructed.labels == categories.labels


def test_label_categories_serialization_with_semantics():
    """Test LabelCategories serialization with label semantics."""
    from getidata.categories import LabelSemantic

    categories = LabelCategories(
        labels=("normal", "anomaly"),
        label_semantics={LabelSemantic.NORMAL: "normal", LabelSemantic.ANOMALOUS: "anomaly"},
    )

    # Serialize to dict
    cat_dict = categories.to_dict()
    assert cat_dict["label_semantics"]["NORMAL"] == "normal"
    assert cat_dict["label_semantics"]["ANOMALOUS"] == "anomaly"

    # Deserialize from dict
    from getidata.categories import Categories, LabelSemantic

    reconstructed = Categories.from_dict(cat_dict)
    assert isinstance(reconstructed, LabelCategories)

    # Compare with original
    assert reconstructed.label_semantics == categories.label_semantics
    assert reconstructed.label_semantics[LabelSemantic.NORMAL] == "normal"
    assert reconstructed.label_semantics[LabelSemantic.ANOMALOUS] == "anomaly"


def test_hierarchical_label_categories_serialization_simple():
    """Test HierarchicalLabelCategories to_dict/from_dict serialization."""
    items = (
        HierarchicalLabelCategory("animal"),
        HierarchicalLabelCategory("cat", parent="animal"),
        HierarchicalLabelCategory("dog", parent="animal"),
    )
    categories = HierarchicalLabelCategories(items=items)

    # Serialize to dict
    cat_dict = categories.to_dict()
    assert cat_dict["type"] == "HierarchicalLabelCategories"
    assert len(cat_dict["items"]) == 3
    assert cat_dict["items"][0]["name"] == "animal"
    assert cat_dict["items"][0]["parent"] == ""
    assert cat_dict["items"][1]["name"] == "cat"
    assert cat_dict["items"][1]["parent"] == "animal"

    # Deserialize from dict
    from getidata.categories import Categories

    reconstructed = Categories.from_dict(cat_dict)
    assert isinstance(reconstructed, HierarchicalLabelCategories)

    # Compare with original
    assert len(reconstructed.items) == len(categories.items)
    assert reconstructed.items[0].name == categories.items[0].name
    assert reconstructed.items[1].name == categories.items[1].name
    assert reconstructed.items[1].parent == categories.items[1].parent
    assert reconstructed.items[2].parent == categories.items[2].parent


def test_hierarchical_label_categories_serialization_with_groups():
    """Test HierarchicalLabelCategories serialization with label groups."""
    items = (
        HierarchicalLabelCategory("red"),
        HierarchicalLabelCategory("green"),
        HierarchicalLabelCategory("blue"),
    )
    groups = (LabelGroup("colors", labels=("red", "green", "blue"), group_type=GroupType.EXCLUSIVE),)
    categories = HierarchicalLabelCategories(items=items, label_groups=groups)

    # Serialize to dict
    cat_dict = categories.to_dict()
    assert len(cat_dict["label_groups"]) == 1
    assert cat_dict["label_groups"][0]["name"] == "colors"
    assert cat_dict["label_groups"][0]["labels"] == ["red", "green", "blue"]
    assert cat_dict["label_groups"][0]["group_type"] == "EXCLUSIVE"

    # Deserialize from dict
    from getidata.categories import Categories

    reconstructed = Categories.from_dict(cat_dict)
    assert isinstance(reconstructed, HierarchicalLabelCategories)

    # Compare with original
    assert len(reconstructed.label_groups) == len(categories.label_groups)
    assert reconstructed.label_groups[0].name == categories.label_groups[0].name
    assert reconstructed.label_groups[0].labels == categories.label_groups[0].labels
    assert reconstructed.label_groups[0].group_type == categories.label_groups[0].group_type


def test_hierarchical_label_categories_serialization_with_semantics():
    """Test HierarchicalLabelCategories serialization with label semantics."""
    from getidata.categories import LabelSemantic

    items = (
        HierarchicalLabelCategory("normal", label_semantics={LabelSemantic.NORMAL: "normal_class"}),
        HierarchicalLabelCategory("defect", label_semantics={LabelSemantic.ANOMALOUS: "defect_class"}),
    )
    categories = HierarchicalLabelCategories(items=items, label_semantics={LabelSemantic.NORMAL: "normal"})

    # Serialize to dict
    cat_dict = categories.to_dict()
    assert cat_dict["items"][0]["label_semantics"]["NORMAL"] == "normal_class"
    assert cat_dict["items"][1]["label_semantics"]["ANOMALOUS"] == "defect_class"
    assert cat_dict["label_semantics"]["NORMAL"] == "normal"

    # Deserialize from dict
    from getidata.categories import Categories, LabelSemantic

    reconstructed = Categories.from_dict(cat_dict)
    assert isinstance(reconstructed, HierarchicalLabelCategories)

    # Compare with original
    assert reconstructed.items[0].label_semantics == categories.items[0].label_semantics
    assert reconstructed.items[1].label_semantics == categories.items[1].label_semantics
    assert reconstructed.label_semantics == categories.label_semantics
    assert reconstructed.items[0].label_semantics[LabelSemantic.NORMAL] == "normal_class"
    assert reconstructed.label_semantics[LabelSemantic.NORMAL] == "normal"


def test_mask_categories_serialization_empty():
    """Test MaskCategories to_dict/from_dict serialization with empty colormap."""
    categories = MaskCategories()

    # Serialize to dict
    cat_dict = categories.to_dict()
    assert cat_dict["type"] == "MaskCategories"
    assert cat_dict["labels"] == []
    assert cat_dict["colormap"] == {}

    # Deserialize from dict
    from getidata.categories import Categories

    reconstructed = Categories.from_dict(cat_dict)
    assert isinstance(reconstructed, MaskCategories)

    # Compare with original
    assert len(reconstructed.labels) == len(categories.labels)
    assert len(reconstructed.colormap) == len(categories.colormap)


def test_mask_categories_serialization_with_colormap():
    """Test MaskCategories serialization with colormap."""
    colormap_data = {
        0: RgbColor(0, 0, 0),
        1: RgbColor(255, 0, 0),
        2: RgbColor(0, 255, 0),
        3: RgbColor(0, 0, 255),
    }
    categories = MaskCategories(labels=["background", "cat", "dog", "bird"], colormap=Colormap(data=colormap_data))

    # Serialize to dict
    cat_dict = categories.to_dict()
    assert cat_dict["type"] == "MaskCategories"
    assert cat_dict["labels"] == ["background", "cat", "dog", "bird"]
    assert cat_dict["colormap"]["0"] == [0, 0, 0]
    assert cat_dict["colormap"]["1"] == [255, 0, 0]
    assert cat_dict["colormap"]["2"] == [0, 255, 0]
    assert cat_dict["colormap"]["3"] == [0, 0, 255]

    # Deserialize from dict
    from getidata.categories import Categories

    reconstructed = Categories.from_dict(cat_dict)
    assert isinstance(reconstructed, MaskCategories)

    # Compare with original
    assert reconstructed.labels == categories.labels
    assert reconstructed.colormap[0] == categories.colormap[0]
    assert reconstructed.colormap[1] == categories.colormap[1]
    assert reconstructed.colormap[2] == categories.colormap[2]
    assert reconstructed.colormap[3] == categories.colormap[3]


def test_mask_categories_serialization_generated():
    """Test MaskCategories serialization with generated colormap."""
    categories = MaskCategories.generate(size=10, include_background=True)

    # Serialize to dict
    cat_dict = categories.to_dict()
    assert cat_dict["type"] == "MaskCategories"
    assert len(cat_dict["colormap"]) > 0

    # Deserialize from dict
    from getidata.categories import Categories

    reconstructed = Categories.from_dict(cat_dict)
    assert isinstance(reconstructed, MaskCategories)

    # Compare with original
    assert len(reconstructed.colormap) == len(categories.colormap)
    # Verify colormap preserved
    for idx, color in categories.colormap:
        assert reconstructed.colormap[idx] == color


def test_categories_polymorphic_deserialization():
    """Test that Categories.from_dict dispatches to correct subclass."""
    from getidata.categories import Categories

    # Test LabelCategories
    label_dict = {
        "type": "LabelCategories",
        "labels": ["a", "b"],
        "group_type": "EXCLUSIVE",
        "label_semantics": {},
    }
    result = Categories.from_dict(label_dict)
    assert isinstance(result, LabelCategories)

    # Test HierarchicalLabelCategories
    hier_dict = {
        "type": "HierarchicalLabelCategories",
        "items": [{"name": "test", "parent": "", "label_semantics": {}}],
        "label_groups": [],
        "label_semantics": {},
    }
    result = Categories.from_dict(hier_dict)
    assert isinstance(result, HierarchicalLabelCategories)

    # Test MaskCategories
    mask_dict = {"type": "MaskCategories", "labels": [], "colormap": {}}
    result = Categories.from_dict(mask_dict)
    assert isinstance(result, MaskCategories)


def test_categories_unknown_type_raises_error():
    """Test that unknown category type raises ValueError."""
    from getidata.categories import Categories

    unknown_dict = {"type": "UnknownCategoryType"}
    with pytest.raises(ValueError, match="Unknown categories type"):
        Categories.from_dict(unknown_dict)


def test_colormap_serialization_round_trip():
    """Test that colormap serialization preserves inverse colormap."""
    colormap_data = {
        0: RgbColor(255, 0, 0),
        1: RgbColor(0, 255, 0),
        2: RgbColor(0, 0, 255),
    }
    original_colormap = Colormap(data=colormap_data)

    # Create categories with colormap
    categories = MaskCategories(colormap=original_colormap)

    # Serialize and deserialize
    cat_dict = categories.to_dict()
    from getidata.categories import Categories

    reconstructed_cats = Categories.from_dict(cat_dict)

    # Compare with original
    assert isinstance(reconstructed_cats, MaskCategories)
    assert reconstructed_cats.colormap[0] == categories.colormap[0]
    assert reconstructed_cats.colormap[1] == categories.colormap[1]
    assert reconstructed_cats.colormap[2] == categories.colormap[2]
    # Verify both forward and inverse colormap work
    assert reconstructed_cats.colormap.inverse_colormap[RgbColor(255, 0, 0)] == 0
    assert reconstructed_cats.colormap.inverse_colormap[RgbColor(0, 255, 0)] == 1
    assert reconstructed_cats.colormap.inverse_colormap[RgbColor(0, 0, 255)] == 2


# ==================== KeypointCategories Tests ====================


def test_keypoint_categories_empty_creation():
    categories = KeypointCategories()
    assert len(categories) == 0
    assert list(categories) == []


def test_keypoint_categories_creation_with_labels():
    categories = KeypointCategories(labels=("nose", "left_eye", "right_eye"))
    assert len(categories) == 3
    assert categories[0] == "nose"
    assert categories[1] == "left_eye"
    assert categories[2] == "right_eye"


def test_keypoint_categories_list_coerced_to_tuple():
    categories = KeypointCategories(labels=["nose", "left_eye"])
    assert isinstance(categories.labels, tuple)
    assert categories.labels == ("nose", "left_eye")


def test_keypoint_categories_invalid_type_raises_error():
    with pytest.raises(TypeError, match="labels must be a list or tuple of strings"):
        KeypointCategories(labels="not_a_tuple")


def test_keypoint_categories_contains_by_name():
    categories = KeypointCategories(labels=("nose", "left_eye"))
    assert "nose" in categories
    assert "left_eye" in categories
    assert "right_eye" not in categories


def test_keypoint_categories_contains_by_index():
    categories = KeypointCategories(labels=("nose", "left_eye"))
    assert 0 in categories
    assert 1 in categories
    assert 2 not in categories
    assert -1 not in categories


def test_keypoint_categories_iteration():
    categories = KeypointCategories(labels=("nose", "left_eye", "right_eye"))
    names = list(categories)
    assert names == ["nose", "left_eye", "right_eye"]


def test_keypoint_categories_hash():
    cat1 = KeypointCategories(labels=("nose", "left_eye"))
    cat2 = KeypointCategories(labels=("nose", "left_eye"))
    cat3 = KeypointCategories(labels=("nose", "right_eye"))

    assert hash(cat1) == hash(cat2)
    assert hash(cat1) != hash(cat3)


def test_keypoint_categories_serialization():
    """Test KeypointCategories to_dict/from_dict round-trip."""
    categories = KeypointCategories(labels=("nose", "left_eye", "right_eye"))

    cat_dict = categories.to_dict()
    assert cat_dict["type"] == "KeypointCategories"
    assert cat_dict["labels"] == ["nose", "left_eye", "right_eye"]

    from getidata.categories import Categories

    reconstructed = Categories.from_dict(cat_dict)
    assert isinstance(reconstructed, KeypointCategories)
    assert reconstructed.labels == categories.labels


def test_keypoint_categories_serialization_empty():
    """Test KeypointCategories serialization with empty labels."""
    categories = KeypointCategories()

    cat_dict = categories.to_dict()
    assert cat_dict["type"] == "KeypointCategories"
    assert cat_dict["labels"] == []

    from getidata.categories import Categories

    reconstructed = Categories.from_dict(cat_dict)
    assert isinstance(reconstructed, KeypointCategories)
    assert len(reconstructed) == 0


def test_keypoint_categories_polymorphic_deserialization():
    """Test that Categories.from_dict correctly dispatches to KeypointCategories."""
    from getidata.categories import Categories

    kp_dict = {
        "type": "KeypointCategories",
        "labels": ["ankle", "knee", "hip"],
    }
    result = Categories.from_dict(kp_dict)
    assert isinstance(result, KeypointCategories)
    assert result.labels == ("ankle", "knee", "hip")
