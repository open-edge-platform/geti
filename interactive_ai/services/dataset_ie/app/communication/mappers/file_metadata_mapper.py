# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements the mapper to convert FileMetadata to and from
a serialized representation compatible with MongoDB
"""

import logging
from datetime import datetime, timezone
from typing import Any

from domain.entities.dataset_ie_file_metadata import ExportMetadata, FileMetadata, ImportMetadata

from sc_sdk.repos.mappers.mongodb_mapper_interface import IMapperSimple
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from sc_sdk.repos.mappers.mongodb_mappers.primitive_mapper import DatetimeToMongo

logger = logging.getLogger(__name__)


TTL_FIELD_NAME = "updated_date"


class FileMetadataToMongo(IMapperSimple[FileMetadata, dict]):
    """MongoDB mapper for  `FileMetadata` entities"""

    @staticmethod
    def forward(instance: FileMetadata) -> dict[str, Any]:
        file_metadata_mongo = {
            "id": IDToMongo.forward(instance.id_),
            "size": instance.size,
            "offset": instance.offset,
            "project_id": IDToMongo.forward(instance.project_id),
            TTL_FIELD_NAME: DatetimeToMongo.forward(datetime.now(timezone.utc)),
        }
        if isinstance(instance, ExportMetadata):
            file_metadata_mongo["metadata_type"] = "export"
        elif isinstance(instance, ImportMetadata):
            file_metadata_mongo["metadata_type"] = "import"
            file_metadata_mongo["upload_id"] = instance.upload_id  # type: ignore
            file_metadata_mongo["upload_parts"] = instance.upload_parts  # type: ignore
        else:
            raise ValueError(
                f"Failed to convert FileMetadata to MongoDB representation. "
                f"Invalid metadata type was received: {type(instance)}"
            )
        return file_metadata_mongo

    @staticmethod
    def backward(instance: dict) -> FileMetadata:
        metadata_type = instance.get("metadata_type", "import")
        if metadata_type == "import":
            metadata = ImportMetadata(
                id_=IDToMongo.backward(instance.get("_id", "")),
                size=int(instance.get("size", "0")),
                offset=int(instance.get("offset", "0")),
                upload_id=instance.get("upload_id"),
                upload_parts=instance.get("upload_parts"),
                project_id=IDToMongo.backward(instance.get("project_id", "")),
            )
        elif metadata_type == "export":
            metadata = ExportMetadata(  # type: ignore
                id_=IDToMongo.backward(instance.get("_id", "")),
                size=int(instance.get("size", "0")),
                offset=int(instance.get("offset", "0")),
                project_id=IDToMongo.backward(instance.get("project_id", "")),
            )
        else:
            raise ValueError(
                f"Metadata type: {metadata_type} is not recognized. "
                f"It has to be one of the following: ['import', 'export']"
            )
        return metadata
