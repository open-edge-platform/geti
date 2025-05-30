# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains the ConfigurableEnum, that is used to define Enums which can be configured by the user."""

from enum import Enum

from .metadata_keys import ENUM_NAME, OPTIONS


class ConfigurableEnum(Enum):
    """This class is used as the basis for defining `selectable` configurable parameters in the OTX API.

    Enums reflecting `selectable` options should inherit from thisclass.
    """

    def __str__(self):
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ConfigurableEnum) and self.__class__.__name__ == other.__class__.__name__:
            return self.value == other.value and self.name == other.name
        return False

    def __hash__(self):
        """Computes hash for the ConfigurableEnum instance."""
        return hash(self.name)

    @classmethod
    def get_class_info(cls) -> dict:
        """Creates a dictionary representation of the ConfigurableEnum.

        This includes the name of the enum and the (name, value) pairs representing its members.

        :return: Dictionary representation of the ConfigurableEnum.
        """
        options_dict = {name: instance.value for name, instance in cls.__members__.items()}

        return {ENUM_NAME: cls.__name__, OPTIONS: options_dict}

    @classmethod
    def get_names(cls) -> list[str]:
        """Returns a list of names that can be used to index the Enum."""
        return [x.name for x in cls]

    @classmethod
    def get_values(cls) -> list[str]:
        """Returns a list of values that can be used to index the Enum."""
        return [x.value for x in cls]
