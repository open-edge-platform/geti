# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements the repository for image entities
"""

import logging
from collections.abc import Callable, Iterable, Iterator
from typing import Any

from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from iai_core.entities.image import Image, NullImage
from iai_core.entities.media import ImageExtensions
from iai_core.repos.base.dataset_storage_based_repo import DatasetStorageBasedSessionRepo
from iai_core.repos.base.session_repo import QueryAccessMode
from iai_core.repos.mappers.cursor_iterator import CursorIterator
from iai_core.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from iai_core.repos.mappers.mongodb_mappers.media_mapper import ImageToMongo
from iai_core.repos.storage.binary_repos import ImageBinaryRepo, ThumbnailBinaryRepo

from geti_types import ID, DatasetStorageIdentifier, ImageIdentifier, Session

logger = logging.getLogger(__name__)
# The following extensions are not supported natively due to browser and Datumaro limitations.
# Media with these extensions should be converted to another format before being saved to the repo.
UNSUPPORTED_SAVE_EXT = [".tif", ".tiff", ".jfif"]


class ImageRepo(DatasetStorageBasedSessionRepo[Image]):
    """
    Repository to persist Image entities in the database.

    :param dataset_storage_identifier: Identifier of the dataset_storage
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    collection_name = "image"

    def __init__(
        self,
        dataset_storage_identifier: DatasetStorageIdentifier,
        session: Session | None = None,
    ) -> None:
        super().__init__(
            collection_name=ImageRepo.collection_name,
            session=session,
            dataset_storage_identifier=dataset_storage_identifier,
        )
        # Extensions that we allow to be stored in the binary repo
        self.allowed_save_extensions = [ext for ext in ImageExtensions if ext.value not in UNSUPPORTED_SAVE_EXT]
        # binary repos are initialized lazily when needed
        self.__binary_repo: ImageBinaryRepo | None = None
        self.__thumbnail_binary_repo: ThumbnailBinaryRepo | None = None

    @property
    def forward_map(self) -> Callable[[Image], dict]:
        return ImageToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], Image]:
        return ImageToMongo.backward

    @property
    def null_object(self) -> NullImage:
        return NullImage()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(cursor=mongo_cursor, mapper=ImageToMongo, parameter=None)

    @property
    def binary_repo(self) -> ImageBinaryRepo:
        """Binary repo relative to the image repo"""
        if self.__binary_repo is None:
            self.__binary_repo = ImageBinaryRepo(self.identifier)
        return self.__binary_repo

    @property
    def thumbnail_binary_repo(self) -> ThumbnailBinaryRepo:
        """Thumbnail binary repo relative to the image repo"""
        if self.__thumbnail_binary_repo is None:
            self.__thumbnail_binary_repo = ThumbnailBinaryRepo(self.identifier)
        return self.__thumbnail_binary_repo

    def _delete_binaries_by_image(self, image: Image) -> None:
        """
        Delete all binary data referenced by an image.

        :param image: Image containing the references to the binary data to delete
        """
        if image.data_binary_filename:
            self.binary_repo.delete_by_filename(image.data_binary_filename)
        if image.thumbnail_filename:
            self.thumbnail_binary_repo.delete_by_filename(image.thumbnail_filename)

    def get_all_identifiers(self) -> Iterator[ImageIdentifier]:
        """
        Get all media identifiers of images contained in the dataset storage.

        :return: iterator over the image identifiers
        """
        for image_id in super().get_all_ids():
            yield ImageIdentifier(image_id=image_id)

    def delete_by_id(self, id_: ID) -> bool:
        """
        Delete an image, its binary data and thumbnail from the database and filesystem.

        :param id_: ID of the image to delete
        :return: True if any DB document was matched and deleted, False otherwise
        """
        # Get the document (which contains the binary data filename). If not found, it means
        # the ID is invalid, the image was already removed, or the user can't access it
        query = self.preliminary_query_match_filter(access_mode=QueryAccessMode.READ)
        query["_id"] = IDToMongo.forward(id_)
        image_doc = self._collection.find_one(query, {"extension": 1})
        if not image_doc:
            logger.warning(
                "Image document with id '%s' not found, possibly it is already deleted",
                id_,
            )
            return False

        # Delete the image document first, to prevent data corruption in case of error
        # during the binary deletion stage
        image_deleted: bool = super().delete_by_id(id_)

        if image_deleted:
            # Delete thumbnail
            thumbnail_filename = Image.thumbnail_filename_by_image_id(str(id_))
            self.thumbnail_binary_repo.delete_by_filename(thumbnail_filename)

            # Delete binary
            image_binary_filename = f"{str(id_)}.{image_doc['extension'].lower()}"
            self.binary_repo.delete_by_filename(image_binary_filename)

        return image_deleted

    def delete_all(self, extra_filter: dict | None = None) -> bool:
        """
        Delete all the images, their binary data and thumbnails.

        :param extra_filter: Optional filter to apply in addition to the default one,
            which depends on the repo type.
        :return: True if any DB document was matched and deleted, False otherwise
        """
        if extra_filter is not None:
            # Since it's not possible to apply the filter to binary repos,
            # we would need a fallback implementation that deletes matched items
            # one by one, which is much slower of course.
            raise NotImplementedError

        # Delete the images documents first, to prevent data corruption in case of error
        # during the binaries deletion stage
        any_item_deleted = super().delete_all()

        if any_item_deleted:
            # Delete image binary data
            self.binary_repo.delete_all()

            # Delete thumbnails
            self.thumbnail_binary_repo.delete_all()

        return any_item_deleted

    def get_image_by_ids(self, ids: Iterable[ID]) -> dict[ID, Image]:
        """
        Get image by image ids

        :param ids: List of IDs to obtain the image for
        :return: Dict mapping each ID to the corresponding Image descriptor
        """
        query: dict[str, Any] = self.preliminary_query_match_filter(QueryAccessMode.READ)
        query["_id"] = {"$in": [IDToMongo.forward(id_) for id_ in ids]}
        docs = self._collection.find(query)
        return {IDToMongo.backward(doc["_id"]): ImageToMongo.backward(doc) for doc in docs}
