"""This module tests classes related to LabelSchema"""

# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

from unittest.mock import patch

import pytest
from networkx.classes.reportviews import NodeView, OutMultiEdgeDataView

from sc_sdk.entities.color import Color
from sc_sdk.entities.label import Domain, Label
from sc_sdk.entities.label_schema import (
    LabelGroup,
    LabelGroupDoesNotExistException,
    LabelGroupExistsException,
    LabelGroupType,
    LabelSchema,
    LabelSchemaView,
    LabelTree,
    NullLabelSchema,
    natural_sort_label_id,
)
from sc_sdk.entities.scored_label import ScoredLabel
from sc_sdk.repos import LabelSchemaRepo

from geti_types import ID


def get_label_entity(id_val: str):
    return Label(name=id_val, domain=Domain.DETECTION, id_=ID(id_val))


def get_scored_label(id_val: str):
    return ScoredLabel(label_id=get_label_entity(id_val).id_, is_empty=get_label_entity(id_val).is_empty)


@pytest.mark.parametrize("id_val", ["3", "fake1name2"])
@pytest.mark.parametrize("target_class", [ID, get_label_entity, get_scored_label])
def test_natural_sort_label_id(id_val: str, target_class):
    target = target_class(id_val)

    if id_val.isdecimal():
        assert natural_sort_label_id(target) == ["", int(id_val)]
    else:
        assert natural_sort_label_id(target) == [id_val]


@pytest.mark.ScSdkComponent
class TestLabelSchemaEntity:
    def test_label_tree(self, label_schema_example):
        """
        <b>Description:</b>
        Check that childs and parents of Labels can be found correctly

        <b>Input data:</b>
        A simple LabelTree

        <b>Expected results:</b>
        Test passes if the correct parent and child labels can be found

        <b>Steps</b>
        1. Create LabelTree
        2. Find parents of Labels
        3. Find children of Label
        """
        threat = label_schema_example.new_label_by_name("threat")
        benign = label_schema_example.new_label_by_name("benign")
        gun = label_schema_example.new_label_by_name("gun")
        rifle = label_schema_example.new_label_by_name("rifle")
        bottle = label_schema_example.new_label_by_name("bottle")

        label_tree = LabelTree()
        label_tree.add_child(threat, gun)
        label_tree.add_child(threat, rifle)
        label_tree.add_child(benign, bottle)

        assert label_tree.get_parent(gun) == threat
        assert label_tree.get_parent(rifle) == threat
        assert label_tree.get_parent(bottle) == benign
        assert label_tree.get_parent(threat) is None

        threat_children = label_tree.get_children(threat)
        assert rifle in threat_children

    def test_add_label_to_group(self, label_schema_example):
        """
        <b>Description:</b>
        Check that new labels can be added to groups

        <b>Input data:</b>
        Empty Label Tree

        <b>Expected results:</b>
        Test passes if an exclusive group can be added to the LabelTree
        as long as a group with the same name does not exist and new labels can be added to a group.

        <b>Steps</b>
        1. Create LabelRelation
        2. Create new label and add to exclusive group
        3. Create new label and attemp to create new group with the same name
        4. Add label to group by group name
        """
        label_schema = LabelSchema(id_=ID())
        bee = label_schema_example.new_label_by_name("bee")  # indicates presence/absence of bee
        bee_state = LabelGroup("bee_state", [bee], LabelGroupType.EXCLUSIVE)
        label_schema.add_group(bee_state)

        # Try to add an extra bee property as a new exclusive label group, but with the same name
        # as an already existing label group
        flying = label_schema_example.new_label_by_name("flying")
        with pytest.raises(ValueError):
            label_schema.add_group(LabelGroup("bee_state", [flying], LabelGroupType.EXCLUSIVE))

        label_schema.add_labels_to_group_by_group_name("bee_state", [flying])

        assert "bee_state" == bee_state.name
        assert 2 == len(bee_state.labels)


class Labels:
    def __init__(self):
        self.label_0 = Label(name="Label 0", domain=Domain.CLASSIFICATION, color=Color(25, 200, 166), id_=ID("0"))
        self.label_0_1 = Label(name="Label 0_1", domain=Domain.DETECTION, color=Color(40, 100, 17), id_=ID("0_1"))
        self.label_0_2 = Label(name="Label 0_2", domain=Domain.SEGMENTATION, color=Color(30, 80, 40), id_=ID("0_2"))
        self.label_0_1_3 = Label(
            name="Label_0_1_3", domain=Domain.SEGMENTATION, color=Color(40, 100, 17), id_=ID("0_1_3")
        )
        self.label_0_2_4 = Label(
            name="Label_0_2_4", domain=Domain.SEGMENTATION, color=Color(30, 80, 40), id_=ID("0_2_4")
        )
        self.label_0_2_5 = Label(
            name="Label_0_2_5", domain=Domain.SEGMENTATION, color=Color(30, 80, 40), id_=ID("0_2_5")
        )
        self.non_included_label = Label(
            ID("non_included_label"), name="Label non included to group", domain=Domain.SEGMENTATION
        )


labels = Labels()


@pytest.mark.ScSdkComponent
class TestLabelGroup:
    def test_label_group_initialization(self):
        """
        <b>Description:</b>
        Check LabelGroup class object initialization

        <b>Input data:</b>
        LabelGroup object with specified name, labels, group type and ID parameters

        <b>Expected results:</b>
        Test passes if LabelGroup object id, labels, name and group_type attributes return expected values

        <b>Steps</b>
        1. Check id, labels, name and group_type attributes of LabelGroup object with not specified group_type
        parameter
        2. Check id, labels, name and group_type attributes of LabelGroup object with not specified id parameter
        """
        # Checking attributes of LabelGroup object with specified id and not specified group_type parameters
        no_group_type_label_group = LabelGroup(
            name="Type non-specified specified label group",
            labels=[labels.label_0_1, labels.label_0],
            id=ID("1"),
        )
        assert no_group_type_label_group.id_ == "1"
        # Expected ascending sorting of labels
        assert no_group_type_label_group.labels == [
            labels.label_0,
            labels.label_0_1,
        ]
        assert no_group_type_label_group.name == "Type non-specified specified label group"
        assert no_group_type_label_group.group_type == LabelGroupType.EXCLUSIVE
        assert isinstance(no_group_type_label_group.minimum_label_id, ID)
        assert no_group_type_label_group.minimum_label_id == ID(0)
        # Checking attributes of LabelGroup object with specified group_type and not specified id parameters
        no_id_label_group = LabelGroup(
            name="ID non-specified Label Group",
            labels=[labels.label_0_1, labels.label_0],
            group_type=LabelGroupType.EMPTY_LABEL,
        )
        # Expected randomly generated ID object with 24 characters as "id" attribute
        assert isinstance(no_id_label_group.id_, ID)
        assert len(no_id_label_group.id_) == 24
        # Expected ascending sorting of labels
        assert no_id_label_group.labels == [labels.label_0, labels.label_0_1]
        assert no_id_label_group.name == "ID non-specified Label Group"
        assert no_id_label_group.group_type == LabelGroupType.EMPTY_LABEL
        assert isinstance(no_id_label_group.minimum_label_id, ID)
        assert no_id_label_group.minimum_label_id == "0"

    def test_label_group_remove_label(self):
        """
        <b>Description:</b>
        Check remove_label method of LabelGroup class object

        <b>Input data:</b>
        LabelGroup objects with specified name, labels, group type and id_parameters parameters

        <b>Expected results:</b>
        Test passes if after using remove_label method values of "labels" property, "minimum_label_id" and
        "is_single_label" methods are equal to expected
        """
        label_group = LabelGroup(name="Test Label Group", labels=[labels.label_0, labels.label_0_1])
        assert not label_group.is_single_label()
        # Removing first label in "labels" property and checking values of "labels", "minimum_label_id" and
        # "is_single_label"
        label_group.remove_label(labels.label_0)
        assert label_group.labels == [labels.label_0_1]
        assert label_group.minimum_label_id == "0_1"
        assert label_group.is_single_label()
        # Removing label that not included to LabelGroup object and repeat checks
        label_group.remove_label(labels.non_included_label)
        assert label_group.labels == [labels.label_0_1]
        assert label_group.minimum_label_id == "0_1"
        assert label_group.is_single_label()


