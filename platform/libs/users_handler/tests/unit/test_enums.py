"""Unit tests for the enums module."""

# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

import pytest
from geti_spicedb_tools import SpiceDBUserRoles


class TestSpiceDBUserRoles:
    """
    Tests the SpiceDBUserRoles class.
    """

    @staticmethod
    @pytest.mark.parametrize(
        "resource_type, relation, role_expected",
        (
            ("project", "project_manager", "admin"),
            ("project", "project_contributor", "contributor"),
            ("workspace", "workspace_admin", "admin"),
            ("workspace", "workspace_contributor", "contributor"),
        ),
    )
    def test_role_from_relation_positive(resource_type: str, relation: str, role_expected: str) -> None:
        """
        Tests the role_from_relation method, positive case.
        """
        role_actual: str = SpiceDBUserRoles.role_from_relation(resource_type=resource_type, relation=relation)

        assert role_actual == role_expected

    @staticmethod
    @pytest.mark.parametrize(
        "resource_type, relation", (("unknown_resource", "project_manager"), ("unknown_resource_2", "workspace_admin"))
    )
    def test_role_from_relation_unknown_resource_type(resource_type: str, relation: str) -> None:
        """
        Tests the role_from_relation method, negative case.

        Covers the scenario in which the provided resource type is unknown (unsupported).
        """
        with pytest.raises(KeyError):
            SpiceDBUserRoles.role_from_relation(resource_type=resource_type, relation=relation)

    @staticmethod
    @pytest.mark.parametrize(
        "resource_type, relation", (("project", "unknown_relation"), ("workspace", "unknown_relation"))
    )
    def test_role_from_relation_no_app_role_match(resource_type: str, relation: str) -> None:
        """
        Tests the role_from_relation method, negative case.

        Covers the scenario in which the provided resource is known (supported),
        and there is no app role match for the provided relation.
        """
        with pytest.raises(ValueError):
            SpiceDBUserRoles.role_from_relation(resource_type=resource_type, relation=relation)
