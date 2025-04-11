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

from geti_types import Singleton


class MySingleton1(metaclass=Singleton):
    def __init__(self) -> None:
        pass


class MySingleton2(metaclass=Singleton):
    def __init__(self) -> None:
        pass


@pytest.mark.ScSdkComponent
class TestSingleton:
    def test_singleton(self) -> None:
        """
        <b>Description:</b>
        Check that each Singleton subclass is only instantiated once

        <b>Input data:</b>
        Singleton subclasses

        <b>Expected results:</b>
        Test passes if MySingleton1 and MySingleton2 are only instantiated once

        <b>Steps</b>
        1. Create MySingleton1
        2. Create MySingleton2
        """
        with patch.object(MySingleton1, "__init__", side_effect=MySingleton1.__init__, autospec=True) as mock:
            singleton1 = MySingleton1()
            singleton2 = MySingleton1()
            mock.assert_called_once()

        assert id(singleton1) == id(singleton2), "Expected to get the entity"

        with patch.object(MySingleton2, "__init__", side_effect=MySingleton2.__init__, autospec=True) as mock:
            singleton3 = MySingleton2()

        assert id(singleton1) != id(singleton3), "Expected to get the different entity"
