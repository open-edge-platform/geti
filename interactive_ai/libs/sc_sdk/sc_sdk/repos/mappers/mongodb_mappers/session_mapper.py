#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

"""This module contains the MongoDB mapper for session related entities"""

from sc_sdk.repos.mappers import IDToMongo
from sc_sdk.repos.mappers.mongodb_mapper_interface import IMapperSimple

from geti_types import RequestSource, Session


class SessionToMongo(IMapperSimple[Session, dict]):
    """MongoDB mapper for `Session` entities"""

    @staticmethod
    def forward(instance: Session) -> dict:
        serialized_instance = {
            "organization_id": IDToMongo.forward(instance.organization_id),
            "workspace_id": IDToMongo.forward(instance.workspace_id),
            "source": instance.source_str,
        }
        if instance.extra:
            serialized_instance["extra"] = instance.extra
        return serialized_instance

    @staticmethod
    def backward(instance: dict) -> Session:
        source = RequestSource[instance.get("source", "unknown").upper()]
        return Session(
            organization_id=IDToMongo.backward(instance["organization_id"]),
            workspace_id=IDToMongo.backward(instance["workspace_id"]),
            source=source,
            extra=instance.get("extra", {}),
        )
