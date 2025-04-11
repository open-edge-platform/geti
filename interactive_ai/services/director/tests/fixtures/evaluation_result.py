# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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

import pytest

from sc_sdk.entities.evaluation_result import EvaluationResult
from sc_sdk.entities.metrics import Performance, ScoreMetric


@pytest.fixture
def fxt_performance():
    yield Performance(score=ScoreMetric(name="score", value=1))


@pytest.fixture
def fxt_evaluation_result(fxt_ote_id, fxt_performance, fxt_project_identifier):
    yield EvaluationResult(
        id_=fxt_ote_id(0),
        project_identifier=fxt_project_identifier,
        model_storage_id=fxt_ote_id(2),
        model_id=fxt_ote_id(3),
        dataset_storage_id=fxt_ote_id(4),
        ground_truth_dataset=fxt_ote_id(5),
        prediction_dataset=fxt_ote_id(6),
        performance=fxt_performance,
    )
