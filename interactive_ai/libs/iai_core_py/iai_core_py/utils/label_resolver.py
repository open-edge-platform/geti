"""
This module is implements label resolution functionality
"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from collections.abc import Sequence

from iai_core_py.entities.label_schema import LabelSchema
from iai_core_py.entities.scored_label import LabelSource, ScoredLabel

from geti_types import ID

logger = logging.getLogger(__name__)


class LabelResolver:
    """
    This class is responsible for working with label hierarchies.
    """

    @staticmethod
    def label_id_to_probability(
        scored_labels: Sequence[ScoredLabel],
    ) -> dict[ID, float]:
        """Converts a list of ScoredLabels to a map Label -> probability"""
        return {scored_label.id_: scored_label.probability for scored_label in scored_labels}

    @staticmethod
    def label_id_to_label_source(
        scored_labels: Sequence[ScoredLabel],
    ) -> dict[ID, LabelSource]:
        """Converts a list of ScoredLabels to a map Label -> LabelSource"""
        return {scored_label.id_: scored_label.label_source for scored_label in scored_labels}

    @staticmethod
    def complete_labels(label_schema: LabelSchema, scored_labels: list[ScoredLabel]) -> list[ScoredLabel]:
        """
        Adds labels that can be inferred from the input. This function is meant to post-process non-probabilistic
        user input so that labels that can be logically inferred are added.

        Steps:

        - add ancestors (all parents) of labels

        :return: list of completed labels
        """
        results_labels = []
        for scored_label in scored_labels:
            results_labels.extend(label_schema.get_ancestors(label=scored_label))  # type: ignore
        results_labels = LabelResolver.__unique_ordered(hashable_list=results_labels)
        # turn into scored labels
        label_id_to_probability = LabelResolver.label_id_to_probability(scored_labels=scored_labels)
        label_id_to_label_source = LabelResolver.label_id_to_label_source(scored_labels=scored_labels)
        result_scored_labels = []
        for label in results_labels:
            result_scored_labels.append(
                ScoredLabel(
                    label_id=label.id_,
                    is_empty=label.is_empty,
                    probability=label_id_to_probability.get(label.id_, 1.0),
                    label_source=label_id_to_label_source.get(label.id_, LabelSource()),
                )
            )

        if {label.id_ for label in result_scored_labels} != {label.id_ for label in scored_labels}:
            logger.info(
                "Some labels were added or removed while completing labels:"
                "label_schema: %s  input_labels: %s  output_labels: %s",
                label_schema,
                scored_labels,
                result_scored_labels,
            )

        return result_scored_labels

    @staticmethod
    def __unique_ordered(hashable_list: list):  # noqa: ANN205
        """
        Makes items in `hashable_list` unique and keeps the original ordering
        """
        todo = set(hashable_list)
        result = []
        for item in hashable_list:
            if item in todo:
                result.append(item)
                todo.remove(item)
        return result
