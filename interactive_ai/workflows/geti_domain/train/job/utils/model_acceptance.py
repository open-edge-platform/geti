# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module contains utility functions for model acceptance, that is the process of
determining whether a newly trained model should be accepted or rejected.
"""

import logging

import numpy as np
import scipy
from geti_types import ProjectIdentifier
from iai_core.entities.datasets import Dataset
from iai_core.entities.evaluation_result import EvaluationPurpose
from iai_core.entities.model import Model, NullModel
from jobs_common.jobs.helpers.model_helpers import get_model_accuracy

logger = logging.getLogger(__name__)

ZTEST_ACCEPTANCE_THRESHOLD = 0.05


def proportions_ztest(  # noqa: ANN201
    previous_performance: float,
    new_performance: float,
    num_validation_images: int,
):
    """
    Re-implementation of statsmodels.stats.proportion.proportions_ztest
    from statsmodels package using only scipy.

    The implementation is made specific for model acceptance policies and only
    implements the 'smaller' alternative hypothesis from
    statsmodels.stats.proportion.proportions_ztest

    :param previous_performance: performance of previous model as a float in range [0,1]
    :param new_performance: performance of new model as a float in range [0,1]
    :param num_validation_images: number of validation images used to compute the performances
    :return: proportions Z-test score in range [0,1]
    """
    if not 0 <= previous_performance <= 1:
        raise ValueError("previous_performance should be in range [0, 1]")
    if not 0 <= new_performance <= 1:
        raise ValueError("new_performance should be in range [0, 1]")
    if num_validation_images < 1:
        raise ValueError("num_validation_images should be >= 1")

    if new_performance == previous_performance:
        # fast path when the performance didn't change.
        # It also prevents NaN at (0,0) and (1,1)
        return 0.5

    # the variable names are adapted from statsmodels
    diff = new_performance - previous_performance

    p_pooled = (previous_performance + new_performance) / 2

    nobs_fact = 2.0 / num_validation_images
    var_ = p_pooled * (1 - p_pooled) * nobs_fact
    std_diff = np.sqrt(var_)

    # alternative hypothesis is 'smaller'
    return scipy.stats.norm.cdf(diff / std_diff)


def is_model_acceptable(
    new_model: Model,
    old_model: Model | None,
    project_identifier: ProjectIdentifier,
    validation_dataset: Dataset,
) -> bool:
    """
    Check if a new model should be accepted or rejected based on its performance
    and other considerations relative to the previous models.

    In case of lower performance w.r.t. the previously trained model, the statistical
    significance of this drop is assessed through the "proportion Z-test": only
    significantly worse models (p <= 0.5) are rejected.
    The Z-test takes into account both the performance value and the size of the
    validation dataset on which the statistic is computed.

    Summarizing, a model is accepted if any of these conditions is satisfied:
     - perf_new > perf_old (better)
     - p-value of Z-test > 0.05 (not significantly worse)
     - no previous revision exists (first training or from scratch)
     - label schema has changed
     - model architecture has changed

    :param new_model: new trained model, used in the evaluation stage
    :param old_model: old trained model, used in the pre-evaluation stage.
        A value of NullModel means that 'new_model' is the first trained model.
    :param project_identifier: project which contains the evaluation result of the models to compare.
    :param validation_dataset: Validation dataset used for the comparison
    :return: boolean indicating if the new model is not worse than the old one,
        i.e. the validation accuracy has not decreased after training.
    """
    if isinstance(new_model, NullModel):
        raise ValueError("Attempted to check for improvement on a NullModel")

    # If there is no previous model, then the training is either the first one or
    # from scratch. In both cases, the new model can be accepted.
    if old_model is None or isinstance(old_model, NullModel):
        logger.info(
            "Model `%s` is acceptable because there is no old model to compare it with",
            new_model.id_,
        )
        return True

    # If the label schema has changed, the new model can be accepted unconditionally
    if new_model.label_schema_id != old_model.label_schema_id:
        logger.info(
            "Model `%s` is acceptable because the old model has different labels",
            new_model.id_,
        )
        return True

    # If the model arch has changed, the new model can be accepted unconditionally
    new_model_template = new_model.model_storage.model_template.model_template_id
    old_model_template = old_model.model_storage.model_template.model_template_id
    if new_model_template != old_model_template:
        logger.info(
            "Model `%s` is acceptable because the old model has different architecture",
            new_model.id_,
        )
        return True

    # Get the accuracy of both models on the latest validation set.
    old_model_accuracy = get_model_accuracy(
        model=old_model,
        project_identifier=project_identifier,
        purpose=EvaluationPurpose.PREEVALUATION,
    )
    new_model_accuracy = get_model_accuracy(
        model=new_model,
        project_identifier=project_identifier,
        purpose=EvaluationPurpose.VALIDATION,
    )

    is_acceptable: bool
    decision_msg: str
    if new_model_accuracy >= old_model_accuracy:
        is_acceptable = True
        decision_msg = "the new accuracy is greater than or equal to the old one"
    else:
        p_value = proportions_ztest(
            previous_performance=old_model_accuracy,
            new_performance=new_model_accuracy,
            num_validation_images=len(validation_dataset),
        )
        if p_value > ZTEST_ACCEPTANCE_THRESHOLD:
            is_acceptable = True
            decision_msg = (
                f"although the new accuracy is lower, the delta is not statistically "
                f"significant to reject the model (p-value = {p_value:.3f})"
            )
        else:
            is_acceptable = False
            decision_msg = f"the new accuracy is significantly worse (p-value = {p_value:.3f})"
    logger.info(
        "Compared the new model (ID %s) versus the old one (ID %s) based on their "
        "accuracy (new %.3f vs %.3f old) on a validation dataset of %d elements: "
        "the new model can %s be accepted because %s.",
        new_model.id_,
        old_model.id_,
        new_model_accuracy,
        old_model_accuracy,
        len(validation_dataset),
        "NOT" if not is_acceptable else "",
        decision_msg,
    )
    return is_acceptable
