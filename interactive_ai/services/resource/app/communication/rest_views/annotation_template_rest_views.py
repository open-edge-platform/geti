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
from sc_sdk.entities.annotation_template import AnnotationTemplate

ID = "id"
NAME = "name"
VALUE = "value"


class AnnotationTemplateRESTViews:
    """
    This class maps Annotation Template entities to REST View (and vice versa)
    """

    @staticmethod
    def annotation_template_from_rest(data: dict) -> AnnotationTemplate:
        """
        Deserializes the data dictionary into an AnnotationTemplate entity

        :param data: the serialized data dictionary
        :return: an AnnotationTemplate entity
        """

        return AnnotationTemplate(
            id_=data[ID],
            name=data[NAME],
            value=data[VALUE],
        )

    @staticmethod
    def annotation_template_to_rest(annotation_template: AnnotationTemplate) -> dict:
        """
        Serializes the AnnotationTemplate entity into a data dictionary

        :param annotation_template: an AnnotationTemplate entity
        :return: a serialized data dictionary
        """
        return {
            ID: annotation_template.id_,
            NAME: annotation_template.name,
            VALUE: annotation_template.value,
        }
