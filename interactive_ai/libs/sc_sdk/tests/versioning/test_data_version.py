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

from sc_sdk.versioning.data_version import DataVersion, SchemaChangeType


@pytest.mark.ScSdkComponent
class TestDataVersion:
    def test_properties(self) -> None:
        data_version = DataVersion("5.8")
        assert data_version.major == 5
        assert data_version.minor == 8

    def test_get_current(self) -> None:
        # just check that it doesn't throw an exception
        DataVersion.get_current()

    def test_get_next(self) -> None:
        data_version = DataVersion("5.8")

        next_major = data_version.get_next(SchemaChangeType.BREAKING)
        next_minor = data_version.get_next(SchemaChangeType.NON_BREAKING)

        assert next_major == DataVersion("6.0")
        assert next_minor == DataVersion("5.9")

    def test_get_previous_major(self) -> None:
        data_version = DataVersion("5.8")

        previous_major = data_version.get_previous_major()

        assert previous_major == DataVersion("4.0")

    def test_equality(self) -> None:
        assert DataVersion("5.8") == DataVersion("5.8")
        assert DataVersion("5.8") != DataVersion("5.9")

    def test_order(self) -> None:
        assert DataVersion("2.0") > DataVersion("1.0")
        assert DataVersion("3.2") > DataVersion("2.3")
        assert DataVersion("3.3") > DataVersion("3.2")
        assert DataVersion("3.10") > DataVersion("3.9")
        assert DataVersion("10.0") > DataVersion("1.0")
        assert DataVersion("10.0") > DataVersion("9.0")

    def test_repr(self) -> None:
        assert str(DataVersion("5.8")) == "DataVersion('5.8')"
