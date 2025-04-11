# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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