class CommonGraphMethods:
    @staticmethod
    def check_graph_non_list_attributes(expected_attributes_dicts: list) -> None:
        for expected_attribute_dict in expected_attributes_dicts:
            assert expected_attribute_dict.get("attribute") == expected_attribute_dict.get("expected_value")

    @staticmethod
    def check_graph_list_attributes(actual_expected_attributes_dicts: list) -> None:
        for expected_attribute_dict in actual_expected_attributes_dicts:
            attribute = expected_attribute_dict.get("attribute")
            assert isinstance(attribute, expected_attribute_dict.get("expected_type"))
            assert list(attribute) == expected_attribute_dict.get("expected_value")


class Edges:
    def __init__(self):
        self.edge_0_to_0_1 = (labels.label_0, labels.label_0_1)
        self.edge_0_to_0_2 = (labels.label_0, labels.label_0_2)
        self.edge_0_1_to_0_2 = (labels.label_0_1, labels.label_0_2)
        self.edge_0_2_to_0 = (labels.label_0_2, labels.label_0)
        self.edge_0_1_to_0_1_3 = (labels.label_0_1, labels.label_0_1_3)
        self.edge_0_2_to_0_2_4 = (labels.label_0_2, labels.label_0_2_4)
        self.edge_0_2_to_0_2_5 = (labels.label_0_2, labels.label_0_2_5)
        self.edge_0_2_4_to_0_2_5 = (labels.label_0_2_4, labels.label_0_2_5)


edges = Edges()


