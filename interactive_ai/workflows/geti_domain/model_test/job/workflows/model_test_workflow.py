# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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
"""
Optimize workflow
"""

from typing import Optional

from flytekit import workflow

from job.tasks.model_testing import run_model_test


@workflow
def model_test_workflow(
    project_id: str,
    model_test_result_id: str,
    is_local_anomaly_test: bool,
    min_annotation_size: Optional[int] = None,  # noqa: UP007
    max_number_of_annotations: Optional[int] = None,  # noqa: UP007
) -> None:
    """
    Runs a model testing workflow

    :param project_id: ID of the project
    :param model_test_result_id: ID of the model test result
    :param is_local_anomaly_test: set to True to only use media that are fully annotated
     for the corresponding task (which the model is trained for)
    :param min_annotation_size: Minimum size of an annotation in pixels. Any annotation smaller than this will be
     ignored during evaluation
    :param max_number_of_annotations: Maximum number of annotation allowed in one annotation scene. If exceeded, the
     annotation scene will be ignored during evaluation.
    """
    run_model_test(
        project_id=project_id,
        model_test_result_id=model_test_result_id,
        is_local_anomaly_test=is_local_anomaly_test,
        min_annotation_size=min_annotation_size,
        max_number_of_annotations=max_number_of_annotations,
    )
