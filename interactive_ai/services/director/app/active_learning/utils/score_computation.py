# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from collections.abc import Callable, Mapping, Sequence
from typing import TypeVar

import numpy as np

KeyT = TypeVar("KeyT")


def reduce_dict_values(
    input_dict: Mapping[KeyT, Sequence[float]],
    reduce_fn: Callable[[Sequence[float]], float] = np.nanmean,
) -> dict[KeyT, float]:
    """
    Given a dictionary whose values are a sequence of float, transform it into
    another dictionary with the same keys but values obtained by reducing the original
    sequence to a single float, exploiting a specific reduction function.

    Note: an empty list will be reduced to value 1.

    :param input_dict: Dict whose values are float lists.
    :param reduce_fn: Function to reduce each list of floats to a single float
    :return: Dictionary with same keys and reduced values
    """
    return {key: reduce_fn(values) if values else 1.0 for key, values in input_dict.items()}
