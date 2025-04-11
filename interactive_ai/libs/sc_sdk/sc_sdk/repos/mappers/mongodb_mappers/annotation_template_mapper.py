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
