import abc
import hashlib
from enum import Enum

from geti_types import ID


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    VIDEO_FRAME = "video_frame"


class MediaIdentifierEntity(abc.ABC):
    """
    This is an interface for other entities used to identify IMedia.
    Note that only IPersistentMedia contains ID (as a result of persistence inside database).
    Other media which is not inherited from IPersistentMedia will need to have an identifier as well,
    which could be a composite of several variables.
    MediaIdentifierEntity is created for that purpose, as an identifier for everything inherited from IMedia.
    """

    def __init__(self, media_id: ID, media_type: MediaType) -> None:
        if not isinstance(media_id, ID):
            raise ValueError(f"Attempting to create {self.__class__.__name__} without the ID of the {media_type}.")
        self._media_type = media_type
        self._media_id = media_id

    @property
    def media_type(self) -> MediaType:
        """
        Returns the identifier name
        """
        return self._media_type

    @property
    def media_id(self) -> ID:
        """
        Returns the ID of the media.
        """
        return self._media_id

    @abc.abstractmethod
    def as_tuple(self) -> tuple:
        """
        Return a tuple uniquely identifying this media.

        The tuple can be used for instance as a sortable key to sort a list of media identifiers.
        """
        raise NotImplementedError

    def as_id(self) -> ID:
        """
        Return an ID obtained by hashing this media identifier.

        This method uniquely maps a complex identifier (MediaIdentifierEntity) to
        a simpler one (ObjectId), which is handy when one wants to use the media
        identifier as a primary key of a database collection.

        The uniqueness is guaranteed by SHA-256, which is virtually collision-free.
        """
        hash_object = hashlib.sha256()
        media_identifier_str = "".join(str(x) for x in self.as_tuple())
        hash_object.update(media_identifier_str.encode("utf-8"))
        hex_digest = hash_object.hexdigest()[:24]
        return ID(hex_digest)

    @abc.abstractmethod
    def __repr__(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def __eq__(self, other: object) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def __hash__(self):
        raise NotImplementedError


class ImageIdentifier(MediaIdentifierEntity):
    """
    Media identifier that is used to identify an image.
    """

    def __init__(self, image_id: ID) -> None:
        super().__init__(media_id=image_id, media_type=MediaType.IMAGE)

    def as_tuple(self) -> tuple:
        """
        Return a tuple uniquely identifying this media.

        The tuple can be used for instance as a sortable key to sort a list of media identifiers.
        """
        return self.media_type.value, self.media_id

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(image_id={str(self.media_id)})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ImageIdentifier):
            return False
        return self.media_id == other.media_id

    def __hash__(self):
        return hash(str(self))


class VideoIdentifier(MediaIdentifierEntity):
    """
    Media identifier that is used to identify a video.
    VideoIdentifier is equal to Video.id_
    """

    def __init__(self, video_id: ID) -> None:
        super().__init__(media_id=video_id, media_type=MediaType.VIDEO)

    def as_tuple(self) -> tuple:
        """
        Return a tuple uniquely identifying this media.

        The tuple can be used for instance as a sortable key to sort a list of media identifiers.
        """
        return self.media_type.value, self.media_id

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(video_id={str(self.media_id)})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VideoIdentifier):
            return False
        return self.media_id == other.media_id

    def __hash__(self):
        return hash(str(self))


class VideoFrameIdentifier(MediaIdentifierEntity):
    """
    Media identifier that is used to identify a video frame.
    VideoFrameIdentifier is a composite of Video.id_ and frame number (frame index inside the video)

    Note that video frames are not persistent media, however they need to be referenced by annotations.
    One of the objectives of media identifier is allowing this type of reference without having to save the referenced
    media into the database.
    """

    def __init__(self, video_id: ID, frame_index: int) -> None:
        if not isinstance(video_id, ID):
            raise ValueError("Attempting to create VideoFrameIdentifier without the ID of the video")
        super().__init__(media_id=video_id, media_type=MediaType.VIDEO_FRAME)
        self._frame_index = frame_index

    @property
    def frame_index(self) -> int:
        return self._frame_index

    def as_tuple(self) -> tuple:
        return self.media_type.value, self.media_id, self.frame_index

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(video_id={self.media_id}, frame_index={self.frame_index})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VideoFrameIdentifier):
            return False
        return self.frame_index == other.frame_index and self.media_id == other.media_id

    def __hash__(self):
        return hash(str(self))


class NullMediaIdentifier(MediaIdentifierEntity):
    """
    This is used to represent NULL for MediaIdentifierEntity.
    """

    def __init__(self) -> None:
        super().__init__(media_id=ID(), media_type=None)  # type: ignore

    def as_tuple(self) -> tuple:
        return ()

    def __repr__(self) -> str:
        return "NullMediaIdentifier()"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, NullMediaIdentifier)

    def __hash__(self):
        return hash(str(self))