@pytest.mark.ScSdkComponent
class TestLabelTree:
    @staticmethod
    def label_tree_no_children() -> LabelTree:
        label_tree = LabelTree()
        label_tree.add_edges([edges.edge_0_to_0_1, edges.edge_0_to_0_2])
        return label_tree

    @staticmethod
    def label_tree() -> LabelTree:
        label_tree = LabelTree()
        label_tree.get_labels_in_topological_order()
        # Forming Label Tree with children
        for parent, child in [
            edges.edge_0_to_0_1,
            edges.edge_0_to_0_2,
            edges.edge_0_1_to_0_1_3,
            edges.edge_0_2_to_0_2_4,
            edges.edge_0_2_to_0_2_5,
        ]:
            label_tree.add_child(parent, child)
        return label_tree

    @staticmethod
    def check_get_children_method(label_tree) -> None:
        for label, expected in [
            (labels.label_0, [labels.label_0_1, labels.label_0_2]),
            (labels.label_0_1, [labels.label_0_1_3]),
            (labels.label_0_2, [labels.label_0_2_4, labels.label_0_2_5]),
            (labels.label_0_1_3, []),
            (labels.label_0_2_4, []),
            (labels.label_0_2_5, []),
            (Label(id_=ID("not_included"), name="not included", domain=Domain.CLASSIFICATION), []),
        ]:
            assert label_tree.get_children(label) == expected

    @staticmethod
    def check_get_descendants_method(label_tree) -> None:
        for label, expected in [
            (
                labels.label_0,
                [
                    labels.label_0_1,
                    labels.label_0_1_3,
                    labels.label_0_2,
                    labels.label_0_2_4,
                    labels.label_0_2_5,
                ],
            ),
            (labels.label_0_1, [labels.label_0_1_3]),
            (labels.label_0_2, [labels.label_0_2_4, labels.label_0_2_5]),
            (labels.label_0_1_3, []),
            (labels.label_0_2_4, []),
            (labels.label_0_2_5, []),
        ]:
            assert label_tree.get_descendants(label) == expected

    @staticmethod
    def check_get_ancestors_method(label_tree) -> None:
        for label, expected in [
            (labels.label_0, [labels.label_0]),
            (labels.label_0_1, [labels.label_0_1, labels.label_0]),
            (labels.label_0_2, [labels.label_0_2, labels.label_0]),
            (
                labels.label_0_1_3,
                [labels.label_0_1_3, labels.label_0_1, labels.label_0],
            ),
            (
                labels.label_0_2_4,
                [labels.label_0_2_4, labels.label_0_2, labels.label_0],
            ),
            (
                labels.label_0_2_5,
                [labels.label_0_2_5, labels.label_0_2, labels.label_0],
            ),
        ]:
            assert label_tree.get_ancestors(label) == expected

    def test_label_tree_initialization(self):
        """
        <b>Description:</b>
        Check LabelTree class object initialization

        <b>Input data:</b>
        LabelTree object, edges and nodes to add

        <b>Expected results:</b>
        Test passes if LabelTree object "directed", "edges" and "nodes" attributes and "num_labels" and "type"
        properties and value returned by "num_nodes" method are equal expected
        """
        label_tree = LabelTree()
        # Check for initiated non-directed LabelGraph
        CommonGraphMethods().check_graph_non_list_attributes(
            [
                {"attribute": label_tree.directed, "expected_value": True},
                {"attribute": label_tree.num_labels, "expected_value": 0},
                {"attribute": label_tree.num_nodes(), "expected_value": 0},
                {"attribute": label_tree.type, "expected_value": "tree"},
            ]
        )
        # Check for LabelTree with added edges and nodes
        label_tree.add_edges([edges.edge_0_to_0_1, edges.edge_0_to_0_2])
        CommonGraphMethods().check_graph_non_list_attributes(
            [
                {"attribute": label_tree.directed, "expected_value": True},
                {"attribute": label_tree.num_labels, "expected_value": 3},
                {"attribute": label_tree.num_nodes(), "expected_value": 3},
                {"attribute": label_tree.type, "expected_value": "tree"},
            ]
        )
        expected_nodes = [labels.label_0, labels.label_0_1, labels.label_0_2]
        CommonGraphMethods().check_graph_list_attributes(
            [
                {
                    "attribute": label_tree.edges,
                    "expected_type": OutMultiEdgeDataView,
                    "expected_value": [
                        (labels.label_0, labels.label_0_1, 0, {}),
                        (labels.label_0, labels.label_0_2, 0, {}),
                    ],
                },
                {
                    "attribute": label_tree.nodes,
                    "expected_type": NodeView,
                    "expected_value": expected_nodes,
                },
            ]
        )

    def test_label_tree_add_edge(self):
        """
        <b>Description:</b>
        Check LabelTree class add_edge and add_edges methods

        <b>Input data:</b>
        LabelTree object with specified directed parameters and added edges

        <b>Expected results:</b>
        Test passes if "edges" attribute of LabelTree is equal expected value after using add_edge and add_edges methods
        """
        label_tree = self.label_tree_no_children()
        # Adding edges, one of which already in LabelTree
        label_tree.topological_sort()
        label_tree.add_edges([edges.edge_0_to_0_1, edges.edge_0_1_to_0_1_3])
        CommonGraphMethods().check_graph_non_list_attributes(
            [
                {"attribute": label_tree.num_labels, "expected_value": 4},
                {"attribute": label_tree.num_nodes(), "expected_value": 4},
            ]
        )
        CommonGraphMethods().check_graph_list_attributes(
            [
                {
                    "attribute": label_tree.edges,
                    "expected_type": OutMultiEdgeDataView,
                    "expected_value": [
                        (labels.label_0, labels.label_0_1, 0, {}),
                        (labels.label_0, labels.label_0_1, 1, {}),
                        (labels.label_0, labels.label_0_2, 0, {}),
                        (labels.label_0_1, labels.label_0_1_3, 0, {}),
                    ],
                },
                {
                    "attribute": label_tree.nodes,
                    "expected_type": NodeView,
                    "expected_value": [
                        labels.label_0,
                        labels.label_0_1,
                        labels.label_0_2,
                        labels.label_0_1_3,
                    ],
                },
            ]
        )
        assert not label_tree._LabelTree__topological_order_cache
        # Adding one existing and one non-existing edge
        label_tree.topological_sort()
        label_tree.add_edges([edges.edge_0_to_0_2, edges.edge_0_2_to_0_2_4])
        CommonGraphMethods().check_graph_non_list_attributes(
            [
                {"attribute": label_tree.num_labels, "expected_value": 5},
                {"attribute": label_tree.num_nodes(), "expected_value": 5},
            ]
        )
        CommonGraphMethods().check_graph_list_attributes(
            [
                {
                    "attribute": label_tree.edges,
                    "expected_type": OutMultiEdgeDataView,
                    "expected_value": [
                        (labels.label_0, labels.label_0_1, 0, {}),
                        (labels.label_0, labels.label_0_1, 1, {}),
                        (labels.label_0, labels.label_0_2, 0, {}),
                        (labels.label_0, labels.label_0_2, 1, {}),
                        (labels.label_0_1, labels.label_0_1_3, 0, {}),
                        (labels.label_0_2, labels.label_0_2_4, 0, {}),
                    ],
                },
                {
                    "attribute": label_tree.nodes,
                    "expected_type": NodeView,
                    "expected_value": [
                        labels.label_0,
                        labels.label_0_1,
                        labels.label_0_2,
                        labels.label_0_1_3,
                        labels.label_0_2_4,
                    ],
                },
            ]
        )
        assert not label_tree._LabelTree__topological_order_cache

    def test_label_tree_add_node(self):
        """
        <b>Description:</b>
        Check LabelTree class add_node method

        <b>Input data:</b>
        LabelTree object with specified directed parameter and added edges

        <b>Expected results:</b>
        Test passes if "nodes" attribute of LabelTree is equal expected value after using add_node method
        """
        label_tree = self.label_tree_no_children()
        # Adding new node
        label_tree.get_labels_in_topological_order()
        label_tree.add_node(labels.label_0_1_3)
        CommonGraphMethods().check_graph_non_list_attributes(
            [
                {"attribute": label_tree.num_labels, "expected_value": 4},
                {"attribute": label_tree.num_nodes(), "expected_value": 4},
            ]
        )
        expected_edges = [
            (labels.label_0, labels.label_0_1, 0, {}),
            (labels.label_0, labels.label_0_2, 0, {}),
        ]
        expected_nodes = [
            labels.label_0,
            labels.label_0_1,
            labels.label_0_2,
            labels.label_0_1_3,
        ]
        CommonGraphMethods().check_graph_list_attributes(
            [
                {
                    "attribute": label_tree.edges,
                    "expected_type": OutMultiEdgeDataView,
                    "expected_value": expected_edges,
                },
                {
                    "attribute": label_tree.nodes,
                    "expected_type": NodeView,
                    "expected_value": expected_nodes,
                },
            ]
        )
        assert not label_tree._LabelTree__topological_order_cache
        # Adding existing node, only topological_order_cache should be empty
        label_tree.get_labels_in_topological_order()
        label_tree.add_node(labels.label_0)
        CommonGraphMethods().check_graph_non_list_attributes(
            [
                {"attribute": label_tree.num_labels, "expected_value": 4},
                {"attribute": label_tree.num_nodes(), "expected_value": 4},
            ]
        )
        CommonGraphMethods().check_graph_list_attributes(
            [
                {
                    "attribute": label_tree.edges,
                    "expected_type": OutMultiEdgeDataView,
                    "expected_value": expected_edges,
                },
                {
                    "attribute": label_tree.nodes,
                    "expected_type": NodeView,
                    "expected_value": expected_nodes,
                },
            ]
        )
        assert not label_tree._LabelTree__topological_order_cache

    def test_label_tree_clear_topological_cache(self):
        """
        <b>Description:</b>
        Check LabelTree class clear_topological_cache method

        <b>Input data:</b>
        LabelTree object with specified directed parameter and added edges

        <b>Expected results:</b>
        Test passes if "__topological_order_cache" attribute of LabelTree is equal "None" after clear_topological_cache
        """
        # Check for empty LabelTree
        label_tree = LabelTree()
        label_tree.get_labels_in_topological_order()
        label_tree.clear_topological_cache()
        assert not label_tree._LabelTree__topological_order_cache
        # Check for LabelTree with specified nodes and edges
        label_tree = self.label_tree_no_children()
        label_tree.get_labels_in_topological_order()
        label_tree.clear_topological_cache()
        assert not label_tree._LabelTree__topological_order_cache

    def test_label_tree_relations(self):
        """
        <b>Description:</b>
        Check LabelTree class relations methods

        <b>Input data:</b>
        LabelTree object with specified directed parameter, added edges and children

        <b>Expected results:</b>
        Test passes if "get_parent", "get_children", "get_descendants", "get_siblings" and "get_ancestors" methods
        of LabelTree return expected values

        <b>Steps</b>
        1. Check add_children method
        2. Check "get_parent" method
        3. Check "get_descendants" method
        4. Check "get_siblings" method
        5. Check "get_ancestors" method
        """
        label_tree = self.label_tree()
        assert not label_tree._LabelTree__topological_order_cache
        # Checking new nodes and edges added after add_children method
        CommonGraphMethods().check_graph_non_list_attributes(
            [
                {"attribute": label_tree.num_labels, "expected_value": 6},
                {"attribute": label_tree.num_nodes(), "expected_value": 6},
            ]
        )
        CommonGraphMethods().check_graph_list_attributes(
            [
                {
                    "attribute": label_tree.edges,
                    "expected_type": OutMultiEdgeDataView,
                    "expected_value": [
                        (labels.label_0_1, labels.label_0, 0, {"value": None}),
                        (labels.label_0_2, labels.label_0, 0, {"value": None}),
                        (labels.label_0_1_3, labels.label_0_1, 0, {"value": None}),
                        (labels.label_0_2_4, labels.label_0_2, 0, {"value": None}),
                        (labels.label_0_2_5, labels.label_0_2, 0, {"value": None}),
                    ],
                },
                {
                    "attribute": label_tree.nodes,
                    "expected_type": NodeView,
                    "expected_value": [
                        labels.label_0_1,
                        labels.label_0,
                        labels.label_0_2,
                        labels.label_0_1_3,
                        labels.label_0_2_4,
                        labels.label_0_2_5,
                    ],
                },
            ]
        )
        # Checking "get_parent" method
        for label, expected in [
            (labels.label_0, None),
            (labels.label_0_1, labels.label_0),
            (labels.label_0_2, labels.label_0),
            (labels.label_0_1_3, labels.label_0_1),
            (labels.label_0_2_4, labels.label_0_2),
            (labels.label_0_2_5, labels.label_0_2),
        ]:
            assert label_tree.get_parent(label) == expected
        # Checking "get_children" method
        self.check_get_children_method(label_tree)
        # Checking "get_descendants" method
        self.check_get_descendants_method(label_tree)
        # Checking "get_siblings" method
        for label, expected in [
            (labels.label_0, []),
            (labels.label_0_1, [labels.label_0_2]),
            (labels.label_0_2, [labels.label_0_1]),
            (labels.label_0_1_3, []),
            (labels.label_0_2_4, [labels.label_0_2_5]),
            (labels.label_0_2_5, [labels.label_0_2_4]),
        ]:
            assert label_tree.get_siblings(label) == expected
        # Checking "get_ancestors" method
        self.check_get_ancestors_method(label_tree)

    def test_label_tree_get_labels_in_topological_order(self):
        """
        <b>Description:</b>
        Check LabelTree class get_labels_in_topological_order method

        <b>Input data:</b>
        LabelTree object with specified directed parameter, added edges and children

        <b>Expected results:</b>
        Test passes if get_labels_in_topological_order method of LabelTree returns expected value

        <b>Steps</b>
        1. Check value returned by get_labels_in_topological_order method for Tree with multiple children branches
        2. Remove node with children from tree and check value returned by get_labels_in_topological_order method
        """
        label_tree = self.label_tree()
        # Checking value returned by get_labels_in_topological_order method for tree with multiple branches
        labels_topological_order = label_tree.get_labels_in_topological_order()

        def previous_vertexes(vert_id):
            vertexes = vert_id.split("_")
            return vertexes[:-1], vertexes[-1]

        returned_vertexes = set()
        for label in labels_topological_order:
            previous, curent = previous_vertexes(label.id_)
            for vertex in previous:
                assert vertex in returned_vertexes
            returned_vertexes.add(curent)
        assert {"0", "1", "2", "3", "4", "5"} == returned_vertexes

        assert label_tree._LabelTree__topological_order_cache == labels_topological_order
        # Removing node with children and checking value returned by get_labels_in_topological_order method
        label_tree.remove_node(labels.label_0_1)
        labels_topological_order = label_tree.get_labels_in_topological_order()
        returned_vertexes = set()
        for label in labels_topological_order:
            previous, curent = previous_vertexes(label.id_)
            for vertex in previous:
                if curent != "3":  # the '1' has been removed, so that '3' is separated from the rest graph.
                    assert vertex in returned_vertexes
            returned_vertexes.add(curent)
        assert {"0", "2", "3", "4", "5"} == returned_vertexes
        assert label_tree._LabelTree__topological_order_cache == labels_topological_order

    def test_label_tree_remove_node(self):
        """
        <b>Description:</b>
        Check LabelTree class remove_node method

        <b>Input data:</b>
        LabelTree object with specified directed parameter, added edges and children

        <b>Expected results:</b>
        Test passes if after using remove_node method on LabelTree object "edges", "nodes" and "num_labels" properties
        and "num_nodes" method return expected values

        <b>Steps</b>
        1. Check values returned by "edges", "nodes" and "num_labels" properties and "num_nodes" method after removing
        children node
        2. Check values returned by "edges", "nodes" and "num_labels" properties and "num_nodes" method after removing
        parent node
        """
        label_tree = self.label_tree()
        # Removing children node and checking "edges", "nodes" and "num_labels" properties and "num_nodes" method values
        label_tree.remove_node(labels.label_0_1_3)
        assert label_tree.num_nodes() == 5
        assert label_tree.num_labels == 5
        assert not label_tree._LabelTree__topological_order_cache
        CommonGraphMethods().check_graph_list_attributes(
            [
                {
                    "attribute": label_tree.edges,
                    "expected_type": OutMultiEdgeDataView,
                    "expected_value": [
                        (labels.label_0_1, labels.label_0, 0, {"value": None}),
                        (labels.label_0_2, labels.label_0, 0, {"value": None}),
                        (labels.label_0_2_4, labels.label_0_2, 0, {"value": None}),
                        (labels.label_0_2_5, labels.label_0_2, 0, {"value": None}),
                    ],
                },
                {
                    "attribute": label_tree.nodes,
                    "expected_type": NodeView,
                    "expected_value": [
                        labels.label_0_1,
                        labels.label_0,
                        labels.label_0_2,
                        labels.label_0_2_4,
                        labels.label_0_2_5,
                    ],
                },
            ]
        )
        # Removing node with children and checking value returned by get_labels_in_topological_order method
        label_tree.get_labels_in_topological_order()
        label_tree.remove_node(labels.label_0_2)
        assert label_tree.num_nodes() == 4
        assert label_tree.num_labels == 4
        assert not label_tree._LabelTree__topological_order_cache
        expected_edges = [(labels.label_0_1, labels.label_0, 0, {"value": None})]
        CommonGraphMethods().check_graph_list_attributes(
            [
                {
                    "attribute": label_tree.edges,
                    "expected_type": OutMultiEdgeDataView,
                    "expected_value": expected_edges,
                },
                {
                    "attribute": label_tree.nodes,
                    "expected_type": NodeView,
                    "expected_value": [
                        labels.label_0_1,
                        labels.label_0,
                        labels.label_0_2_4,
                        labels.label_0_2_5,
                    ],
                },
            ]
        )

    def test_label_tree_subgraph(self):
        """
        <b>Description:</b>
        Check LabelTree class subgraph method

        <b>Input data:</b>
        LabelTree object with specified directed parameter, added edges and children

        <b>Expected results:</b>
        Test passes if LabelTree object returned by subgraph method is equal expected
        """
        label_tree = self.label_tree()
        non_included_label = Label(id_=ID("not"), name="not included", domain=Domain.CLASSIFICATION)
        subgraph = label_tree.subgraph(
            [
                labels.label_0,
                labels.label_0_1,
                labels.label_0_2,
                labels.label_0_2_5,
                non_included_label,
            ]
        )
        assert subgraph.num_nodes() == 4
        assert subgraph.num_labels == 4
        CommonGraphMethods().check_graph_list_attributes(
            [
                {
                    "attribute": subgraph.edges,
                    "expected_type": OutMultiEdgeDataView,
                    "expected_value": [
                        (labels.label_0_1, labels.label_0, 0, {"value": None}),
                        (labels.label_0_2, labels.label_0, 0, {"value": None}),
                        (labels.label_0_2_5, labels.label_0_2, 0, {"value": None}),
                    ],
                },
                {
                    "attribute": subgraph.nodes,
                    "expected_type": NodeView,
                    "expected_value": [
                        labels.label_0_1,
                        labels.label_0,
                        labels.label_0_2,
                        labels.label_0_2_5,
                    ],
                },
            ]
        )

    def test_label_tree_eq(self):
        """
        <b>Description:</b>
        Check LabelTree class __eq__ method

        <b>Input data:</b>
        LabelTree objects with specified directed parameter, added edges and children

        <b>Expected results:</b>
        Test passes if value returned by __eq__ method is equal expected

        <b>Steps</b>
        1. Check value returned by __eq__ method for equal LabelTree objects
        2. Check value returned by __eq__ method for LabelTree objects with different edges
        3. Check value returned by __eq__ method for LabelTree objects with different nodes
        4. Check value returned by __eq__ method for comparing LabelTree objects with different type object
        """
        label_tree = self.label_tree()
        # Checking __eq__ method for equal LabelTree objects
        equal_label_tree = self.label_tree()
        assert label_tree == equal_label_tree
        # Checking __eq__ method for LabelTree objects with different edges
        different_edges_tree = self.label_tree()
        different_edges_tree.add_edge(labels.label_0, labels.label_0_1)
        assert not label_tree == different_edges_tree
        # Checking __eq__ method for LabelTree objects with different nodes
        different_nodes_tree = self.label_tree()
        different_nodes_tree.add_node(Label(id_=ID("not_included"), name="not included", domain=Domain.CLASSIFICATION))
        assert label_tree != different_nodes_tree
        # Checking __eq__ method for comparing LabelTree object with different type object
        assert not isinstance(label_tree, str)


