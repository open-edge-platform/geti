# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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

"""This module implements the Label entity"""

import colorsys
import datetime
from enum import Enum, auto

from sc_sdk.entities.color import Color
from sc_sdk.entities.persistent_entity import PersistentEntity
from sc_sdk.utils.time_utils import now

from geti_types import ID


def distinct_colors(number_of_colors: int) -> list[Color]:
    """
    Generates n distinct colors
    :return: list of Color entities
    """
    result = []
    red = 1.0
    green = 1.0
    blue = 0.0
    hue, saturation, value = colorsys.rgb_to_hsv(red, green, blue)
    step = 1.0 / number_of_colors
    for _ in range(number_of_colors):
        red, green, blue = colorsys.hsv_to_rgb(hue, saturation, value)
        result.append(Color(int(red * 255), int(green * 255), int(blue * 255), 255))
        hue += step
        if hue > 1.0:
            hue -= 1.0
    return result


class Domain(Enum):
    """Describes an algorithm domain like classification, detection, etc."""

    NULL = auto()
    CLASSIFICATION = auto()
    DETECTION = auto()
    SEGMENTATION = auto()
    ANOMALY_CLASSIFICATION = auto()
    ANOMALY_DETECTION = auto()
    ANOMALY_SEGMENTATION = auto()
    INSTANCE_SEGMENTATION = auto()
    ROTATED_DETECTION = auto()
    ACTION_CLASSIFICATION = auto()
    ACTION_DETECTION = auto()
    KEYPOINT_DETECTION = auto()

    def __str__(self):
        """Returns Domain name."""
        return str(self.name)


class Label(PersistentEntity):
    """This represents a label. The Label is the object that the user annotates and the tasks predict.

    For example, a label with name "car" can be constructed as follows.

    >>> car = Label(name="car",domain=Domain.DETECTION)

    .. rubric:: About Empty Label

    In addition to representing the presence of a certain object, the label can also
    be used to represent the absence of objects in the image (or other media types).
    Such a label is referred to as empty label.
    The empty label is constructed as follows:

    >>> empty = Label(name="empty",domain=Domain.DETECTION,is_empty=True)

    Empty label is used to declare that there is nothing of interest inside this image.
    For example, let's assume a car detection project. During annotation process,
    for positive images (images with cars), the users are asked to annotate the images
    with bounding boxes with car label. However, when the user sees a negative image
    (no car), the user needs to annotate this image with an empty label.

    The empty label is particularly useful to distinguish images with no objects
    of interest from images that have not been annotated, especially in task-chain
    scenario. Let's assume car detection task that is followed with with another
    detection task which detects the driver inside the car. There are two issues here:

    1. The user can (intentionally or unintentionally) miss to annotate
        the driver inside a car.
    2. There is no driver inside the car.

    Without empty label, these two cases cannot be distinguished.
    This is why an empty label is introduced. The empty label makes an explicit
    distinction between missing annotations and "negative" images.

    :param name: the name of the label
    :param domain: the algorithm domain this label is associated to
    :param color: the color of the label (See :class:`Color`)
    :param hotkey: key or combination of keys to select this label in the UI
    :param creation_date: the date time of the label creation
    :param is_empty: set to True if the label is an empty label.
    :param id_: the ID of the label. Set to ID() so that a new unique ID
        will be assigned upon saving. If the argument is None, it will be set to ID()
    :param is_anomalous: boolean that indicates whether the label is the
        Anomalous label. Always set to False for non-anomaly projects.
    """

    def __init__(  # noqa: PLR0913
        self,
        id_: ID,
        name: str,
        domain: Domain,
        color: Color | None = None,
        hotkey: str = "",
        creation_date: datetime.datetime | None = None,
        is_empty: bool = False,
        is_anomalous: bool = False,
        ephemeral: bool = True,
    ):
        color = Color.random() if color is None else color
        creation_date = now() if creation_date is None else creation_date

        self.name = name
        self.color = color
        self.hotkey = hotkey
        self.domain = domain
        self._is_empty = is_empty
        self._creation_date = creation_date
        self.is_anomalous = is_anomalous
        PersistentEntity.__init__(self, id_=id_, ephemeral=ephemeral)

    @property
    def is_empty(self) -> bool:
        """Returns a boolean indicating if the label is an empty label."""
        return self._is_empty

    @property
    def creation_date(self) -> datetime.datetime:
        """Returns the creation date of the label."""
        return self._creation_date

    def __repr__(self):
        """String representation of the label."""
        return (
            f"Label({self.id_}, name={self.name}, hotkey={self.hotkey}, "
            f"domain={self.domain}, color={self.color.hex_str}, is_anomalous={self.is_anomalous})"
        )

    def __eq__(self, other: object) -> bool:
        """Returns True if the two labels are equal."""
        if isinstance(other, Label):
            return (
                self.id_ == other.id_
                and self.name == other.name
                and self.color == other.color
                and self.hotkey == other.hotkey
                and self.domain == other.domain
                and self.is_anomalous == other.is_anomalous
            )
        return False

    def __lt__(self, other: object):
        """Returns True if self.id_ < other.id_."""
        if isinstance(other, Label):
            return self.id_ < other.id_
        return False

    def __hash__(self):
        """Returns hash of the label."""
        return hash(str(self))


class NullLabel(Label):
    """Representation of a label 'label not found'"""

    def __init__(self) -> None:
        super().__init__(
            name="",
            domain=Domain.CLASSIFICATION,
            color=Color(0, 0, 0),
            creation_date=datetime.datetime.min,
            id_=ID(),
            ephemeral=False,
        )

    def __repr__(self) -> str:
        return "NullLabel()"
