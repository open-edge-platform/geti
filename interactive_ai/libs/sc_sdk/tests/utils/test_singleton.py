# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