@pytest.mark.ScSdkComponent
class TestLabelSchemaGroupEntity:
    @staticmethod
    def label_groups() -> list:
        group_1 = LabelGroup(
            name="Exclusive group 1",
            labels=[labels.label_0_1, labels.label_0_2],
            id=ID("Exclusive group 1"),
        )
        group_2 = LabelGroup(
            name="Exclusive group 2",
            labels=[labels.label_0_2_4, labels.label_0_2_5],
            id=ID("Exclusive group 2"),
        )
        return [group_1, group_2]

    @staticmethod
    def empty_labels() -> list:
        empty_label = Label(
            name="Empty label",
            domain=Domain.SEGMENTATION,
            color=Color(255, 255, 255),
            is_empty=True,
            id_=ID("empty_label_1"),
        )
        empty_non_exclusive_label = Label(
            name="Empty non-exclusive label",
            domain=Domain.DETECTION,
            color=Color(255, 255, 255),
            is_empty=True,
            id_=ID("empty_non_excl_label_1"),
        )
        return [empty_label, empty_non_exclusive_label]

    def empty_labels_groups(self) -> list:
        empty_labels = self.empty_labels()
        empty_group_1 = LabelGroup(
            name="Exclusive group with empty label",
            labels=[empty_labels[0]],
            id=ID("Exclusive group with empty label"),
        )
        empty_group_2 = LabelGroup(
            name="Empty label group with empty label",
            labels=[empty_labels[1]],
            group_type=LabelGroupType.EMPTY_LABEL,
            id=ID("Empty label group with empty label"),
        )
        return [empty_group_1, empty_group_2]

    def label_schema_entity(self) -> LabelSchema:
        return LabelSchema(
            id_=ID(),
            label_tree=TestLabelTree.label_tree(),
            label_groups=self.label_groups() + self.empty_labels_groups(),
        )

    def test_label_schema_entity_get_labels(self):
        """
        <b>Description:</b>
        Check LabelSchema class get_labels method

        <b>Input data:</b>
        LabelSchema object with specified label_tree and label_groups parameters

        <b>Expected results:</b>
        Test passes if list returned by get_labels method is equal expected

        <b>Steps</b>
        1. Check list returned by get_labels method with include_empty parameter set to True
        2. Check list returned by get_labels method with include_empty parameter set to False
        """
        empty_labels = self.empty_labels()
        label_schema_entity = self.label_schema_entity()
        # Checking list returned by get_labels method with include_empty parameter set to True
        assert label_schema_entity.get_labels(include_empty=True) == [
            labels.label_0_1,
            labels.label_0_2,
            labels.label_0_2_4,
            labels.label_0_2_5,
            empty_labels[0],
            empty_labels[1],
        ]
        # Checking list returned by get_labels method with include_empty parameter set to False
        assert label_schema_entity.get_labels(include_empty=False) == [
            labels.label_0_1,
            labels.label_0_2,
            labels.label_0_2_4,
            labels.label_0_2_5,
        ]

    def test_label_schema_entity_get_groups(self):
        """
        <b>Description:</b>
        Check LabelSchema class get_groups method

        <b>Input data:</b>
        LabelSchema object with specified label_tree and label_groups parameters

        <b>Expected results:</b>
        Test passes if list returned by get_groups method is equal expected

        <b>Steps</b>
        1. Check list returned by get_groups method with include_empty parameter set to True
        2. Check list returned by get_groups method with include_empty parameter set to False
        """
        label_groups = self.label_groups()
        empty_label_groups = self.empty_labels_groups()
        label_schema_entity = self.label_schema_entity()
        # Checking list returned by get_groups method with include_empty parameter set to True
        assert label_schema_entity.get_groups(include_empty=True) == [
            label_groups[0],
            label_groups[1],
            empty_label_groups[0],
            empty_label_groups[1],
        ]
        # Checking list returned by get_groups method with include_empty parameter set to False
        assert label_schema_entity.get_groups(include_empty=False) == [
            label_groups[0],
            label_groups[1],
            empty_label_groups[0],
        ]

    def test_label_schema_entity_add_group(self):
        """
        <b>Description:</b>
        Check LabelSchema class add_group method

        <b>Input data:</b>
        LabelSchema object with label_tree and label_groups parameters

        <b>Expected results:</b>
        Test passes if value returned by "get_exclusive_groups" method is equal expected

        <b>Steps</b>
        1. Check value returned by "get_exclusive_groups" method after adding group with new labels
        2. Check value returned by "get_exclusive_groups" method after adding group with single label
        3. Check value returned by "get_exclusive_groups" method after adding group with already added label
        4. Check value returned by "get_exclusive_groups" method and exclusivity of labels after adding group exclusive
        to other
        5. Check value returned by "get_exclusive_groups" method after adding non-exclusive group
        6. Check LabelGroupExistsException raised when adding LabelGroup with already existing name
        """
        empty_label_groups = self.empty_labels_groups()
        exclusive_groups = self.label_groups() + [empty_label_groups[0]]
        label_schema_entity = self.label_schema_entity()
        # Scenario for adding exclusive group with new labels
        new_exclusive_label = Label(name="New label", domain=Domain.DETECTION, id_=ID("new_ex_1"))
        other_new_exclusive_label = Label(name="Other new label", domain=Domain.DETECTION, id_=ID("new_ex_2"))
        new_exclusive_group = LabelGroup(
            name="New exclusive labels group",
            labels=[new_exclusive_label, other_new_exclusive_label],
            id=ID("new_ex_group"),
        )
        label_schema_entity.add_group(new_exclusive_group)
        assert label_schema_entity.get_exclusive_groups() == (exclusive_groups + [new_exclusive_group])
        # Scenario for adding exclusive group with single label
        label_schema_entity = self.label_schema_entity()
        new_exclusive_group = LabelGroup(
            name="Exclusive group with one label",
            labels=[new_exclusive_label],
            id=ID("single_excl_group"),
        )
        label_schema_entity.add_group(new_exclusive_group)
        assert label_schema_entity.get_exclusive_groups() == (exclusive_groups + [new_exclusive_group])
        # Scenario for adding exclusive group with one already existing label
        label_schema_entity = self.label_schema_entity()
        new_exclusive_group = LabelGroup(
            name="Exclusive group to link with existing",
            labels=[labels.label_0_1, new_exclusive_label],
            id=ID("new_ex_group"),
        )
        label_schema_entity.add_group(new_exclusive_group)
        assert label_schema_entity.get_exclusive_groups() == (exclusive_groups + [new_exclusive_group])
        # Scenario for adding non-exclusive group
        label_schema_entity = self.label_schema_entity()
        new_exclusive_group = LabelGroup(
            name="Non exclusive label group",
            labels=[new_exclusive_label],
            group_type=LabelGroupType.EMPTY_LABEL,
            id=ID("non_exclusive_group"),
        )
        label_schema_entity.add_group(new_exclusive_group)
        assert label_schema_entity.get_exclusive_groups() == exclusive_groups
        # Raise LabelGroupExistsException when adding LabelGroup with same name
        for group_type in [LabelGroupType.EXCLUSIVE, LabelGroupType.EMPTY_LABEL]:
            with pytest.raises(LabelGroupExistsException):
                label_schema_entity.add_group(
                    LabelGroup(
                        name="Exclusive group 1",
                        labels=[],
                        group_type=group_type,
                    )
                )

    def test_label_schema_add_child(self):
        """
        <b>Description:</b>
        Check LabelSchema class add_child method

        <b>Input data:</b>
        LabelSchema object with specified label_tree and label_groups parameters

        <b>Expected results:</b>
        Test passes if list returned by get_children method after using add_child method are equal to expected

        <b>Steps</b>
        1. Check get_children list after using add_child method
        2. Check get_children list after using add_child method for previous pair for a second time
        """
        label_schema_entity = self.label_schema_entity()
        label_schema_entity.add_child(parent=labels.label_0_2_4, child=labels.label_0_2_5)
        assert label_schema_entity.get_children(labels.label_0_2_4) == [labels.label_0_2_5]
        label_schema_entity.add_child(parent=labels.label_0_2_4, child=labels.label_0_2_5)
        assert label_schema_entity.get_children(labels.label_0_2_4) == [labels.label_0_2_5]

    def test_label_schema_entity_get_label_ids(self):
        """
        <b>Description:</b>
        Check LabelSchema class get_label_ids method

        <b>Input data:</b>
        LabelSchema object with specified label_tree and label_groups parameters

        <b>Expected results:</b>
        Test passes if values returned by get_label_ids method is equal expected

        <b>Steps</b>
        Check value returned by get_label_ids method for LabelSchema object
        """
        expected_non_empty_labels = [ID("0_1"), ID("0_2"), ID("0_2_4"), ID("0_2_5")]
        expected_include_empty_labels = expected_non_empty_labels + [
            ID("empty_label_1"),
            ID("empty_non_excl_label_1"),
        ]
        label_schema_entity = self.label_schema_entity()
        assert label_schema_entity.get_label_ids(include_empty=True) == expected_include_empty_labels
        assert label_schema_entity.get_label_ids(include_empty=False) == expected_non_empty_labels

    def test_label_schema_get_label_group_by_name(self):
        """
        <b>Description:</b>
        Check LabelSchema class get_label_group_by_name method

        <b>Input data:</b>
        LabelSchema object with specified label_tree and label_groups parameters

        <b>Expected results:</b>
        Test passes if value returned by get_label_group_by_name method is equal expected

        <b>Steps</b>
        1. Check get_label_group_by_name method for searching exclusive group
        2. Check get_label_group_by_name method for searching empty label group
        2. Check get_label_group_by_name method for searching non_existing group
        """
        label_schema_entity = self.label_schema_entity()
        label_groups = self.label_groups()
        empty_non_excl_group = self.empty_labels_groups()[1]
        # Checking get_label_group_by_name method for searching exclusive group for not specified empty labels
        assert label_schema_entity.get_label_group_by_name("Exclusive group 1") == label_groups[0]
        # Checking get_label_group_by_name method for searching empty label group with empty label
        assert label_schema_entity.get_label_group_by_name("Empty label group with empty label") == empty_non_excl_group
        # Checking get_label_group_by_name method for searching non-existing group
        assert not label_schema_entity.get_label_group_by_name("Non-existing group")

    def test_label_schema_get_exclusive_groups(self):
        """
        <b>Description:</b>
        Check LabelSchema class get_exclusive_groups method

        <b>Input data:</b>
        LabelSchema object with specified label_tree and label_groups parameters

        <b>Expected results:</b>
        Test passes if value returned by get_exclusive_groups method is equal expected

        <b>Steps</b>
        1. Check get_exclusive_groups method
        2. Check get_exclusive_groups method after adding exclusive group
        3. Check get_exclusive_groups method after adding empty label group
        """
        label_schema_entity = self.label_schema_entity()
        exclusive_groups = self.label_groups() + [self.empty_labels_groups()[0]]
        # Checking get_exclusive_groups method for searching exclusive groups
        assert label_schema_entity.get_exclusive_groups() == exclusive_groups
        # Checking get_exclusive_groups method after adding new exclusive group
        new_label = Label(name="New label", domain=Domain.DETECTION, color=Color(100, 16, 25), id_=ID("new_ex_1"))
        new_labels_group = LabelGroup(
            name="New exclusive labels group",
            labels=[new_label],
            id=ID("new_ex_group"),
        )
        label_schema_entity.add_group(new_labels_group)
        exclusive_groups.append(new_labels_group)
        assert label_schema_entity.get_exclusive_groups() == exclusive_groups
        # Checking get_exclusive_groups method after adding empty label group
        empty_label_group = LabelGroup(
            name="New non-exclusive labels group",
            labels=[new_label],
            group_type=LabelGroupType.EMPTY_LABEL,
            id=ID("new_ex_group"),
        )
        label_schema_entity.add_group(empty_label_group)
        assert label_schema_entity.get_exclusive_groups() == exclusive_groups

    def test_label_schema_add_labels_to_group_by_group_name(self):
        """
        <b>Description:</b>
        Check LabelSchema class add_labels_to_group_by_group_name method

        <b>Input data:</b>
        LabelSchema object with specified label_tree and label_groups parameters

        <b>Expected results:</b>
        Test passes if labels attribute returned by group which specified in add_labels_to_group_by_group_name method
        is equal expected

        <b>Steps</b>
        1. Check add_labels_to_group_by_group_name method to add labels to exclusive group
        2. Check add_labels_to_group_by_group_name method to add labels to empty label group
        3. Check LabelGroupDoesNotExistException raised when adding labels to non-existing group
        """
        label_schema_entity = self.label_schema_entity()
        non_exclusive_label = self.empty_labels()[1]
        # Checking add_labels_to_group_by_group_name method to add labels to exclusive group
        new_label = Label(name="New label", domain=Domain.DETECTION, color=Color(100, 16, 25), id_=ID("new_ex_1"))
        new_empty_label = Label(
            name="New empty label", domain=Domain.DETECTION, color=Color(81, 100, 10), id_=ID("new_ex_2")
        )
        exclusive_group_name = "Exclusive group 1"
        label_schema_entity.add_labels_to_group_by_group_name(
            group_name=exclusive_group_name, labels=[new_label, new_empty_label]
        )
        assert label_schema_entity.get_label_group_by_name(exclusive_group_name).labels == [
            labels.label_0_1,
            labels.label_0_2,
            new_label,
            new_empty_label,
        ]
        # Checking add_labels_to_group_by_group_name method to add labels to non-exclusive group
        new_empty_label = Label(
            name="New non-exclusive empty_label", domain=Domain.SEGMENTATION, is_empty=True, id_=ID("empty_label_1")
        )
        empty_label_group_name = "Empty label group with empty label"
        label_schema_entity.add_labels_to_group_by_group_name(
            group_name=empty_label_group_name, labels=[new_empty_label]
        )
        assert label_schema_entity.get_label_group_by_name(empty_label_group_name).labels == [
            non_exclusive_label,
            new_empty_label,
        ]
        # Checking that LabelGroupDoesNotExistException raised when adding labels to non-existing group
        with pytest.raises(LabelGroupDoesNotExistException):
            label_schema_entity.add_labels_to_group_by_group_name(
                group_name="Non-existing group", labels=[new_empty_label]
            )

    def test_label_schema_relations(self):
        """
        <b>Description:</b>
        Check LabelSchema relations methods

        <b>Input data:</b>
        LabelSchema object with specified label_tree and label_groups parameters

        <b>Expected results:</b>
        Test passes if "get_children", "get_descendants" and "get_ancestors" methods
        of LabelTree return expected values

        <b>Steps</b>
        1. Check "get_children" method
        2. Check "get_descendants" method
        3. Check "get_ancestors" method
        """
        label_schema_entity = self.label_schema_entity()
        # Checking get_children method
        TestLabelTree.check_get_children_method(label_schema_entity)
        # Checking get_descendants method
        TestLabelTree.check_get_descendants_method(label_schema_entity)
        # Checking get_ancestors method
        TestLabelTree.check_get_ancestors_method(label_schema_entity)

    def test_label_schema_get_group_containing_label(self):
        """
        <b>Description:</b>
        Check LabelSchema class get_group_containing_label method

        <b>Input data:</b>
        LabelSchema object with specified label_tree and label_groups parameters

        <b>Expected results:</b>
        Test passes if value returned by get_group_containing_label method is equal expected

        <b>Steps</b>
        1. Check get_group_containing_label method for label included in exclusive group
        2. Check get_group_containing_label method for label included in empty label
        3. Check get_group_containing_label method for label not included in any group
        """
        label_schema_entity = self.label_schema_entity()
        label_groups = self.label_groups()
        # Checking get_group_containing_label method for label included in exclusive group
        assert label_schema_entity.get_group_containing_label(labels.label_0_1) == label_groups[0]
        assert label_schema_entity.get_group_containing_label(labels.label_0_2) == label_groups[0]
        assert label_schema_entity.get_group_containing_label(labels.label_0_2_4) == label_groups[1]
        assert label_schema_entity.get_group_containing_label(labels.label_0_2_5) == label_groups[1]
        # Checking get_group_containing_label method for label included in non-exclusive group
        assert label_schema_entity.get_group_containing_label(self.empty_labels()[1]) == self.empty_labels_groups()[1]
        # Checking get_group_containing_label method for label not included in any group
        assert not label_schema_entity.get_group_containing_label(labels.label_0)
        assert not label_schema_entity.get_group_containing_label(labels.label_0_1_3)


