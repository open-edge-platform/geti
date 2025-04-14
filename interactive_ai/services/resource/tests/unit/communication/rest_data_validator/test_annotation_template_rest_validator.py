# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from jsonschema.exceptions import ValidationError

from communication.rest_data_validator.annotation_template_rest_validator import AnnotationTemplateRestValidator


@pytest.fixture
def fxt_annotation_template_valid():
    yield {"name": "Valid Name", "value": "Valid Value"}


@pytest.fixture
def fxt_annotation_template_invalid_name():
    yield {"name": "", "value": "Valid Value"}


@pytest.fixture
def fxt_annotation_template_invalid_value():
    yield {"name": "Valid Name", "value": ""}


class TestAnnotationRestValidator:
    def test_validate_annotation_template_success(
        self,
        fxt_annotation_template_valid,
    ) -> None:
        """Test validate_annotation_template with a valid input"""

        AnnotationTemplateRestValidator().validate_annotation_template(
            annotation_template_rest=fxt_annotation_template_valid,
        )

    def test_validate_annotation_template_invalid_name(
        self,
        fxt_annotation_template_invalid_name,
    ) -> None:
        """Test validate_annotation_template with an invalid name"""
        with pytest.raises(ValidationError):
            AnnotationTemplateRestValidator().validate_annotation_template(
                annotation_template_rest=fxt_annotation_template_invalid_name,
            )

    def test_validate_annotation_template_invalid_value(
        self,
        fxt_annotation_template_invalid_value,
    ) -> None:
        """Test validate_annotation_template with an invalid value"""
        with pytest.raises(ValidationError):
            AnnotationTemplateRestValidator().validate_annotation_template(
                annotation_template_rest=fxt_annotation_template_invalid_value,
            )
