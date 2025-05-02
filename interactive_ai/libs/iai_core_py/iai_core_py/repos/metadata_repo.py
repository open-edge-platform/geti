# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the repository for metadata entities"""

import io
import logging
from collections.abc import Callable, Sequence
from functools import partial
from typing import TYPE_CHECKING, cast
from urllib.parse import quote_plus

import numpy as np
from pymongo import DESCENDING, IndexModel
from pymongo.client_session import ClientSession
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from iai_core_py.entities.metadata import IMetadata, MetadataItem, NullMetadataItem
from iai_core_py.entities.tensor import Tensor
from iai_core_py.repos.base.dataset_storage_based_repo import DatasetStorageBasedSessionRepo
from iai_core_py.repos.base.session_repo import QueryAccessMode
from iai_core_py.repos.mappers import CursorIterator, IDToMongo, MediaIdentifierToMongo, MetadataItemToMongo
from iai_core_py.repos.mappers.mongodb_mappers.metadata_mapper import (
    MetadataDocSchema,
    MetadataItemMapperBackwardParameters,
)
from iai_core_py.repos.storage.binary_repos import TensorBinaryRepo

from geti_types import ID, DatasetStorageIdentifier, MediaIdentifierEntity, Session

if TYPE_CHECKING:

    class FloatMetadata(IMetadata): ...

else:
    from iai_core_py.entities.metadata import FloatMetadata

logger = logging.getLogger(__name__)


