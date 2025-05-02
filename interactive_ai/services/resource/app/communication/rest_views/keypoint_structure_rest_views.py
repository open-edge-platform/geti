# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements rest views for keypoint structure entities
"""

from typing import Any

from iai_core.entities.keypoint_structure import KeypointStructure

EDGES = "edges"
KEYPOINT_STRUCTURE = "keypoint_structure"
POSITIONS = "positions"
LABEL = "label"
NODES = "nodes"
X = "x"
Y = "y"


class KeypointStructureRESTViews:
    @staticmethod
    def keypoint_structure_to_rest(
        keypoint_structure: KeypointStructure,
    ) -> dict[str, Any]:
        """
        Converts a KeypointStructure object to a dictionary representation suitable for REST API responses.

        :param keypoint_structure: The KeypointStructure object to convert.
        :return: the REST representation of the KeypointStructure object.
        """
        return {
            EDGES: [{NODES: [str(edge.node_1), str(edge.node_2)]} for edge in keypoint_structure._edges],
            POSITIONS: [
                {LABEL: str(position.node), X: position.x, Y: position.y} for position in keypoint_structure._positions
            ],
        }
