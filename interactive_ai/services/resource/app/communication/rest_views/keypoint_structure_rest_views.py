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

"""
This module implements rest views for keypoint structure entities
"""

from typing import Any

from sc_sdk.entities.keypoint_structure import KeypointStructure

EDGES = "edges"
KEYPOINT_STRUCTURE = "keypoint_structure"
POSITIONS = "positions"
LABEL = "label"
NODES = "nodes"
X = "x"
Y = "y"


class KeypointStructureRESTViews:
    @staticmethod
    def keypoint_structure_to_rest(keypoint_structure: KeypointStructure) -> dict[str, Any]:
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
