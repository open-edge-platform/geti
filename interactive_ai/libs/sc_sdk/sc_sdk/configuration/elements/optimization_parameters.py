# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from dataclasses import dataclass, fields


class DefaultFields:
    def __post_init__(self):
        """
        Substitutes fields with default value if None
        """
        for field in fields(self):
            if getattr(self, field.name) is None:
                setattr(self, field.name, field.default)


@dataclass
class POTOptimizationParameters(DefaultFields):
    """
    Store POT OptimizationParameters as an object.
    """

    stat_subset_size: int = 300
