# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module define the scored label entity."""

import math
from dataclasses import dataclass, field

from geti_types import ID


@dataclass
class LabelSource:
    """This dataclass contains information about the source of a scored label.

    For annotations, the id of the user who created the label and for predictions, the
    id and model storage id of the model that created the prediction. When a user has
    accepted a predictions as is, both the user id of the user who accepted and the
    model/model storage id of the model that predicted should be filled in.
    """

    user_id: str = ""
    model_id: ID = field(default_factory=ID)
    model_storage_id: ID = field(default_factory=ID)


class ScoredLabel:
    """This represents a label along with a probability. This is used inside `Annotation` class.

    :param label_id: ID of the Label to which probability and source are attached.
    :param is_empty: bool indicating whether label is the empty label
    :param probability: a float denoting the probability of the shape belonging to the label.
    :param label_source: a LabelSource dataclass containing the id of the user who created
        or the model that predicted this label.
    """

    def __init__(
        self, label_id: ID, is_empty: bool = False, probability: float = 0.0, label_source: LabelSource | None = None
    ):
        if math.isnan(probability) or (not 0 <= probability <= 1.0):
            raise ValueError(f"Probability should be in range [0, 1], {probability} is given")

        self.label_id = label_id
        self.is_empty = is_empty
        self.probability = probability
        self.label_source = label_source if label_source is not None else LabelSource()

    @property
    def id_(self) -> ID:
        """Returns the label id."""
        return self.label_id

    def __repr__(self):
        """String representation of the label."""
        return (
            f"ScoredLabel(label_id={self.label_id}, is_empty={self.is_empty}, probability={self.probability}, "
            f"label_source={self.label_source})"
        )

    def __eq__(self, other: object) -> bool:
        """Checks if the label is equal to the other label."""
        if isinstance(other, ScoredLabel):
            return (
                self.label_id == other.label_id
                and self.is_empty == other.is_empty
                and self.probability == other.probability
                and self.label_source == other.label_source
            )
        return False

    def __hash__(self):
        """Returns hash of the label."""
        return hash(str(self))
