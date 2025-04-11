#
# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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
