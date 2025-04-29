# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

"""This module contains the MongoDB mapper for the AnnotationTemplate entity"""

from sc_sdk.entities.annotation_template import AnnotationTemplate
from sc_sdk.repos.mappers.mongodb_mapper_interface import IMapperSimple

from .id_mapper import IDToMongo
from .primitive_mapper import DatetimeToMongo


class AnnotationTemplateToMongo(IMapperSimple[AnnotationTemplate, dict]):
    """MongoDB mapper for `AnnotationTemplate` entities"""

    @staticmethod
    def forward(instance: AnnotationTemplate) -> dict:
        return {
            "id_": IDToMongo.forward(instance.id_),
            "name": instance.name,
            "value": instance.value,
            "creation_date": DatetimeToMongo.forward(instance.creation_date),
        }

    @staticmethod
    def backward(instance: dict) -> AnnotationTemplate:
        return AnnotationTemplate(
            id_=IDToMongo.backward(instance["id_"]),
            name=instance["name"],
            value=instance["value"],
            creation_date=DatetimeToMongo.backward(instance.get("creation_date")),
            ephemeral=False,
        )
