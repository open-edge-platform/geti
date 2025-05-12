# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains Model-related utility functions for job creation"""

import logging

from geti_types import ID, ProjectIdentifier
from iai_core.entities.evaluation_result import EvaluationPurpose
from iai_core.entities.model import Model, ModelDeprecationStatus, NullModel
from iai_core.entities.model_storage import ModelStorage
from iai_core.repos import EvaluationResultRepo, ModelRepo
from iai_core.repos.model_repo import ModelStatusFilter

logger = logging.getLogger(__name__)


def select_input_model(
    model_storage: ModelStorage,
    from_scratch: bool,
    current_task_label_schema_id: ID | None = None,
) -> Model | None:
    """
    Returns the latest trainable (i.e. non-optimized) model from the model_storage,
    unless training from scratch.

    :param model_storage: ModelStorage to fetch the latest model checkpoint from
    :param from_scratch: True to train from scratch, False to continue from previous
        model checkpoint (if any)
    :param current_task_label_schema_id: Optional, ID of the current label schema for
        the task relative to the model. In case of mismatch with the label schema ID
        stored in the latest model fetched from the repo, then a log message will
        be emitted
    :return: None if training from scratch or if no previous model checkpoint exists.
        Otherwise, the latest trained (and trainable) model.
    """
    if from_scratch:  # explicit request to train from scratch
        return None

    model = ModelRepo(model_storage.identifier).get_latest(
        model_status_filter=ModelStatusFilter.IMPROVED,
        include_optimized_models=False,
    )
    if isinstance(model, NullModel):
        return None

    if model.model_deprecation_status == ModelDeprecationStatus.OBSOLETE:
        logger.info(
            "While looking for a previous model to use as input for training, one was "
            "found in storage `%s`, but it is marked as obsolete; therefore, the model "
            "will not be used and training will be from scratch.",
            model_storage.id_,
        )
        return None

    if (
        current_task_label_schema_id and current_task_label_schema_id != model.configuration.label_schema_id
    ):  # previous model found, but trained with a different schema
        logger.info(
            "While looking for a previous model to use as input for training, one was "
            "found in storage `%s`, but it was trained with a different label schema "
            "revision (`%s`) from the current one (`%s`); the training policy will be "
            "'Class-incremental learning' for this task.",
            model_storage.id_,
            model.configuration.label_schema_id,
            current_task_label_schema_id,
        )

    return model


def get_model_accuracy(model: Model, project_identifier: ProjectIdentifier, purpose: EvaluationPurpose) -> float:
    """
    Retrieve the accuracy value of a model which has been previously evaluated
    on a dataset with a certain purpose.

    :param model: Model for which to get the accuracy
    :param project_identifier: Identifier of the project containing the evaluation
    :param purpose: Purpose of the evaluation
    :return: Accuracy as a float in range [0,1]
    """
    accuracy: float = 0.0
    equivalent_model_ids = ModelRepo(model.model_storage_identifier).get_all_equivalent_model_ids(model=model)
    evaluation_result = EvaluationResultRepo(project_identifier).get_latest_by_model_ids(
        equivalent_model_ids=equivalent_model_ids,
        purpose=purpose,
    )
    if evaluation_result.has_score_metric() and evaluation_result.performance is not None:
        accuracy = evaluation_result.performance.score.value
    else:
        logger.warning(
            "Cannot retrieve the performance from the %s evaluation result of the model with ID '%s'; assuming 0.0.",
            purpose.name,
            model.id_,
        )
    return accuracy
