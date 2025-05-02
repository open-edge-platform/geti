# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module implements dataset item mapper for conversion between SC DatasetItem and Datumaro DatasetItem"""

from multiprocessing.pool import AsyncResult
from typing import Any

import cv2
import datumaro as dm
import numpy as np
from geti_types import ID, DatasetStorageIdentifier
from iai_core.entities.annotation import Annotation
from iai_core.entities.dataset_item import DatasetItem
from iai_core.entities.label import Label
from iai_core.entities.shapes import Ellipse, Keypoint, Point, Polygon, Rectangle, Shape
from iai_core.entities.subset import Subset
from media_utils import get_media_numpy

from jobs_common_extras.datumaro_conversion.mappers.annotation_scene_mapper import AnnotationSceneMapper
from jobs_common_extras.datumaro_conversion.mappers.id_mapper import IDMapper
from jobs_common_extras.datumaro_conversion.mappers.label_mapper import LabelMapper


class DmImageAdapter:
    """Adapt Datumaro Image to SC Image"""

    def __init__(self, dm_image: dm.Image) -> None:
        super().__init__()
        self.dm_image = dm_image

    @property
    def width(self) -> int:
        return self.dm_image.size[1]

    @property
    def height(self) -> int:
        return self.dm_image.size[0]

    @property
    def num_channels(self) -> int:
        img = self._fetch_numpy()
        if img.ndim == 2:
            return 1
        if img.ndim == 3:
            return img.shape[-1]

        raise ValueError(f"Invalid number of image dim={img.ndim}")

    def fetch_bytes(self) -> bytes:
        return self.dm_image.bytes

    def fetch_numpy(self) -> np.ndarray:
        """Read the image from Datumaro Image.
        Since Datumaro returns an image with the HWC Grayscale/BGR(A) [0; 255] format,
        it converts its image format to RGB[0; 255] (uint8).

        :return: The image as a Numpy array
        """
        numpy = self._fetch_numpy().astype(dtype=np.uint8)

        # Convert if grayscale
        return (
            cv2.cvtColor(numpy, cv2.COLOR_GRAY2RGB) if len(numpy.shape) < 2 else cv2.cvtColor(numpy, cv2.COLOR_BGR2RGB)
        )

    def _fetch_numpy(self):
        return self.dm_image.data


class SubsetMapper:
    """Map Datumaro subset string to OTX Subset enum"""

    mapping = {subset.name: subset for subset in Subset}

    @classmethod
    def forward(cls, subset: Subset) -> str:
        """Convert subset from SC to Datumaro"""
        return subset.name


class PointMapper:
    """Conversion of point coordinates ROI from Geti to Datumaro"""

    @staticmethod
    def forward(instance: Point) -> dict:
        return {"x": instance.x, "y": instance.y}


class RectangleMapper:
    """Conversion of rectangle shape's ROI from Geti to Datumaro"""

    @staticmethod
    def forward(rectangle: Rectangle) -> dict[str, Any]:
        return {
            "type": rectangle.type.name,
            "modification_date": rectangle.modification_date.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "x1": rectangle.x1,
            "y1": rectangle.y1,
            "x2": rectangle.x2,
            "y2": rectangle.y2,
        }


class EllipseMapper:
    """Conversion of ellipse shape's ROI from Geti to Datumaro"""

    @staticmethod
    def forward(ellipse: Ellipse) -> dict[str, Any]:
        return {
            "type": ellipse.type.name,
            "modification_date": ellipse.modification_date.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "x1": ellipse.x1,
            "y1": ellipse.y1,
            "x2": ellipse.x2,
            "y2": ellipse.y2,
        }


class PolygonMapper:
    """Conversion of polygon shape's ROI from Geti to Datumaro"""

    @staticmethod
    def forward(polygon: Polygon) -> dict[str, Any]:
        return {
            "type": polygon.type.name,
            "modification_date": polygon.modification_date.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "points": [PointMapper.forward(p) for p in polygon.points],
        }


