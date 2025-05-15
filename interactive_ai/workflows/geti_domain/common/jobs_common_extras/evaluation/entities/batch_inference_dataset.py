# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from dataclasses import dataclass, field

from iai_core.entities.dataset_storage import DatasetStorage
from iai_core.entities.datasets import Dataset, DatasetPurpose
from iai_core.entities.evaluation_result import EvaluationPurpose, EvaluationResult


@dataclass
class BatchInferenceDataset:
    """
    Container for dataset-related information used for a batch inference job.

    :param dataset_storage: Storage containing the datasets.
    :param input_dataset: Dataset to use as input for the inference.
        This dataset will be overwritten with the inference output one in the DB
        (same ID), however there is no guarantee on the in-memory Dataset object
        pointed by this field at the end of the operation, as it could be stale.
        If you need the updated Dataset, use field 'output_dataset' instead.
    :param annotated_dataset: Equivalent of the Dataset used for inference, but with
        annotations; typically, this exists only for evaluation.
    :param output_dataset_purpose: Purpose to set in the output dataset after inference.
    :param evaluation_result: If the inference deals with result sets (e.g. evaluation),
        pre-created EvaluationResult object where to write the results.
    :param evaluation_purpose: If the inference modifies the evaluation result, purpose to set in it.
    :param output_dataset: This field can be used after the inference to retrieve
        an up-to-date Dataset in-memory object. This field should not be used or
        initialized until the inference operation is complete.
    """

    dataset_storage: DatasetStorage
    input_dataset: Dataset
    output_dataset_purpose: DatasetPurpose
    evaluation_purpose: EvaluationPurpose | None = None
    annotated_dataset: Dataset | None = None
    evaluation_result: EvaluationResult | None = field(default=None, init=False)
    output_dataset: Dataset | None = field(default=None, init=False)

    def __post_init__(self):
        """
        Validate inputs and raise errors if values are inconsistent
        """
        if self.output_dataset_purpose == DatasetPurpose.EVALUATION:
            if self.annotated_dataset is None:
                raise ValueError("annotated_dataset is required for validation")
            if self.evaluation_purpose is None:
                raise ValueError("evaluation_purpose is required for validation")
