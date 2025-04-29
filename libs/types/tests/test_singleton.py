from unittest.mock import patch

from geti_types import Singleton


class MySingleton1(metaclass=Singleton):
    def __init__(self) -> None:
        pass


class MySingleton2(metaclass=Singleton):
    def __init__(self) -> None:
        pass


class TestSingleton:
    def test_singleton(self) -> None:
        """
        Check that each Singleton subclass is only instantiated once
        """
        with patch.object(MySingleton1, "__init__", side_effect=MySingleton1.__init__, autospec=True) as mock:
            singleton1 = MySingleton1()
            singleton2 = MySingleton1()
            mock.assert_called_once()

        assert id(singleton1) == id(singleton2), "Objects should refer to the same instance"

        with patch.object(MySingleton2, "__init__", side_effect=MySingleton2.__init__, autospec=True) as mock:
            singleton3 = MySingleton2()
            mock.assert_called_once()

        assert id(singleton1) != id(singleton3), "Objects should refer to different instance"
