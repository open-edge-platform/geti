# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import pytest

from entities.deployment import CodeDeployment, ModelIdentifier
from repos.code_deployment_repo import CodeDeploymentRepo

from geti_types import ID


@pytest.fixture
def fxt_model_identifiers(
    fxt_optimized_model_1_with_exportable_code,
    fxt_optimized_model_2_with_exportable_code,
):
    yield [
        ModelIdentifier(
            model_id=fxt_optimized_model_1_with_exportable_code.id_,
            model_storage_id=fxt_optimized_model_1_with_exportable_code.model_storage.id_,
        ),
        ModelIdentifier(
            model_id=fxt_optimized_model_2_with_exportable_code.id_,
            model_storage_id=fxt_optimized_model_2_with_exportable_code.model_storage.id_,
        ),
    ]


@pytest.fixture
def fxt_code_deployment(fxt_project, fxt_model_identifiers):
    yield CodeDeployment(
        id_=CodeDeploymentRepo.generate_id(),
        creator_id=ID("dummy_user"),
        model_identifiers=fxt_model_identifiers,
    )


@pytest.fixture
def fxt_code_deployment_rest(fxt_code_deployment):
    yield {
        "id": str(fxt_code_deployment.id_),
        "models": [
            {
                "model_id": model_identifier.model_id,
                "model_group_id": model_identifier.model_storage_id,
            }
            for model_identifier in fxt_code_deployment.model_identifiers
        ],
        "progress": fxt_code_deployment.progress,
        "state": fxt_code_deployment.state.name,
        "message": fxt_code_deployment.message,
        "creator_id": fxt_code_deployment.creator_id,
        "creation_time": fxt_code_deployment.creation_time.isoformat(),
    }
