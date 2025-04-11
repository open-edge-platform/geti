# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.
"""This module tests model acceptance utils"""

import copy
from unittest.mock import patch

import pytest
from sc_sdk.entities.evaluation_result import EvaluationPurpose
from sc_sdk.entities.model import NullModel

from job.utils.model_acceptance import is_model_acceptable, proportions_ztest


@pytest.mark.JobsComponent
class TestModelAcceptance:
    @pytest.mark.parametrize(
        "previous_performance, new_performance, num_validation_images, exp_pvalue",
        [
            (0.0, 0.0, 4, 0.5),
            (0.3, 0.3, 4, 0.5),
            (0.4, 0.6, 10, 0.814),
            (0.6, 0.4, 10, 0.186),
            (0.8, 0.9, 15, 0.778),
            (0.0, 1.0, 20, 1.0),
            (1.0, 0.0, 20, 0.0),
            (1.0, 1.0, 25, 0.5),
        ],
    )
    def test_proportions_ztest(self, previous_performance, new_performance, num_validation_images, exp_pvalue) -> None:
        """
        The scipy reimplementation of proportions_ztest must be equivalent to
        the statsmodels.stats.proportion.proportions_ztest according to the formula:

        proportions_ztest(
            (new_perf * n_val, prev_perf * n_val),
            (n_val, n_val),
            alternative="smaller"
        )[1]
        """
        tolerance = 0.01

        # Act
        pvalue = proportions_ztest(previous_performance, new_performance, num_validation_images)

        # Assert
        assert abs(pvalue - exp_pvalue) < tolerance

    @pytest.mark.parametrize(
        "old_model_accuracy, new_model_accuracy, old_model_arch, new_model_arch, should_accept",
        [
            (None, 0.7, "algo1", "algo1", True),
            (0.0, 0.7, "algo1", "algo1", True),
            (0.5, 0.5, "algo1", "algo1", True),
            (0.5, 0.49, "algo1", "algo1", True),
            (0.9, 0.01, "algo1", "algo1", False),
            (0.9, 0.1, "algo1", "algo2", True),
        ],
        ids=[
            "first training",
            "accuracy improved",
            "accuracy unchanged ",
            "accuracy marginally decreased",
            "accuracy substantially decreased",
            "different model architecture",
        ],
    )
    def test_is_model_acceptable(
        self,
        fxt_model,
        fxt_project,
        fxt_dataset_non_empty,
        old_model_accuracy,
        new_model_accuracy,
        old_model_arch,
        new_model_arch,
        should_accept,
    ) -> None:
        def get_model_accuracy_mock(model, project_identifier, purpose) -> float:
            if purpose == EvaluationPurpose.PREEVALUATION:
                return old_model_accuracy
            if purpose == EvaluationPurpose.VALIDATION:
                return new_model_accuracy
            raise ValueError(f"Unexpected purpose {purpose}")

        new_model = fxt_model
        new_model.model_storage.model_template.model_template_id = new_model_arch
        if old_model_accuracy is not None:
            old_model = copy.deepcopy(fxt_model)
            old_model.model_storage.model_template.model_template_id = old_model_arch
        else:
            old_model = NullModel()
        with patch(
            "job.utils.model_acceptance.get_model_accuracy",
            side_effect=get_model_accuracy_mock,
        ):
            accepted = is_model_acceptable(
                new_model=new_model,
                old_model=old_model,
                project_identifier=fxt_project.identifier,
                validation_dataset=fxt_dataset_non_empty,
            )

        assert accepted == should_accept
