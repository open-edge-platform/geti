# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from typing import TYPE_CHECKING

from behave import step
from behave.runner import Context

if TYPE_CHECKING:
    from geti_client import ModelsApi


@step("a model of type '{expected_model_type}' exists")
def step_then_a_model_exists(context: Context, expected_model_type: str):
    models_api: ModelsApi = context.models_api
    model_groups = models_api.get_model_groups(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        project_id=context.project_id,
    )

    matching_model_groups = [
        model_group for model_group in model_groups.model_groups if model_group.model_template_id == expected_model_type
    ]

    assert len(matching_model_groups) == 1, (
        f"There must be exactly one model group with the expected architecture '{expected_model_type}', found {len(matching_model_groups)} model groups."  # noqa: E501
    )

    context.model_storage_info = matching_model_groups[0]
    context.model_storage_id = context.model_storage_info.id

    models = sorted(context.model_storage_info.models, key=lambda model: model.version, reverse=True)

    assert len(matching_model_groups) > 0, "There must be at least one model in the model group."

    context.model_id = models[0].id
    context.model_info = models_api.get_model_detail(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        project_id=context.project_id,
        model_group_id=context.model_storage_id,
        model_id=context.model_id,
    )
