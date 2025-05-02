# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from .score_computation import reduce_dict_values
from iai_core.entities.datasets import Dataset, NullDataset

NullableDataset = Dataset | NullDataset

__all__ = ["NullableDataset", "reduce_dict_values"]
