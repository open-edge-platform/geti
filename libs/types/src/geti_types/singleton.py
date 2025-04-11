import abc
import threading
from typing import Any


class Singleton(abc.ABCMeta):
    # We subclass GenericMeta instead of ABCMeta to allow Singleton to be used as metaclass for a generic class.
    """
    Metaclass to create singleton classes.

    :example: The class can be used as follows:

        .. code-block:: python
            class Foo(metaclass=Singleton):
                def __init__(self):
                    ...

        The class `Foo` will be instantiated only once and subsequent calls to `Foo()`
        will return the existing instance of `Foo`.
    """

    def __new__(cls, clsname, bases, dct):  # noqa: ANN001
        def __deepcopy__(self, memo_dict=None):  # noqa: ANN001
            # Since the classes are singleton per-project, we can return the same object.
            if memo_dict is None:
                memo_dict = {}
            memo_dict[id(self)] = self
            return self

        def __copy__(self):  # noqa: ANN001
            # Since the classes are singleton per-project, we can return the same object.
            return self

        newclass = super().__new__(cls, clsname, bases, dct)
        setattr(newclass, __deepcopy__.__name__, __deepcopy__)
        setattr(newclass, __copy__.__name__, __copy__)
        return newclass

    def __init__(cls, clsname, bases, dct) -> None:  # noqa: ANN001
        super().__init__(clsname, bases, dct)
        cls._lock = threading.Lock()
        cls._instance: Singleton | None = None

    def __call__(cls, *args, **kwargs) -> Any:
        if cls._instance is None:  # double-checked locking
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__call__(*args, **kwargs)
        return cls._instance
