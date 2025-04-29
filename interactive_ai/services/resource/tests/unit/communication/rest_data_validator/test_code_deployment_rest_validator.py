# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import jsonschema
import pytest

from communication.rest_data_validator import CodeDeploymentRESTValidator


@pytest.fixture
def fxt_code_deployment_rest_model_identifiers(fxt_optimized_model_1, fxt_optimized_model_2):
    yield {
        "models": [
            {
                "model_id": fxt_optimized_model_1.id_,
                "model_group_id": fxt_optimized_model_1.model_storage.id_,
            },
            {
                "model_id": fxt_optimized_model_2.id_,
                "model_group_id": fxt_optimized_model_2.model_storage.id_,
            },
        ]
    }


@pytest.fixture
def fxt_code_deployment_rest_model_identifiers_missing_model_id(fxt_optimized_model_1, fxt_optimized_model_2):
    yield {
        "models": [
            {"model_group_id": fxt_optimized_model_1.model_storage.id_},
            {
                "model_id": fxt_optimized_model_2.id_,
                "model_group_id": fxt_optimized_model_2.model_storage.id_,
            },
        ]
    }


@pytest.fixture
def fxt_code_deployment_rest_model_identifiers_missing_model_group_id(fxt_optimized_model_1, fxt_optimized_model_2):
    yield {
        "models": [
            {
                "model_id": fxt_optimized_model_2.id_,
            },
            {
                "model_id": fxt_optimized_model_2.id_,
                "model_group_id": fxt_optimized_model_2.model_storage.id_,
            },
        ]
    }


class TestCodeDeploymentRestValidator:
    def test_validate_code_deployment_rest_success(
        self,
        fxt_code_deployment_rest_model_identifiers,
        fxt_segmentation_label_schema_factory,
        fxt_annotation_scene_rest_request,
        fxt_image_identifier_1,
    ) -> None:
        CodeDeploymentRESTValidator().validate_code_deployment(data=fxt_code_deployment_rest_model_identifiers)

    def test_validate_code_deployment_rest_missing_model_id(
        self, fxt_code_deployment_rest_model_identifiers_missing_model_id
    ) -> None:
        with pytest.raises(jsonschema.exceptions.ValidationError):
            CodeDeploymentRESTValidator().validate_code_deployment(
                data=fxt_code_deployment_rest_model_identifiers_missing_model_id
            )

    def test_validate_code_deployment_rest_missing_model_group_id(
        self, fxt_code_deployment_rest_model_identifiers_missing_model_group_id
    ) -> None:
        with pytest.raises(jsonschema.exceptions.ValidationError):
            CodeDeploymentRESTValidator().validate_code_deployment(
                data=fxt_code_deployment_rest_model_identifiers_missing_model_group_id
            )
