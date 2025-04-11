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
from typing import Any

from communication.rest_data_validator.annotation_template_rest_validator import AnnotationTemplateRestValidator
from communication.rest_views.annotation_template_rest_views import AnnotationTemplateRESTViews

from geti_types import ID, ProjectIdentifier
from sc_sdk.entities.annotation_template import AnnotationTemplate
from sc_sdk.repos.annotation_template_repo import AnnotationTemplateRepo


class AnnotationTemplateRESTController:
    @staticmethod
    def make_annotation_template(project_identifier: ProjectIdentifier, data: dict) -> dict[str, Any]:
        """
        Creates and saves a new annotation template

        :param project_identifier: Identifier of the project
        :param data: Dictionary containing the annotation template
        :return: the newly created AnnotationTemplate in REST view representation
        """
        AnnotationTemplateRestValidator().validate_annotation_template(annotation_template_rest=data)
        annotation_template = AnnotationTemplate(
            id_=AnnotationTemplateRepo.generate_id(),
            name=data["name"],
            value=data["value"],
        )
        AnnotationTemplateRepo(project_identifier=project_identifier).save(instance=annotation_template)
        return AnnotationTemplateRESTViews.annotation_template_to_rest(annotation_template)

    @staticmethod
    def get_annotation_template(project_identifier: ProjectIdentifier, annotation_template_id: ID) -> dict[str, Any]:
        """
        Get an AnnotationTemplate for the project

        :param project_identifier: Identifier of the project
        :param annotation_template_id: The ID of the annotation template to get
        :return: an AnnotationTemplate in REST view representation
        """
        annotation_template = AnnotationTemplateRepo(project_identifier=project_identifier).get_by_id(
            id_=annotation_template_id
        )

        return AnnotationTemplateRESTViews.annotation_template_to_rest(annotation_template)

    @staticmethod
    def get_annotation_templates(project_identifier: ProjectIdentifier) -> dict[str, list[dict]]:
        """
        Get all annotation templates for a project

        :param project_identifier: Identifier of the project
        :return: a dictionary of a list of AnnotationTemplates in REST view representation
        """
        annotation_templates = AnnotationTemplateRepo(project_identifier=project_identifier).get_all()

        return {
            "annotation_templates": [
                AnnotationTemplateRESTViews.annotation_template_to_rest(annotation_template)
                for annotation_template in annotation_templates
            ]
        }
