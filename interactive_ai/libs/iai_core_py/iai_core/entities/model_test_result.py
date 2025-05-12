# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the ModelTestResult entity"""

import logging
from datetime import datetime
from enum import Enum, IntEnum, auto

from iai_core.entities.dataset_storage import DatasetStorage
from iai_core.entities.datasets import Dataset
from iai_core.entities.evaluation_result import EvaluationPurpose, EvaluationResult
from iai_core.entities.metrics import MultiScorePerformance, NullPerformance, ScoreMetric

from geti_types import ID, ProjectIdentifier

logger = logging.getLogger(__name__)


# TODO: remove after cleanup CVS-124942
class MetricType(Enum):
    F_MEASURE = auto()
    ACCURACY = auto()
    DICE = auto()


class TestState(IntEnum):
    # Model testing job is created but not yet started
    PENDING = auto()
    # Annotated dataset being created for testing
    CREATING_DATASET = auto()
    # Inferring on dataset
    INFERRING = auto()
    # Computing the score based on the annotated and inferred dataset
    EVALUATING = auto()
    # Model test is successfully populated with scores
    DONE = auto()
    # Model testing failed
    FAILED = auto()
    # Model testing resulted in error
    ERROR = auto()


class ModelTestResult(EvaluationResult):
    """
    Entity used to represent a user-triggered model test.

    :param id_: ID of the test.
    :param name: name of the test
    :param project_identifier: identifier of the project containing the model test result
    :param model_storage_id: ID of the model storage containing the model
    :param model_id: ID of the model used
    :param dataset_storage_ids: list of IDs of the dataset storages to which the dataset are created from.
        Note: multiple dataset storages is not fully supported yet, hence only the first one is used.
    :param state: state of the test (pending, inferring, evaluating, done)
    :param job_id: the ID of the job computing the model test result
    :param ground_truth_dataset: The dataset or ID of the dataset with the ground truth dataset used for evaluation
    :param prediction_dataset: The dataset or ID of the dataset with the prediction dataset used for evaluation
    :param performance: (optional) performance with list of scores for different metrics after evaluation.
        If not specified, it is instantiated as an empty MultiScorePerformance object.
    :param creation_date: time of creation of the test
    :param ephemeral: Boolean to mark whether the ModelTestResult instance has been persisted in the database or not
    """

    def __init__(
        self,
        id_: ID,
        name: str,
        project_identifier: ProjectIdentifier,
        model_storage_id: ID,
        model_id: ID,
        dataset_storage_ids: list[ID],
        state: TestState = TestState.PENDING,
        ground_truth_dataset: ID | Dataset = ID(),
        prediction_dataset: ID | Dataset = ID(),
        job_id: ID | None = None,
        performance: MultiScorePerformance | None = None,
        creation_date: datetime | None = None,
        ephemeral: bool = True,
    ) -> None:
        super().__init__(
            id_=id_,
            project_identifier=project_identifier,
            model_storage_id=model_storage_id,
            model_id=model_id,
            dataset_storage_id=dataset_storage_ids[0],
            ground_truth_dataset=ground_truth_dataset,
            prediction_dataset=prediction_dataset,
            purpose=EvaluationPurpose.MODEL_TEST,
            creation_date=creation_date,
            ephemeral=ephemeral,
        )
        self._name = name
        self.dataset_storage_ids = dataset_storage_ids
        self.state = state
        self.job_id = job_id
        self.performance: MultiScorePerformance = (
            performance
            if performance is not None and not isinstance(performance, NullPerformance)
            else MultiScorePerformance()
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def scores(self) -> list[ScoreMetric]:
        if isinstance(self.performance, MultiScorePerformance):
            return self.performance.scores
        logger.warning(
            "Unrecognized performance of type '%s' for model test with ID '%s'. Returning empty scores list.",
            type(self.performance),
            self.id_,
        )
        return []

    def get_dataset_storages(self) -> list[DatasetStorage]:
        from iai_core.repos.dataset_storage_repo import DatasetStorageRepo

        ds_repo = DatasetStorageRepo(self.project_identifier)
        return [ds_repo.get_by_id(ds_id) for ds_id in self.dataset_storage_ids]

    def append_score(self, score: ScoreMetric):
        self.performance.add_score(score)

    def __repr__(self) -> str:
        return (
            f"ModelTestResult({self.id_}, name='{self.name}', model='{self.model_id}', "
            f"dataset_storages='{self.dataset_storage_ids}', job_id='{self.job_id}', state={self.state}, "
            f"scores='{self.scores}')"
        )

    def __eq__(self, other):
        if isinstance(other, ModelTestResult):
            return (
                self.id_ == other.id_
                and self.name == other.name
                and self.model_storage_id == other.model_storage_id
                and self.model_id == other.model_id
                and set(self.dataset_storage_ids) == set(other.dataset_storage_ids)
                and self.job_id == other.job_id
                and self.ground_truth_dataset_id == other.ground_truth_dataset_id
                and self.prediction_dataset_id == other.prediction_dataset_id
                and self.state == other.state
                and self.scores == other.scores
            )


class NullModelTestResult(ModelTestResult):
    """Representation of a 'ModelTestResult not found'"""

    def __init__(self) -> None:
        super().__init__(
            id_=ID(),
            name="",
            project_identifier=ProjectIdentifier(workspace_id=ID(), project_id=ID()),
            model_storage_id=ID(),
            model_id=ID(),
            dataset_storage_ids=[ID()],
            job_id=None,
            ephemeral=False,
        )

    def __repr__(self) -> str:
        return "NullModelTestResult()"
