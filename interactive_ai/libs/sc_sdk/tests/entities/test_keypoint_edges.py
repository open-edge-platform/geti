# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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

import pytest

from sc_sdk.entities.keypoint_structure import KeypointEdge, KeypointPosition, KeypointStructure

from geti_types import ID


@pytest.mark.ScSdkComponent
class TestKeypointStructure:
    def test_edges_and_position(self) -> None:
        """
        <b>Description:</b>
        Check the KeypointStructure is correctly initialized.

        <b>Input data:</b>
        KeypointStructure data

        <b>Expected results:</b>
        Test passes if the KeypointStructure object has the correct properties.

        <b>Steps</b>
        1. Create KeypointStructure with an edge and position.
        2. Assert the KeypointStructure object has the correct properties.
        """
        kps_edge = KeypointEdge(node_1=ID("node1"), node_2=ID("node2"))
        assert kps_edge.node_1 == ID("node1")
        assert kps_edge.node_2 == ID("node2")
        assert str(kps_edge) == "(node1-node2)"

        kps_position = KeypointPosition(node=ID("node1"), x=1.0, y=1.0)
        assert kps_position.node == ID("node1")
        assert kps_position.x == 1.0
        assert kps_position.y == 1.0

        kps = KeypointStructure(edges=[kps_edge], positions=[kps_position])
        assert kps._edges == [kps_edge]
        assert kps._positions == [kps_position]
        assert str(kps) == "KeypointStructure(edges=[(node1-node2)], positions=[keypoint: node1, at (1.0, 1.0)])"

    def test_contains_edge(self) -> None:
        """
        <b>Description:</b>
        Check if an edge is in the kps

        <b>Input data:</b>
        A KeypointStructure an edge.

        <b>Expected results:</b>
        Test passes if the edge is correctly found in the kps

        <b>Steps</b>
        1. Create keypoint structure with an edge.
        2. Assert keypoint structure contains the edge.
        3. Assert keypoint structure contains the reverse edge.
        4. Assert keypoint structure does not contain an edge.
        """
        kps = KeypointStructure(edges=[KeypointEdge(node_1=ID("node1"), node_2=ID("node2"))], positions=[])

        assert kps.contains_edge(KeypointEdge(node_1=ID("node1"), node_2=ID("node2")))
        assert kps.contains_edge(KeypointEdge(node_1=ID("node2"), node_2=ID("node1")))
        assert not kps.contains_edge(KeypointEdge(node_1=ID("does_not"), node_2=ID("exist")))

    def test_get_edges_with_label(self) -> None:
        """
        <b>Description:</b>
        Check that all edges with a specific label are returned

        <b>Input data:</b>
        A KeypointStructure with multiple edges.

        <b>Expected results:</b>
        Test passes if the edges are returned

        <b>Steps</b>
        1. Create keypoint structure with multiple edges.
        2. Assert keypoint structure is correctly made.
        3. Get edges with a specific label.
        4. Assert the list of edges is correct.
        """
        # node 1 with 4 edges in a kps with 5 total edges
        node_1_kps_edges = [
            KeypointEdge(node_1=ID("node1"), node_2=ID("node2")),
            KeypointEdge(node_1=ID("node1"), node_2=ID("node3")),
            KeypointEdge(node_1=ID("node1"), node_2=ID("node4")),
            KeypointEdge(node_1=ID("node1"), node_2=ID("node5")),
        ]
        extra_edges = [
            KeypointEdge(node_1=ID("node6"), node_2=ID("node7")),
        ]
        total_kps_edges = node_1_kps_edges + extra_edges
        kps = KeypointStructure(edges=total_kps_edges, positions=[])

        assert len(kps._edges) == 5
        assert kps._edges == total_kps_edges

        edges_with_node_1 = kps.get_edges_with_keypoint(ID("node1"))
        assert len(edges_with_node_1) == 4
        assert edges_with_node_1 == node_1_kps_edges

    def test_add_edge(self) -> None:
        """
        <b>Description:</b>
        Check an edge can be added with no duplicates

        <b>Input data:</b>
        A KeypointStructure with multiple edges.

        <b>Expected results:</b>
        Test passes if the edge is added.

        <b>Steps</b>
        1. Create keypoint structure with multiple edges.
        2. Assert keypoint structure is correctly made.
        3. Add the edge.
        4. Assert the kps has the correct structure.
        """
        kps_edges = [
            KeypointEdge(node_1=ID("node1"), node_2=ID("node2")),
            KeypointEdge(node_1=ID("node1"), node_2=ID("node3")),
            KeypointEdge(node_1=ID("node1"), node_2=ID("node4")),
            KeypointEdge(node_1=ID("node1"), node_2=ID("node5")),
        ]
        extra_edge = KeypointEdge(node_1=ID("node6"), node_2=ID("node7"))

        kps = KeypointStructure(edges=kps_edges, positions=[])
        kps.add_edge(edge=extra_edge)

        assert len(kps._edges) == 5
        kps_edges.append(extra_edge)
        assert kps._edges == kps_edges

    @staticmethod
    def test_add_duplicate_edge_error() -> None:
        """
        <b>Description:</b>
        Check an edge can be added with no duplicates

        <b>Input data:</b>
        A KeypointStructure with multiple edges.

        <b>Expected results:</b>
        Test passes if duplicate edges (and reverse of those edges) are not added.

        <b>Steps</b>
        1. Create keypoint structure with multiple edges.
        2. Assert keypoint structure is correctly made.
        3. Add the duplicate edge.
        4. Assert the duplicate edge has not been added, and an error has been raised.
        5. Add the duplicate reverse edge.
        6. Assert the duplicate reverse edge has not been added, and an error has been raised.
        """
        edge = KeypointEdge(node_1=ID("node1"), node_2=ID("node2"))
        kps = KeypointStructure(edges=[edge], positions=[])

        with pytest.raises(ValueError):
            kps.add_edge(edge=edge)

        assert len(kps._edges) == 1

        reverse_edge = KeypointEdge(node_1=ID("node2"), node_2=ID("node1"))

        with pytest.raises(ValueError):
            kps.add_edge(edge=reverse_edge)

        assert len(kps._edges) == 1

    def test_remove_edge(self) -> None:
        """
        <b>Description:</b>
        Check an edge can be removed.

        <b>Input data:</b>
        A KeypointStructure with multiple edges.

        <b>Expected results:</b>
        Test passes if the edge (and reverse of the edge) are removed.

        <b>Steps</b>
        1. Create keypoint structure with multiple edges.
        2. Assert keypoint structure is correctly made.
        3. Remove edge.
        4. Assert keypoint structure has correct structure.
        5. Add edge back to keypoint structure.
        6. Remove reverse edge from keypoint structure.
        7. Assert the keypoint structure has the correct structure.
        """
        edge_1 = KeypointEdge(node_1=ID("node1"), node_2=ID("node2"))
        edge_2 = KeypointEdge(node_1=ID("node2"), node_2=ID("node3"))
        kps = KeypointStructure(edges=[edge_1, edge_2], positions=[])

        assert len(kps._edges) == 2
        assert kps._edges == [edge_1, edge_2]

        kps.remove_edge(edge_1)
        assert len(kps._edges) == 1
        assert kps._edges == [edge_2]

        reverse_edge_1 = KeypointEdge(node_1=ID("node2"), node_2=ID("node1"))
        kps.add_edge(edge=edge_1)
        kps.remove_edge(reverse_edge_1)
        assert len(kps._edges) == 1
        assert kps._edges == [edge_2]

    def test_remove_edges_with_label(self) -> None:
        """
        <b>Description:</b>
        Check that all edges with a specific label are removed.

        <b>Input data:</b>
        A KeypointStructure with a node with multiple edges.

        <b>Expected results:</b>
        Test passes if all edges with a specific label are removed and the correct number of edges remain.

        <b>Steps</b>
        1. Create keypoint structure with multiple edges.
        2. Assert keypoint structure is correctly made.
        3. Remove all edges with a specific label.
        4. Assert the keypoint structure has the correct structure.
        """
        kps_edges = [
            KeypointEdge(node_1=ID("node1"), node_2=ID("node2")),
            KeypointEdge(node_1=ID("node1"), node_2=ID("node3")),
            KeypointEdge(node_1=ID("node1"), node_2=ID("node4")),
            KeypointEdge(node_1=ID("node1"), node_2=ID("node5")),
            KeypointEdge(node_1=ID("node6"), node_2=ID("node7")),
        ]
        kps = KeypointStructure(edges=kps_edges, positions=[])

        assert len(kps._edges) == 5
        assert kps._edges == kps_edges

        kps.remove_edges_with_keypoint(ID("node1"))
        assert len(kps._edges) == 1
        assert kps._edges == [KeypointEdge(node_1=ID("node6"), node_2=ID("node7"))]

    def test_get_position_with_label(self) -> None:
        """
        <b>Description:</b>
        Check a position can be retrieved

        <b>Input data:</b>
        A KeypointStructure with multiple positions.

        <b>Expected results:</b>
        Test passes if a position is correctly retrieved

        <b>Steps</b>
        1. Create keypoint structure with multiple positions.
        2. Assert keypoint structure is correctly made.
        3. Assert the correct position is returned.
        """
        kps_positions = [
            KeypointPosition(node=ID("node1"), x=0.1, y=0.1),
            KeypointPosition(node=ID("node2"), x=0.2, y=0.2),
            KeypointPosition(node=ID("node3"), x=0.3, y=0.3),
            KeypointPosition(node=ID("node4"), x=0.4, y=0.4),
        ]
        kps = KeypointStructure(edges=[], positions=kps_positions)

        assert len(kps._positions) == 4
        assert kps._positions == kps_positions
        assert kps.get_position_of_keypoint(ID("node3")) == KeypointPosition(node=ID("node3"), x=0.3, y=0.3)