@pytest.mark.ScSdkComponent
class TestLabelSchema:
    def test_labelschema_equality(self, fxt_label_schema_example) -> None:
        """
        <b>Description:</b>
        Check that LabelSchema equality works correctly

        <b>Input data:</b>
        LabelSchema instances

        <b>Expected results:</b>
        == and != operations work correctly for various inputs

        <b>Steps</b>
        1. Test LabelSchema equality
        2. Test NullLabelSchema equality
        """
        label_schema = LabelSchema(id_=ID("test"))

        label_group_name = "Vegetation"
        label_schema.add_group(
            LabelGroup(
                label_group_name,
                [fxt_label_schema_example.flowering],
                LabelGroupType.EXCLUSIVE,
            )
        )

        label_schema.add_labels_to_group_by_group_name(label_group_name, [fxt_label_schema_example.no_plant])

        copy_schema = label_schema
        assert label_schema == copy_schema

        new_schema = LabelSchema(
            id_=LabelSchemaRepo.generate_id(),
            label_tree=label_schema.label_tree,
            label_groups=label_schema.get_groups(True),
        )

        assert new_schema != label_schema

        assert NullLabelSchema() != label_schema
        assert label_schema != NullLabelSchema()
        assert NullLabelSchema() == NullLabelSchema()

    def test_get_label_by_id(self, fxt_mongo_id, fxt_label_schema_example) -> None:
        """
        <b>Description:</b>
        Check that LabelSchema.get_label_by_id works correctly

        <b>Input data:</b>
        LabelSchema instance

        <b>Expected results:</b>
        The method returns the label if present in the schema, and None if not present.

        <b>Steps</b>
        1. Call LabelSchema.get_label_by_id with the ID of a label that exists in the schema
        2. Call LabelSchema.get_label_by_id with the ID of a label that does NOT exist in the schema
        3. Check that the first call returned the expected label
        4. Check that the second call returned None
        """
        # Arrange
        label: Label = fxt_label_schema_example.flowering
        label_schema: LabelSchema = fxt_label_schema_example.label_schema

        # Act
        retrieved_existing_label = label_schema.get_label_by_id(label_id=label.id_)
        retrieved_non_existing_label = label_schema.get_label_by_id(label_id=fxt_mongo_id(24543))

        # Assert
        assert retrieved_existing_label == label
        assert retrieved_non_existing_label is None

    def test_get_label_by_name(self, fxt_mongo_id, fxt_label_schema_example) -> None:
        """
        <b>Description:</b>
        Check that LabelSchema.get_label_by_name works correctly

        <b>Input data:</b>
        LabelSchema instance

        <b>Expected results:</b>
        The method returns the label if present in the schema, and None if not present.

        <b>Steps</b>
        1. Call LabelSchema.get_label_by_name with the ID of a label that exists in the schema
        2. Call LabelSchema.get_label_by_name with the ID of a label that does NOT exist in the schema
        3. Check that the first call returned the expected label
        4. Check that the second call returned None
        """
        # Arrange
        label: Label = fxt_label_schema_example.flowering
        label_schema: LabelSchema = fxt_label_schema_example.label_schema

        # Act
        retrieved_existing_label = label_schema.get_label_by_name(label_name=label.name)
        retrieved_non_existing_label = label_schema.get_label_by_name(label_name="non existing")

        # Assert
        assert retrieved_existing_label == label
        assert retrieved_non_existing_label is None

    def test_add_label_relations_for_task(self, fxt_ote_id) -> None:
        """
        Test 'add_label_relations_for_task' in a complex scenario:
            - detection -> classification hierarchical project
            - 1 detection label
            - 2 top-level classification labels
            - 2 children classification labels for each top-level one
        """

        det1 = Label(name="det1", domain=Domain.DETECTION, id_=fxt_ote_id(1))
        cls1 = Label(name="cls1", domain=Domain.CLASSIFICATION, id_=fxt_ote_id(2))
        cls2 = Label(name="cls2", domain=Domain.CLASSIFICATION, id_=fxt_ote_id(3))
        cls1_1 = Label(name="cls1_1", domain=Domain.CLASSIFICATION, id_=fxt_ote_id(4))
        cls1_2 = Label(name="cls1_2", domain=Domain.CLASSIFICATION, id_=fxt_ote_id(5))
        cls2_1 = Label(name="cls2_1", domain=Domain.CLASSIFICATION, id_=fxt_ote_id(6))
        cls2_2 = Label(name="cls2_2", domain=Domain.CLASSIFICATION, id_=fxt_ote_id(7))
        det_labels = [det1]
        cls_labels = [cls1, cls2, cls1_1, cls1_2, cls2_1, cls2_2]
        det_grp = LabelGroup(name="det_group", labels=[det1])
        cls_grp_top = LabelGroup(name="cls_grp_top", labels=[cls1, cls2])
        cls_grp_bot_1 = LabelGroup(name="cls_grp_bot_1", labels=[cls1_1, cls1_2])
        cls_grp_bot_2 = LabelGroup(name="cls_grp_bot_2", labels=[cls2_1, cls2_2])
        label_schema = LabelSchema(
            id_=fxt_ote_id(100),
            label_groups=[det_grp, cls_grp_top, cls_grp_bot_1, cls_grp_bot_2],
            project_id=fxt_ote_id,
        )
        child_to_parent = {
            cls1_1: cls1.name,
            cls1_2: cls1.name,
            cls2_1: cls2.name,
            cls2_2: cls2.name,
        }

        label_schema.add_label_relations_for_task(
            task_labels=cls_labels,
            child_to_parent_id=child_to_parent,
            previous_trainable_task_labels=det_labels,
            add_previous_task_label_as_parent=True,
        )

        assert len(label_schema.label_tree.nodes) == len(det_labels + cls_labels)
        edges = {(edge[0], edge[1]) for edge in label_schema.label_tree.edges}
        expected_edges = {
            (cls1, det1),
            (cls2, det1),
            (cls1_1, cls1),
            (cls1_2, cls1),
            (cls2_1, cls2),
            (cls2_2, cls2),
        }
        assert edges == expected_edges


