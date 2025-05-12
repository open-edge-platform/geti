# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the Image entity"""

import datetime
import logging

from iai_core.entities.media import ImageExtensions, Media, MediaPreprocessing, MediaPreprocessingStatus
from iai_core.entities.persistent_entity import PersistentEntity
from iai_core.utils.time_utils import now

from geti_types import ID, ImageIdentifier

logger = logging.getLogger(__name__)

IMAGE_THUMBNAIL_SUFFIX = "_thumbnail.jpg"


class Image(Media, PersistentEntity):
    """
    Represents a 2D image in SC.

    :param name: Name
    :param creation_date: Date of creation. If ``None``, it will be set to `datetime.now(datetime.timezone.utc)`
    :param id: ID of image.
    :param width: Image width
    :param height: Image height
    :param size: Image binary size
    :param extension: The original extension of the image
    :param ephemeral: True if the image exists only in memory, False if it is backed
        up by the database
    """

    def __init__(  # noqa: PLR0913
        self,
        name: str,
        id: ID,
        uploader_id: str,
        width: int,
        height: int,
        size: int,
        preprocessing: MediaPreprocessing,
        creation_date: datetime.datetime | None = None,
        extension: ImageExtensions = ImageExtensions.PNG,
        ephemeral: bool = True,
    ) -> None:
        creation_date = now() if creation_date is None else creation_date

        PersistentEntity.__init__(
            self,
            id_=id,
            ephemeral=ephemeral,
        )
        Media.__init__(
            self,
            name=name,
            height=height,
            width=width,
            creation_date=creation_date,
            uploader_id=uploader_id,
            size=size,
            extension=extension,
            preprocessing=preprocessing,
        )

    @property
    def data_binary_filename(self) -> str:
        """
        Fetches binary filename of stored image.
        :return: binary filename
        """
        return str(self.id_) + self.extension.value

    @property
    def thumbnail_filename(self) -> str:
        """
        Fetches thumbnail filename of stored image.
        :return: thumbnail filename
        """
        return Image.thumbnail_filename_by_image_id(str(self.id_))

    @staticmethod
    def thumbnail_filename_by_image_id(image_id: str) -> str:
        """
        Fetches thumbnail filename of stored image.

        :param image_id: Image identifier
        :return: thumbnail filename
        """
        return image_id + IMAGE_THUMBNAIL_SUFFIX

    @property
    def media_identifier(self) -> ImageIdentifier:
        return ImageIdentifier(self.id_)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Image):
            if self.id_ != ID() and other.id_ != ID():
                return (
                    self.id_ == other.id_
                    and self.name == other.name
                    and self.width == other.width
                    and self.height == self.height
                    and self.size == other.size
                )
            return self.id_ == other.id_ and self.name == other.name
        return False

    def __repr__(self) -> str:
        return f"Image({self.id_}, '{self.name}')"


class NullImage(Image):
    """Representation of an image that is not found"""

    def __init__(self) -> None:
        super().__init__(
            name="",
            creation_date=datetime.datetime.min,
            id=ID(),
            uploader_id="",
            width=0,
            height=0,
            size=0,
            ephemeral=False,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )

    def __repr__(self) -> str:
        return "NullImage()"
