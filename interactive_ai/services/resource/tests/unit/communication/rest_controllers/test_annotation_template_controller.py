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

from unittest.mock import patch

import pytest

from communication.rest_controllers.annotation_template_controller import AnnotationTemplateRESTController

from geti_types import ID, ProjectIdentifier
from sc_sdk.entities.annotation_template import AnnotationTemplate
from sc_sdk.repos.annotation_template_repo import AnnotationTemplateRepo


@pytest.fixture
def fxt_project_identifier():
    yield ProjectIdentifier(
        project_id=ID("test_project_id"),
        workspace_id=ID("test_workspace_id"),
    )


@pytest.fixture
def fxt_annotation_template_1_rest():
    yield {
        "name": "test_name_1",
        "value": "test_value_1",
    }


@pytest.fixture
def fxt_annotation_template_1():
    yield AnnotationTemplate(
        id_=ID("test_id_1"),
        name="test_name_1",
        value="test_value_1",
    )


@pytest.fixture
def fxt_annotation_template_1_mapped():
    yield {
        "id": "test_id_1",
        "name": "test_name_1",
        "value": "test_value_1",
    }


@pytest.fixture
def fxt_annotation_template_2():
    yield AnnotationTemplate(
        id_=ID("test_id_2"),
        name="test_name_2",
        value="test_value_2",
    )


@pytest.fixture
def fxt_annotation_template_2_mapped():
    yield {
        "id": "test_id_2",
        "name": "test_name_2",
        "value": "test_value_2",
    }


class TestAnnotationTemplateRESTController:
    def test_make_annotation_template(
        self,
        fxt_project_identifier,
        fxt_annotation_template_1_rest,
        fxt_annotation_template_1_mapped,
        fxt_annotation_template_1,
    ) -> None:
        with (
            patch.object(AnnotationTemplateRepo, "save") as mock_save_annotation_template,
            patch.object(AnnotationTemplateRepo, "generate_id", return_value=fxt_annotation_template_1.id_),
        ):
            annotation_template = AnnotationTemplateRESTController.make_annotation_template(
                project_identifier=fxt_project_identifier,
                data=fxt_annotation_template_1_rest,
            )

        assert annotation_template == fxt_annotation_template_1_mapped
        mock_save_annotation_template.assert_called_once_with(
            instance=fxt_annotation_template_1,
        )

    def test_get_annotation_template(
        self,
        fxt_project_identifier,
        fxt_annotation_template_1_mapped,
        fxt_annotation_template_1,
    ) -> None:
        with (
            patch.object(
                AnnotationTemplateRepo, "get_by_id", return_value=fxt_annotation_template_1
            ) as mock_get_annotation_template,
        ):
            annotation_template = AnnotationTemplateRESTController.get_annotation_template(
                project_identifier=fxt_project_identifier,
                annotation_template_id=fxt_annotation_template_1.id_,
            )

        assert annotation_template == fxt_annotation_template_1_mapped
        mock_get_annotation_template.assert_called_once_with(
            id_=fxt_annotation_template_1.id_,
        )

    def test_get_annotation_templates(
        self,
        fxt_project_identifier,
        fxt_annotation_template_1_mapped,
        fxt_annotation_template_1,
        fxt_annotation_template_2_mapped,
        fxt_annotation_template_2,
    ) -> None:
        with (
            patch.object(
                AnnotationTemplateRepo,
                "get_all",
                return_value=[fxt_annotation_template_1, fxt_annotation_template_2],
            ) as mock_get_annotation_templates,
        ):
            annotation_templates = AnnotationTemplateRESTController.get_annotation_templates(
                project_identifier=fxt_project_identifier,
            )

        assert annotation_templates == {
            "annotation_templates": [fxt_annotation_template_1_mapped, fxt_annotation_template_2_mapped]
        }
        mock_get_annotation_templates.assert_called_once()
