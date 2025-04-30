# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
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

from typing import TYPE_CHECKING

from behave import then, when
from behave.runner import Context

if TYPE_CHECKING:
    from geti_client import ModelsApi, OptimizeJob


def _optimize(context: Context) -> None:
    models_api: ModelsApi = context.models_api

    optimize_response = models_api.optimize_model(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        project_id=context.project_id,
        model_group_id=context.model_storage_id,
        model_id=context.model_id,
    )
    context.job_id = optimize_response.job_id


@when("the user requests to optimize a model")
def step_when_user_optimizes_model(context: Context) -> None:
    _optimize(context=context)


@when("the user tries to optimize a model")
def step_when_user_tries_optimizing_model(context: Context) -> None:
    try:
        _optimize(context=context)
    except Exception as e:
        context.exception = e


@then(
    "a model of type '{expected_model_type}' and optimization type '{expected_optimization_type}' is created"
)
def step_then_model_created(
    context: Context, expected_model_type: str, expected_optimization_type: str
):
    optimize_job_info: OptimizeJob = context.job_info.actual_instance

    context.model_storage_id = optimize_job_info.metadata.model_storage_id
    context.model_id = optimize_job_info.metadata.optimized_model_id

    models_api: ModelsApi = context.models_api
    context.model_storage_info = models_api.get_model_group(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        project_id=context.project_id,
        model_group_id=context.model_storage_id,
    )
    context.model_info = models_api.get_model_detail(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        project_id=context.project_id,
        model_group_id=context.model_storage_id,
        model_id=context.model_id,
    )

    optimization_model_type = context.model_storage_info.model_template_id
    optimized_models = context.model_info.optimized_models
    optimization_types = {model.optimization_type for model in optimized_models}
    assert optimization_model_type == expected_model_type, (
        f"The optimized model does not have the expected architecture (expected '{expected_model_type}', found '{optimization_model_type}')"
    )
    assert expected_optimization_type in optimization_types, (
        f"The optimized model does not have the expected optimization type (expected '{expected_optimization_type}', found '{optimization_types}'"
    )
