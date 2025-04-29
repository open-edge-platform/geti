# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
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