@pytest.mark.ScSdkComponent
class TestLabelSchemaView:
    def test_label_schema_view_creation(self, fxt_label_schema_example) -> None:
        """
        <b>Description:</b>
        Check that creating a LabelSchemaView through the __init__, from_parent and from_labels methods
         works correctly

        <b>Input data:</b>
        Label Group "Plant state"
        LabelSchemaExample instance

        <b>Expected results:</b>
        Test passes if the LabelSchemaView contains the correct labels and label groups based on the way
        it was constructed

        <b>Steps</b>
        1. Create LabelSchema with "Plant state" label group
        2. Create LabelSchemaView using __init__ method with this LabelSchema
        3. Check that the LabelSchemaView and the LabelSchema contain the same label groups and labels
        4. Create LabelSchemaView using "from_parent" method with all labels this LabelSchema
        5. Check that the LabelSchemaView and the LabelSchema contain the same label groups and labels
        6. Create LabelSchemaView using "from_parent" method with this LabelSchema, only using some of the labels
        7. Check that the LabelSchemaView and the LabelSchema contain the same label groups and labels
        8. Create LabelSchemaView using "from_label" method with all labels in "Plant state" label group
        9. Check that the LabelSchemaView contains the correct labels
        """
        flowering = fxt_label_schema_example.flowering
        no_plant = fxt_label_schema_example.no_plant
        vegetative = fxt_label_schema_example.vegetative
        all_labels = [flowering, no_plant, vegetative]
        filtered_labels = [flowering, no_plant]

        label_schema = LabelSchema(id_=LabelSchemaRepo.generate_id())
        label_schema.add_group(LabelGroup("Plant state", all_labels, LabelGroupType.EXCLUSIVE))

        # Using __init__ method
        label_schema_view = LabelSchemaView(
            label_schema=label_schema,
            label_groups=label_schema.get_groups(include_empty=True),
            id_=LabelSchemaRepo.generate_id(),
        )

        assert label_schema.get_groups(include_empty=True) == label_schema_view.get_groups(include_empty=True)
        assert label_schema.get_labels(include_empty=True) == label_schema_view.get_labels(include_empty=True)

        # Using from_parent method
        # First construct using all labels
        label_schema_view = LabelSchemaView.from_parent(
            parent_schema=label_schema,
            labels=all_labels,
            id_=LabelSchemaRepo.generate_id(),
        )

        assert label_schema.get_groups(include_empty=True) == label_schema_view.get_groups(include_empty=True)
        assert label_schema_view.get_labels(include_empty=True) == all_labels

        # Construct using only some labels
        label_schema_view = LabelSchemaView.from_parent(
            parent_schema=label_schema,
            labels=filtered_labels,
            id_=LabelSchemaRepo.generate_id(),
        )

        assert label_schema.get_labels(include_empty=True) != filtered_labels
        assert label_schema_view.get_labels(include_empty=True) == filtered_labels

        # Using from_labels method
        label_schema_view = LabelSchemaView.from_labels(labels=all_labels)

        assert label_schema_view.get_labels(include_empty=True) == all_labels

    def test_label_schema_view_label_schema_methods(self, fxt_label_schema_example) -> None:
        """
        <b>Description:</b>
        Check that using LabelSchema methods through LabelSchemaView works properly. This function does not test
        every LabelSchema method, since that is beyond the scope of this test. It only tests that calling some
        LabelSchema methods through LabelSchemaView works

        <b>Input data:</b>
        LabelSchemaExample instance

        <b>Expected results:</b>
        Test passes if using LabelSchema methods through LabelSchemaView works as expected

        <b>Steps</b>
        1. Create a list of labels
        2. Create LabelSchemaView from these labels
        3. Check that using LabelSchemaView.add_group() (which is a method of LabelSchema) works
        4. Check that getting labels, label groups and exclusive groups (which are methods of LabelSchema) works
         properly through LabelSchemaView, and these change between the parent schema and the LabelSchemaView
        """
        flowering = fxt_label_schema_example.flowering
        vegetative = fxt_label_schema_example.vegetative
        all_labels = [flowering, vegetative]

        label_schema_view = LabelSchemaView.from_labels(labels=all_labels)
        new_group = LabelGroup(name="New label group", labels=[fxt_label_schema_example.no_plant])

        # Check that adding group works
        label_schema_view.add_group(new_group)

        # Check getting labels, label groups and exclusive groups
        groups_in_label_schema_view = label_schema_view.get_groups(include_empty=True)
        groups_in_parent_schema = label_schema_view.parent_schema.get_groups(include_empty=True)

        labels_in_label_schema_view = label_schema_view.get_labels(include_empty=True)
        labels_in_parent_schema = label_schema_view.parent_schema.get_labels(include_empty=True)

        exclusive_groups_in_label_schema_view = label_schema_view.get_exclusive_groups()
        exclusive_groups_in_parent_schema = label_schema_view.parent_schema.get_exclusive_groups()

        assert len(groups_in_label_schema_view) == len(groups_in_parent_schema) + 1
        assert len(labels_in_label_schema_view) == len(labels_in_parent_schema) + 1
        assert len(exclusive_groups_in_label_schema_view) == len(exclusive_groups_in_parent_schema) + 1

    def test_labelschemaview_equality(self, fxt_label_schema_example) -> None:
        """
        <b>Description:</b>
        Check that LabelSchemaView equality works correctly

        <b>Input data:</b>
        LabelSchemaView instances with different labels

        <b>Expected results:</b>
        == and != operations work correctly for various inputs

        <b>Steps</b>
        1. Test LabelSchemaView equality
        """
        label_schema = LabelSchema(id_=ID("test"))

        label_group_name = "Vegetation"
        label_schema.add_group(
            LabelGroup(
                label_group_name,
                [
                    fxt_label_schema_example.flowering,
                    fxt_label_schema_example.vegetative,
                ],
                LabelGroupType.EXCLUSIVE,
            )
        )

        label_schema.add_labels_to_group_by_group_name(label_group_name, [fxt_label_schema_example.no_plant])

        view_id = LabelSchemaRepo.generate_id()
        label_schemaview = LabelSchemaView.from_parent(
            label_schema, labels=[fxt_label_schema_example.flowering], id_=view_id
        )
        copy_label_schemaview = LabelSchemaView.from_parent(
            label_schema, labels=[fxt_label_schema_example.flowering], id_=view_id
        )

        assert label_schemaview == copy_label_schemaview

        new_labelschemaview = LabelSchemaView.from_parent(
            label_schema,
            labels=[fxt_label_schema_example.no_plant],
            id_=LabelSchemaRepo.generate_id(),
        )
        assert label_schemaview != new_labelschemaview

    @pytest.mark.parametrize(
        "domain",
        [
            Domain.DETECTION,
            Domain.SEGMENTATION,
            Domain.ROTATED_DETECTION,
        ],
        ids=lambda domain: domain.name,
    )
    def test_get_empty_labels(self, fxt_label_schema_factory, domain):
        """
        Test LabelSchema.get_empty_labels()

        empty_labels, which is return value of the target function,
        has to include all empty labels in the label schema
        """
        all_labels = fxt_label_schema_factory(domain).get_labels(include_empty=True)
        non_empty_labels = fxt_label_schema_factory(domain).get_labels(include_empty=False)
        empty_labels = fxt_label_schema_factory(domain).get_empty_labels()

        assert sorted(all_labels) == sorted(non_empty_labels + list(empty_labels))

        for non_empty_label in non_empty_labels:
            assert not non_empty_label.is_empty

        for empty_label in empty_labels:
            assert empty_label.is_empty

    def test_get_label_map(self, fxt_label):
        schema = NullLabelSchema()
        expected_map = {fxt_label.id_: fxt_label}
        with patch.object(LabelSchema, "get_labels", return_value=[fxt_label]):
            label_map = schema.get_label_map()
        assert label_map == expected_map
