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
"""This module implements the KeypointStructure entity"""

import logging
from dataclasses import dataclass

from geti_types import ID

logger = logging.getLogger(__name__)


@dataclass
class KeypointEdge:
    """
    An edge in the graph represented by two nodes. The edge does not have a direction.
    """

    node_1: ID  # ID of label 1
    node_2: ID  # ID of label 2

    def __repr__(self) -> str:
        return f"({self.node_1}-{self.node_2})"


@dataclass
class KeypointPosition:
    """
    The position of the keypoint in normalized coordinate space.
    """

    node: ID
    x: float
    y: float

    def __repr__(self) -> str:
        return f"keypoint: {self.node}, at ({self.x}, {self.y})"


class KeypointStructure:
    """
    KeypointStructure defines the graph and position

    KeypointStructure is made up of multiple KeypointEdges and KeypointPositions.
    - duplicated edges are not allowed
    - the graph does not need to be fully connected
    - an edge must have exactly 2 nodes
    - positions are in normalised coordinate space
    """

    def __init__(self, edges: list[KeypointEdge], positions: list[KeypointPosition]):
        self._edges = edges
        self._positions = positions

    def contains_edge(self, edge: KeypointEdge) -> bool:
        """
        Checks if an edge is in the graph.

        :param edge: The edge to check
        :return: True if the edge is in the graph, False otherwise
        """
        return any({old_edge.node_1, old_edge.node_2} == {edge.node_1, edge.node_2} for old_edge in self._edges)

    def get_edges_with_keypoint(self, keypoint_id: ID) -> list[KeypointEdge]:
        """
        Gets a list of all the edges in a graph which include the specified keypoint.

        :param keypoint_id: ID of the keypoint
        :return: A list of edges from the graph which include the keypoint
        """
        return [edge for edge in self._edges if keypoint_id in (edge.node_1, edge.node_2)]

    def add_edge(self, edge: KeypointEdge) -> None:
        """
        Adds a new edge to the graph.

        :param edge: The edge to add
        :raises ValueError: If the edge already exists
        """
        if self.contains_edge(edge):
            raise ValueError(f"Edge {edge} already exists")
        self._edges.append(edge)

    def remove_edge(self, edge: KeypointEdge) -> None:
        """
        Removes an edge from the graph.

        :param edge: The edge to remove
        """
        for old_edge in self._edges:
            if {old_edge.node_1, old_edge.node_2} == {edge.node_1, edge.node_2}:
                self._edges.remove(old_edge)
                return
        logger.debug(f"Tried to remove edge {edge} but it does not exist.")

    def remove_edges_with_keypoint(self, keypoint_id: ID) -> None:
        """
        Removes all edges in the graph which include the specified keypoint.

        :param keypoint_id: ID of the keypoint
        """
        self._edges = [edge for edge in self._edges if keypoint_id not in (edge.node_1, edge.node_2)]

    def get_position_of_keypoint(self, keypoint_id: ID) -> KeypointPosition:
        """
        Gets a KeypointPosition object for the specified label.

        :param keypoint_id: ID of the label
        :return: KeypointPosition object for the specified label
        :raises ValueError: If the label does not exist in the positions data
        """
        for position in self._positions:
            if position.node == keypoint_id:
                return position
        raise ValueError(f"Keypoint {keypoint_id} does not exist in the positions data")

    def __repr__(self) -> str:
        return f"KeypointStructure(edges={self._edges}, positions={self._positions})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, KeypointStructure):
            return False
        return self._edges == other._edges and self._positions == other._positions


class NullKeypointStructure(KeypointStructure):
    """Representation of an empty KeypointStructure"""

    def __init__(self) -> None:
        super().__init__(edges=[], positions=[])

    def __repr__(self) -> str:
        return "NullKeypointStructure()"