class KeypointMapper:
    """Conversion of keypoint shape's ROI from Geti to Datumaro"""

    @staticmethod
    def forward(keypoint: Keypoint) -> dict[str, Any]:
        return {
            "type": keypoint.type.name,
            "modification_date": keypoint.modification_date.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "points": [keypoint.x, keypoint.y],
            "visibility": [dm.Points.Visibility.visible if keypoint.is_visible else dm.Points.Visibility.hidden],
        }


class ShapeMapper:
    """Conversion of shape's ROI from Geti to Datumaro"""

    @staticmethod
    def forward(shape: Shape) -> dict[str, Any]:
        if isinstance(shape, Rectangle):
            return RectangleMapper.forward(shape)
        if isinstance(shape, Ellipse):
            return EllipseMapper.forward(shape)
        if isinstance(shape, Polygon):
            return PolygonMapper.forward(shape)
        if isinstance(shape, Keypoint):
            return KeypointMapper.forward(shape)
        raise ValueError(f"Invalid Shape provided, got {type(shape)}")


class RoIMapper:
    """For conversion of 'roi' (Region-of-interest) field from Geti to Datumaro"""

    ATTR_NAME = "roi"

    @staticmethod
    def forward(roi: Annotation, label_id_to_label: dict[ID, Label], include_empty: bool = True) -> dict[str, Any]:
        """Convert roi from Geti to Datumaro"""
        if not isinstance(roi.shape, Shape):
            raise TypeError("roi.shape's type should be Shape")
        shape = ShapeMapper.forward(shape=roi.shape)
        return {
            "id": IDMapper.forward(roi.id_),
            "shape": shape,
            "labels": [
                {
                    "label": LabelMapper.forward(label_id_to_label[scored_label.label_id]),
                    "probability": scored_label.probability,
                }
                for scored_label in roi.get_labels(include_empty=include_empty)
            ],
        }


class IgnoredLabelsMapper:
    """For conversion of `ignored_label_ids` field in Geti to `ignored_labels` in Datumaro"""

    ATTR_NAME = "ignored_labels"

    @staticmethod
    def forward(ignored_label_ids: set[ID], label_id_to_label: dict[ID, Label]) -> list[dict[str, Any]]:
        return [LabelMapper.forward(label_id_to_label[label_id]) for label_id in ignored_label_ids]


class DatasetItemMapper:
    """Map Datumaro DatasetItem to SC DatasetItem"""

    ATTR_MEDIA_ID = "id"

    def __init__(
        self,
        uploader_id: ID,
        annotation_scene_mapper: AnnotationSceneMapper,
        label_id_to_label: dict[ID, Label],
    ) -> None:
        self.uploader_id = str(uploader_id)
        self.annotation_scene_mapper = annotation_scene_mapper
        self.label_id_to_label = label_id_to_label

    def forward(
        self,
        dataset_storage_identifier: DatasetStorageIdentifier,
        instance: DatasetItem,
        image_bytes_future: AsyncResult[bytes] | None = None,
        extension: str | None = None,
    ) -> dm.DatasetItem:
        """Convert DatasetItem from SC to Datumaro"""
        if image_bytes_future is None:
            numpy_data = get_media_numpy(
                dataset_storage_identifier=dataset_storage_identifier,
                media=instance.media,
            )
            dm_image = dm.Image.from_numpy(
                lambda: cv2.cvtColor(numpy_data, cv2.COLOR_RGB2BGR),
                ext=".jpg",
                size=(instance.media.height, instance.media.width),
            )
        else:
            dm_image = dm.Image.from_bytes(
                data=lambda: image_bytes_future.get(),
                ext=extension,
                size=(instance.media.height, instance.media.width),
            )

        return dm.DatasetItem(
            id=IDMapper.forward(instance.id_),
            subset=SubsetMapper.forward(instance.subset),
            media=dm_image,
            annotations=self.annotation_scene_mapper.forward(instance.annotation_scene),
            attributes={
                self.ATTR_MEDIA_ID: str(instance.media.media_identifier.media_id),
                RoIMapper.ATTR_NAME: RoIMapper.forward(roi=instance.roi, label_id_to_label=self.label_id_to_label),
                IgnoredLabelsMapper.ATTR_NAME: IgnoredLabelsMapper.forward(
                    ignored_label_ids=instance.ignored_label_ids,
                    label_id_to_label=self.label_id_to_label,
                ),
            },
        )
