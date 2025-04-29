# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from dataclasses import dataclass

# Value to use for accuracy when it is not well-defined (e.g. division by zero)
UNDEFINED_ACCURACY_VALUE = 1.0


@dataclass
class AccuracyCounters:
    """
    Container for intermediate information necessary to compute the 'accuracy' score.

    :var tp: number of true positives
    :var tn: number of true negatives
    :var fp: number of false positives
    :var fn: number of false negatives
    """

    tp: int = 0
    tn: int = 0
    fp: int = 0
    fn: int = 0

    @property
    def num_positive(self) -> int:
        """
        Number of instances classified as 'positive' (condition present) by the model
        """
        return self.tp + self.fp

    @property
    def num_negative(self) -> int:
        """
        Number of instances classified as 'negative' (condition absent) by the model
        """
        return self.tn + self.fn

    @property
    def num_true(self) -> int:
        """
        Number of instances classified correctly by the model (ground truth matches)
        """
        return self.tp + self.tn

    @property
    def num_false(self) -> int:
        """
        Number of instances misclassified correctly by the model (ground truth does not match)
        """
        return self.fp + self.fn

    @property
    def num_total(self) -> int:
        """
        Total number of instances
        """
        return self.tp + self.tn + self.fp + self.fn

    @property
    def accuracy(self) -> float:
        """
        Accuracy score

        Reference: https://en.wikipedia.org/wiki/Accuracy_and_precision
        """
        if self.num_total == 0:
            return UNDEFINED_ACCURACY_VALUE

        return self.num_true / self.num_total

    @property
    def precision(self) -> float:
        """
        Precision score, defined as true positives divided by the sum of true positives and false positives.

        reference: https://en.wikipedia.org/wiki/Precision_and_recall
        """
        if self.tp + self.fp + self.fn == 0:
            # if the true positives, false positives and false negatives are all 0, the precision is 1.
            return 1.0
        if self.tp == 0:
            # if true positives are 0 and at least one of the two other counters is larger than 0, precision l is 0.
            return 0.0

        return self.tp / (self.tp + self.fp)

    @property
    def recall(self) -> float:
        """
        Recall score, defined as true positives divided by the sum of true positives and false negatives.

        reference: https://en.wikipedia.org/wiki/Precision_and_recall
        """
        if self.tp + self.fp + self.fn == 0:
            # if the true positives, false positives and false negatives are all 0, the recall is 1.
            return 1.0
        if self.tp == 0:
            # if true positives are 0 and at least one of the two other counters is larger than 0, the recall is 0.
            return 0.0

        return self.tp / (self.tp + self.fn)

    @property
    def positives(self) -> "AccuracyCounters":
        """
        Get a view object containing the same positive (TP, FP) values of this one,
        but no negative (TN, FN) ones.
        """
        return AccuracyCounters(
            tp=self.tp,
            fp=self.fp,
            tn=0,
            fn=0,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AccuracyCounters):
            return False
        return self.tp == other.tp and self.tn == other.tn and self.fp == other.fp and self.fn == other.fn

    def __add__(self, other: object):
        if not isinstance(other, AccuracyCounters):
            raise ValueError(f"Cannot add `AccuracyCounters` and `{type(other)}`")
        return AccuracyCounters(
            tp=(self.tp + other.tp),
            tn=(self.tn + other.tn),
            fp=(self.fp + other.fp),
            fn=(self.fn + other.fn),
        )
