# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Utilities to enhance Python classes"""


class classproperty(property):
    """
    Decorator to implement class 'static' properties, that is properties
    that are relative to the class rather than the instance.
    It's like class-level attributes, but you can define your custom getter here (which
    possibly leverages other class-methods). The behavior is roughly the one you would
    expect by combining @property with @classmethod, although that wouldn't work due
    to how the decorators are stacked.

    >>> class A:
    >>>   @classmethod
    >>>   def _impt(cls):
    >>>     return 3
    >>>
    >>>   @classproperty
    >>>   def x(cls):
    >>>     return cls._impt()
    >>>
    >>> A.x    # 3
    >>> A().x  # 3
    """

    def __get__(self, cls, owner):  # noqa: ANN001
        return classmethod(self.fget).__get__(None, owner)()
