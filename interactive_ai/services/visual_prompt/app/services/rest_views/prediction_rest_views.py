# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import logging
import math
import operator
from enum import IntEnum, auto
from typing import Any

from services.rest_views.media_identifier_rest_views import MediaIdentifierRESTViews
from services.rest_views.scored_label_rest_views import ScoredLabelRESTViews
from services.visual_prompt_service import VPSPredictionResults

from geti_types import MediaIdentifierEntity
from iai_core_py.entities.shapes import Point, Polygon, Rectangle
from iai_core_py.utils.time_utils import now

logger = logging.getLogger(__name__)
TYPE = "type"
WIDTH = "width"
HEIGHT = "height"
X = "x"
Y = "y"
POINTS = "points"
ANGLE = "angle"


class RestShapeType(IntEnum):
    RECTANGLE = auto()
    POLYGON = auto()
    ROTATED_RECTANGLE = auto()


class PredictionRESTViews:
    @staticmethod
    def rectangle_shape_to_rest(rectangle_shape: Rectangle, media_height: int, media_width: int) -> dict:
        """
        Returns the REST representation of a rectangle.

        :param rectangle_shape: the input rectangle to be represented in REST
        :return: the REST representation of a rectangle.
        """
        return {
            TYPE: RestShapeType.RECTANGLE.name,
            X: round(rectangle_shape.x1 * media_width),
            Y: round(rectangle_shape.y1 * media_height),
            WIDTH: round(rectangle_shape.width * media_width),
            HEIGHT: round(rectangle_shape.height * media_height),
        }

    @staticmethod
    def point_to_rest(point: Point, media_height: int, media_width: int) -> dict:
        """
        Returns the REST representation of a Point.

        :param point: the point to be represented in REST
        :return: the REST representation of a point
        """
        return {
            X: round(point.x * media_width),
            Y: round(point.y * media_height),
        }

    @staticmethod
    def _polygon_shape_to_rest(polygon_shape: Polygon, media_height: int, media_width: int) -> dict:
        """
        Returns the REST representation of a polygon

        :param polygon_shape: the polygon to be represented in REST
        :return: the REST representation of a polygon
        """
        return {
            TYPE: RestShapeType.POLYGON.name,
            POINTS: [PredictionRESTViews.point_to_rest(p, media_height, media_width) for p in polygon_shape.points],
        }

    @staticmethod
    def rotated_rectangle_shape_to_rest(rotated_rectangle: Polygon, media_height: int, media_width: int) -> dict:
        """
        Returns the REST representation of a rotated rectangle.

        :param rotated_rectangle: the rotated rectangle to be represented in REST
        :param media_height: The height in pixels of the media
        :param media_width: The width in pixels of the media
        :raises: ValueError if the input polygon does not have 4 points
        :return: the REST representation of a polygon
        """
        if len(rotated_rectangle.points) != 4:
            raise ValueError("A rotated rectangle must have exactly 4 points.")

        for p in rotated_rectangle.points:
            p.x *= media_width
            p.y *= media_height

        x_max_coord = max(rotated_rectangle.points, key=operator.attrgetter("x"))
        x_min_coord = min(rotated_rectangle.points, key=operator.attrgetter("x"))
        y_max_coord = max(rotated_rectangle.points, key=operator.attrgetter("y"))
        y_min_coord = min(rotated_rectangle.points, key=operator.attrgetter("y"))

        x_center = (x_max_coord.x + x_min_coord.x) / 2
        y_center = (y_max_coord.y + y_min_coord.y) / 2

        height = math.sqrt((y_max_coord.y - x_max_coord.y) ** 2 + (x_max_coord.x - y_max_coord.x) ** 2)
        width = math.sqrt((x_max_coord.y - y_min_coord.y) ** 2 + (y_min_coord.x - x_max_coord.x) ** 2)

        delta_y = rotated_rectangle.points[2].y - rotated_rectangle.points[1].y
        delta_x = rotated_rectangle.points[2].x - rotated_rectangle.points[1].x

        angle = math.atan2(delta_y, delta_x)
        while angle < 0.0:
            angle += math.pi * 2
        angle *= 180 / math.pi
        angle += 90
        if angle >= 360:
            angle -= 360
        if 270 < angle < 360 or 90 < angle < 180:
            height, width = width, height

        angle_rounded = round(angle, 3)  # rounding to avoid floating-point error
        if angle_rounded in (0, 360):
            width = rotated_rectangle.points[0].x - rotated_rectangle.points[1].x
            height = rotated_rectangle.points[1].y - rotated_rectangle.points[2].y
        elif angle_rounded == 90:
            width = rotated_rectangle.points[0].y - rotated_rectangle.points[1].y
            height = rotated_rectangle.points[2].x - rotated_rectangle.points[1].x
        elif angle_rounded == 180:
            width = rotated_rectangle.points[1].x - rotated_rectangle.points[0].x
            height = rotated_rectangle.points[2].y - rotated_rectangle.points[1].y
        elif angle_rounded == 270:
            width = rotated_rectangle.points[2].y - rotated_rectangle.points[3].y
            height = rotated_rectangle.points[1].x - rotated_rectangle.points[2].x

        return {
            TYPE: RestShapeType.ROTATED_RECTANGLE.name,
            X: round(x_center, 4),
            Y: round(y_center, 4),
            WIDTH: round(width, 4),
            HEIGHT: round(height, 4),
            ANGLE: round(angle, 4),
        }

    @staticmethod
    def predictions_results_to_rest(
        prediction_results: VPSPredictionResults,
        media_identifier: MediaIdentifierEntity | None,
        media_width: int,
        media_height: int,
    ) -> dict[str, Any]:
        """
        Converts VPS predictions to their REST representation.

        :param prediction_results: The VPS prediction results.
        :param media_identifier: The media identifier of the media the predictions are for.
        :param media_width: The width of the media.
        :param media_height: The height of the media.
        :return: The REST representation of the predictions.
        """
        predictions_rest = []

        # convert bounding boxes to REST
        for annotation in prediction_results.bboxes:
            shape = annotation.shape
            if not isinstance(shape, Rectangle):
                logger.warning(f"Skipping annotation with shape `{annotation.shape}` as it is not a rectangle.")
                continue
            rectangle_rest = PredictionRESTViews.rectangle_shape_to_rest(
                rectangle_shape=shape, media_height=media_height, media_width=media_width
            )
            labels_rest = [
                ScoredLabelRESTViews.scored_label_to_rest(label) for label in annotation.get_labels(include_empty=True)
            ]
            annotation_rest = {
                "labels": labels_rest,
                "shape": rectangle_rest,
            }
            predictions_rest.append(annotation_rest)

        # convert rotated bounding boxes to REST
        for annotation in prediction_results.rotated_bboxes:
            shape = annotation.shape
            if not isinstance(shape, Polygon):
                logger.warning(f"Skipping annotation with shape `{annotation.shape}` as it is not a rotated rectangle.")
                continue
            rot_rectangle_rest = PredictionRESTViews.rotated_rectangle_shape_to_rest(
                rotated_rectangle=shape, media_height=media_height, media_width=media_width
            )
            labels_rest = [
                ScoredLabelRESTViews.scored_label_to_rest(label) for label in annotation.get_labels(include_empty=True)
            ]
            annotation_rest = {
                "labels": labels_rest,
                "shape": rot_rectangle_rest,
            }
            predictions_rest.append(annotation_rest)

        # convert polygons to REST
        for annotation in prediction_results.polygons:
            shape = annotation.shape
            if not isinstance(shape, Polygon):
                logger.warning(f"Skipping annotation with shape `{annotation.shape}` as it is not a polygon.")
                continue
            polygon_rest = PredictionRESTViews._polygon_shape_to_rest(
                polygon_shape=shape, media_height=media_height, media_width=media_width
            )
            labels_rest = [
                ScoredLabelRESTViews.scored_label_to_rest(label) for label in annotation.get_labels(include_empty=True)
            ]
            annotation_rest = {
                "labels": labels_rest,
                "shape": polygon_rest,
            }
            predictions_rest.append(annotation_rest)

        rest_view: dict[str, Any] = {
            "predictions": predictions_rest,
            "created": now().isoformat(),
        }
        if media_identifier:
            rest_view["media_identifier"] = MediaIdentifierRESTViews.media_identifier_to_rest(media_identifier)
        return rest_view