class MetadataRepo(DatasetStorageBasedSessionRepo[MetadataItem]):
    """
    Repository to persist MetadataItem entities in the database.

    :param dataset_storage_identifier: Identifier of the dataset_storage
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    def __init__(
        self,
        dataset_storage_identifier: DatasetStorageIdentifier,
        session: Session | None = None,
    ) -> None:
        super().__init__(
            collection_name="metadata_item",
            session=session,
            dataset_storage_identifier=dataset_storage_identifier,
        )
        # binary repos are initialized lazily when needed
        self.__tensor_binary_repo: TensorBinaryRepo | None = None

    @property
    def forward_map(self) -> Callable[[MetadataItem], dict]:
        return MetadataItemToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], MetadataItem]:
        return partial(
            MetadataItemToMongo.backward,
            parameters=MetadataItemMapperBackwardParameters(
                tensor_binary_repo=self.tensor_binary_repo,
                dataset_storage_identifier=self.identifier,
            ),
        )

    @property
    def null_object(self) -> NullMetadataItem:
        return NullMetadataItem()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(
            cursor=mongo_cursor,
            mapper=MetadataItemToMongo,
            parameter=MetadataItemMapperBackwardParameters(
                tensor_binary_repo=self.tensor_binary_repo,
                dataset_storage_identifier=self.identifier,
            ),
        )

    @property
    def indexes(self) -> list[IndexModel]:
        super_indexes = super().indexes
        new_indexes = [
            IndexModel(
                [
                    ("dataset_storage_id", DESCENDING),
                    ("project_id", DESCENDING),
                    ("workspace_id", DESCENDING),
                    ("organization_id", DESCENDING),
                    ("content.schema", DESCENDING),
                ]
            ),
            IndexModel([("media_identifier", DESCENDING)]),
            IndexModel([("content.schema", DESCENDING)]),  # TODO CVS-144604 drop unused index
            IndexModel([("content.prediction_id", DESCENDING)]),
        ]
        return super_indexes + new_indexes

    @property
    def tensor_binary_repo(self) -> TensorBinaryRepo:
        """Tensor binary repo relative to the metadata repo"""
        if self.__tensor_binary_repo is None:
            self.__tensor_binary_repo = TensorBinaryRepo(self.identifier)
        return self.__tensor_binary_repo

    def _offload_tensor_onto_repo(self, tensor: Tensor) -> None:
        from iai_core_py.adapters.tensor_adapter import TensorAdapter

        # Object name will be '{name}.npz'; special characters are escaped
        binary_filename = quote_plus(f"{tensor.name}.npz")

        buffer = io.BytesIO()
        np.savez(buffer, array=tensor.numpy)
        data = buffer.getvalue()

        binary_filename = self.tensor_binary_repo.save(
            dst_file_name=binary_filename, data_source=data, make_unique=True
        )

        # Replace the in-memory numpy with an adapter
        tensor.tensor_adapter = TensorAdapter(
            data_source=self.tensor_binary_repo,
            binary_filename=binary_filename,
            shape=tensor.shape,
        )
        tensor._numpy = None  # type: ignore

    def _delete_binaries_by_metadata_item(self, metadata_item: MetadataItem) -> None:
        """
        Delete all binary data referenced by a metadata item.

        :param metadata_item: Metadata item containing the references to the binary data to delete
        """
        match metadata_item.data:
            case Tensor():
                tensor = cast("Tensor", metadata_item.data)
                if tensor.data_binary_filename != "":
                    self.tensor_binary_repo.delete_by_filename(filename=tensor.data_binary_filename)
            case _:
                pass  # no binaries to delete

    def save(
        self,
        instance: MetadataItem,
        mongodb_session: ClientSession | None = None,
    ) -> None:
        """
        Save a metadata item to the database and its binary data to the persisted
        storage, if needed based on the metadata type.

        Metadata item should be treated as immutable entities and never saved twice.

        :param instance: Metadata item to save
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        """
        if not instance.ephemeral:
            raise RuntimeError(
                f"Metadata item with ID `{instance.id_}` (data type `{type(instance.data)}`) cannot be saved twice"
            )

        try:
            # Store the binary to storage
            match instance.data:
                case Tensor():
                    tensor = cast("Tensor", instance.data)
                    if tensor.tensor_adapter is None:
                        self._offload_tensor_onto_repo(tensor=tensor)
                case FloatMetadata():
                    pass  # the float value is directly stored in the MongoDB document
                case _:
                    raise TypeError(f"Unsupported metadata type {type(instance.data)}")

            # Store the MongoDB document
            super().save(instance, mongodb_session=mongodb_session)
        except TypeError:
            raise
        except Exception:
            # In case of error, delete any binary file that was already stored
            logger.exception(
                "Error saving metadata item `%s` to `%s`; associated binaries will be removed",
                instance.id_,
                self.identifier,
            )
            self._delete_binaries_by_metadata_item(metadata_item=instance)
            raise

    def save_many(
        self,
        instances: Sequence[MetadataItem],
        mongodb_session: ClientSession | None = None,
    ) -> None:
        # Not implemented because unneeded and due to the complexity of an
        # efficient and fault-tolerant implementation
        raise NotImplementedError

    def delete_by_id(self, id_: ID) -> bool:
        """
        Delete a metadata item and its binary (if needed) from the DB and filesystem.

        :param id_: ID of the metadata item to delete
        :return: True if any DB document was matched and deleted, False otherwise
        """
        # Fetch the document to know the type and binary data filename.
        # If not found, it means that either the ID is invalid, the image was already
        # removed, or the user can't access it
        query = self.preliminary_query_match_filter(access_mode=QueryAccessMode.READ)
        query["_id"] = IDToMongo.forward(id_)
        metadata_doc = self._collection.find_one(query, {"content.schema": 1, "content.binary_filename": 1})
        if not metadata_doc:
            logger.warning(
                "Metadata item doc with id '%s' not found, possibly already deleted",
                id_,
            )
            return False

        # Delete the image document first, to prevent data corruption in case of error
        # during the binary deletion stage
        metadata_item_deleted: bool = super().delete_by_id(id_)

        if metadata_item_deleted:
            # Delete binary if needed
            match metadata_doc["content"]["schema"].upper():
                case MetadataDocSchema.FLOAT.name:
                    pass
                case MetadataDocSchema.TENSOR.name:
                    self.tensor_binary_repo.delete_by_filename(metadata_doc["content"]["binary_filename"])
                case _:
                    raise TypeError(f"Invalid metadata type {metadata_doc['content']['schema']}")

        return metadata_item_deleted

    def _delete_all_with_filter(self, extra_filter: dict) -> bool:
        # Fetch the matching documents to know the types and binary data filenames.
        # If not found, it means that either the identifier is invalid, the items were
        # already removed, or the user can't access them
        tensor_type_str = str(MetadataDocSchema.TENSOR.value)
        files_to_delete_by_type: dict[str, list[str]] = {
            tensor_type_str: [],
        }
        query = extra_filter | self.preliminary_query_match_filter(access_mode=QueryAccessMode.READ)
        metadata_docs_to_delete = self._collection.find(query, {"content.schema": 1, "content.binary_filename": 1})
        for metadata_doc in metadata_docs_to_delete:
            if "binary_filename" in metadata_doc["content"]:
                type = metadata_doc["content"]["schema"].lower()
                binary_filename = metadata_doc["content"]["binary_filename"]
                files_to_delete_by_type.setdefault(type, []).append(binary_filename)

        # Delete tensor binaries
        for tensor_binary_filename in files_to_delete_by_type[tensor_type_str]:
            self.tensor_binary_repo.delete_by_filename(filename=tensor_binary_filename)

        # Delete the documents last, because if there are problems happening during binaries removal, data will be
        # cleaned from repo and leftover binaries will remain.
        return super().delete_all(extra_filter=extra_filter)

    def _delete_all_no_filter(self) -> bool:
        # Delete tensors
        self.tensor_binary_repo.delete_all()

        # Delete the documents last, because if there are problems happening during binaries removal, data will be
        # cleaned from repo and leftover binaries will remain.
        return super().delete_all()

    def delete_all(self, extra_filter: dict | None = None) -> bool:
        """
        Delete all the metadata items and their binary data, if any.

        :param extra_filter: Optional filter to apply in addition to the default one,
            which depends on the repo type.
        :return: True if any DB document was matched and deleted, False otherwise
        """
        if extra_filter is None:  # fast path
            return self._delete_all_no_filter()

        return self._delete_all_with_filter(extra_filter=extra_filter)

    def delete_all_by_type(self, metadata_type: type[IMetadata]) -> None:
        """
        Delete all the metadata items of a certain type

        :param metadata_type: Type of the metadata (e.g. FloatMetadata or Tensor)
        """
        # For efficiency:
        #   1. remove binaries with delete_all() rather than by filename, where applicable
        #   2. remove docs with super().delete_all() instead of self.delete_all();
        #      the former is faster because it deletes data in bulk, and binaries have
        #      been removed anyway in step #1
        if metadata_type == FloatMetadata:
            super().delete_all(extra_filter={"content.schema": MetadataDocSchema.FLOAT.value})
        elif metadata_type == Tensor:
            super().delete_all(extra_filter={"content.schema": MetadataDocSchema.TENSOR.value})
            self.tensor_binary_repo.delete_all()
        else:
            raise ValueError(f"Invalid metadata type '{metadata_type}'")

    def delete_all_by_media_identifier(self, media_identifier: MediaIdentifierEntity) -> None:
        """
        Delete all the metadata items relative to a given media.

        :param media_identifier: Identifier of the media
        """
        media_filter = {"media_identifier": MediaIdentifierToMongo.forward(media_identifier)}
        self.delete_all(extra_filter=media_filter)
