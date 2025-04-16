# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
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
    min_annotation_size: Optional[int] = None,  # noqa: UP007
    max_number_of_annotations: Optional[int] = None,  # noqa: UP007
) -> None:
    """
    Runs a model testing workflow

    :param project_id: ID of the project
    :param model_test_result_id: ID of the model test result
    :param min_annotation_size: Minimum size of an annotation in pixels. Any annotation smaller than this will be
     ignored during evaluation
    :param max_number_of_annotations: Maximum number of annotation allowed in one annotation scene. If exceeded, the
     annotation scene will be ignored during evaluation.
    """
    run_model_test(
        project_id=project_id,
        model_test_result_id=model_test_result_id,
        min_annotation_size=min_annotation_size,
        max_number_of_annotations=max_number_of_annotations,
    )
