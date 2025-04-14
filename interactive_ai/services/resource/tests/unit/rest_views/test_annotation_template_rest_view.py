# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from testfixtures import compare

from communication.rest_views.annotation_template_rest_views import AnnotationTemplateRESTViews

from geti_types import ID
from sc_sdk.entities.annotation_template import AnnotationTemplate


class TestAnnotationTemplateRESTViews:
    def test_annotation_template_to_rest(self) -> None:
        annotation_template = AnnotationTemplate(
            id_=ID("test_id"),
            name="test_annotation_template",
            value="test_value",
        )
        result = AnnotationTemplateRESTViews.annotation_template_to_rest(annotation_template=annotation_template)
        annotation_template_rest = {
            "id": ID("test_id"),
            "name": "test_annotation_template",
            "value": "test_value",
        }
        compare(result, annotation_template_rest, ignore_eq=True)

    def test_annotation_template_from_rest(self) -> None:
        annotation_template_rest = {
            "id": ID("test_id"),
            "name": "test_annotation_template",
            "value": "test_value",
        }
        result = AnnotationTemplateRESTViews.annotation_template_from_rest(data=annotation_template_rest)
        annotation_template = AnnotationTemplate(
            id_=ID("test_id"),
            name="test_annotation_template",
            value="test_value",
        )
        assert result == annotation_template
