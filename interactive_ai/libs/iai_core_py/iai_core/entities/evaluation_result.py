# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the EvaluationResult entity"""

import datetime
from enum import Enum, auto

from iai_core.entities.datasets import Dataset
from iai_core.entities.metrics import NullPerformance, Performance
from iai_core.entities.model import Model
from iai_core.entities.model_storage import ModelStorageIdentifier
from iai_core.utils.time_utils import now

from geti_types import ID, DatasetStorageIdentifier, PersistentEntity, ProjectIdentifier


class EvaluationPurpose(Enum):
    """
    This defines the purpose of the EvaluationResult.

    VALIDATION      generated at Evaluation stage on validation subset of training dataset
    TEST            generated at Evaluation stage on test subset of training dataset
    PREEVALUATION   generated during the Preevaluation stage (i.e., using a previously trained model version) on a
                    validation subset of the training dataset.
    MODEL_TEST      evaluation generated on test (non-training) datasets
    """

    VALIDATION = auto()  # TODO: CVS-127330 migrate from "EVALUATION" to "VALIDATION"
    TEST = auto()
    PREEVALUATION = auto()
    MODEL_TEST = auto()


class EvaluationResult(PersistentEntity):
    """
    Represents the end result of the evaluation process. Specifically, this entity is responsible for linking:
    - the ground truth dataset with its corresponding prediction dataset;
    - the model with the computed predictions and performance on the dataset.

    :param id_: ID of the evaluation result
    :param project_identifier: identifier of the project containing the evaluation result
    :param model_storage_id: ID of the model storage containing the model
    :param model_id: ID of the model used
    :param dataset_storage_id: ID of the dataset storage
    :param ground_truth_dataset: The dataset or ID of the dataset containing ground truth annotations
    :param prediction_dataset: The dataset or ID of the dataset containing the predictions
    :param purpose: see :class:`EvaluationPurpose`
    :param performance: the performance of the model on the ground truth dataset
    :param creation_date: the timestamp when the evaluation result was created
    :param ephemeral: True if the instance exists only in memory, False otherwise
    """

    def __init__(  # noqa: PLR0913
        self,
        id_: ID,
        project_identifier: ProjectIdentifier,
        model_storage_id: ID,
        model_id: ID,
        dataset_storage_id: ID,
        ground_truth_dataset: ID | Dataset,
        prediction_dataset: ID | Dataset,
        purpose: EvaluationPurpose = EvaluationPurpose.VALIDATION,
        performance: Performance | None = None,
        creation_date: datetime.datetime | None = None,
        ephemeral: bool = True,
    ) -> None:
        super().__init__(id_=id_, ephemeral=ephemeral)
        self.project_identifier = project_identifier
        self.model_storage_id = model_storage_id
        self.model_id = model_id
        self.dataset_storage_id = dataset_storage_id
        if isinstance(ground_truth_dataset, ID):
            self.ground_truth_dataset_id = ground_truth_dataset
            self._ground_truth_dataset = None
        if isinstance(ground_truth_dataset, Dataset):
            self.ground_truth_dataset_id = ground_truth_dataset.id_
            self._ground_truth_dataset = ground_truth_dataset

        if isinstance(prediction_dataset, ID):
            self.prediction_dataset_id = prediction_dataset
            self._prediction_dataset = None
        if isinstance(prediction_dataset, Dataset):
            self.prediction_dataset_id = prediction_dataset.id_
            self._prediction_dataset = prediction_dataset

        self.purpose = purpose
        self.performance = performance
        self._creation_date = creation_date if creation_date is not None else now()

    @property
    def creation_date(self) -> datetime.datetime:
        """Returns the creation date of the evaluation result."""
        return self._creation_date

    @property
    def prediction_dataset(self) -> Dataset:
        """Returns the prediction dataset"""
        if self._prediction_dataset is None:
            self._prediction_dataset = self.__dataset(self.prediction_dataset_id)
        return self._prediction_dataset

    @property
    def ground_truth_dataset(self) -> Dataset:
        """Returns the ground truth dataset"""
        if self._ground_truth_dataset is None:
            self._ground_truth_dataset = self.__dataset(self.ground_truth_dataset_id)
        return self._ground_truth_dataset

    def has_score_metric(self) -> bool:
        """Returns True if the evaluation result contains non-null performance and score value."""
        return self.performance is not None and not isinstance(self.performance, NullPerformance)

    def get_model(self) -> Model:
        """Returns the model used to generate this evaluation result."""
        from iai_core.repos.model_repo import ModelRepo

        model_storage_identifier = ModelStorageIdentifier(
            workspace_id=self.project_identifier.workspace_id,
            project_id=self.project_identifier.project_id,
            model_storage_id=self.model_storage_id,
        )
        return ModelRepo(model_storage_identifier).get_by_id(self.model_id)

    def __dataset(self, dataset_id: ID) -> Dataset:
        from iai_core.repos.dataset_repo import DatasetRepo

        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=self.project_identifier.workspace_id,
            project_id=self.project_identifier.project_id,
            dataset_storage_id=self.dataset_storage_id,
        )
        return DatasetRepo(dataset_storage_identifier).get_by_id(dataset_id)

    def __repr__(self):
        """String representation of the evaluation result."""
        return (
            f"{type(self).__name__}("
            f"model_id={self.model_id}, "
            f"ground_truth_dataset_id={self.ground_truth_dataset_id}, "
            f"prediction_dataset_id={self.prediction_dataset_id}, "
            f"purpose={self.purpose}, "
            f"performance={self.performance}, "
            f"creation_date={self.creation_date}, "
            f"id={self.id_})"
        )


class NullEvaluationResult(EvaluationResult):
    """Representation of a EvaluationResult 'EvaluationResult not found'"""

    def __init__(self) -> None:
        super().__init__(
            id_=ID(),
            project_identifier=ProjectIdentifier(workspace_id=ID(), project_id=ID()),
            model_storage_id=ID(),
            model_id=ID(),
            dataset_storage_id=ID(),
            ground_truth_dataset=ID(),
            prediction_dataset=ID(),
            creation_date=datetime.datetime.min,
            ephemeral=False,
        )
