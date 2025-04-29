#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

"""This module contains the MongoDB mapper for shape related entities"""

import math
from dataclasses import dataclass

from shapely.geometry import Polygon as ShapelyPolygon

from sc_sdk.entities.shapes import Ellipse, Keypoint, Point, Polygon, Rectangle, Shape, ShapeType
from sc_sdk.entities.shapes import ShapeType as SDK_ShapeType
from sc_sdk.repos.mappers.mongodb_mapper_interface import (
    IMapperBackward,
    IMapperParametricForward,
    IMapperSimple,
    MappingError,
)

from .primitive_mapper import DatetimeToMongo


@dataclass(frozen=True)
class ShapeToMongoForwardParameters:
    """Forward mapping parameters for `Shape`-derived classes"""

    media_height: int  # pixel
    media_width: int  # pixel
    # If include coordinates is False, the coordinates of the shape will not be mapped
    # Note that you can not unmap the documents without shape with the shape mapper!
    include_coordinates: bool = True


class ShapeToMongo(
    IMapperParametricForward[Shape, dict, ShapeToMongoForwardParameters],
    IMapperBackward[Shape, dict],
):
    """MongoDB mapper for `Shape` entities"""

    @staticmethod
    def forward(instance: Shape, parameters: ShapeToMongoForwardParameters) -> dict:
        if isinstance(instance, Rectangle):
            return RectangleToMongo.forward(instance, parameters=parameters)
        if isinstance(instance, Ellipse):
            return EllipseToMongo.forward(instance, parameters=parameters)
        if isinstance(instance, Polygon):
            return PolygonToMongo.forward(instance, parameters=parameters)
        if isinstance(instance, Keypoint):
            return KeypointToMongo.forward(instance, parameters=parameters)
        raise ValueError(f"No valid Shape provided, got {type(instance)}")

    @staticmethod
    def backward(instance: dict) -> Shape:
        if instance["type"] == ShapeType.RECTANGLE.name:
            shape = RectangleToMongo.backward(instance)
        elif instance["type"] == ShapeType.ELLIPSE.name:
            shape = EllipseToMongo.backward(instance)  # type: ignore
        elif instance["type"] == ShapeType.POLYGON.name:
            shape = PolygonToMongo.backward(instance)  # type: ignore
        elif instance["type"] == SDK_ShapeType.KEYPOINT.name:
            shape = KeypointToMongo.backward(instance)  # type: ignore
        else:
            raise MappingError(f"Shape ({instance['type']}) could not be recognized")

        return shape


class RectangleToMongo(
    IMapperParametricForward[Rectangle, dict, ShapeToMongoForwardParameters],
    IMapperBackward[Rectangle, dict],
):
    """MongoDB mapper for `Rectangle` entities"""

    @staticmethod
    def forward(instance: Rectangle, parameters: ShapeToMongoForwardParameters) -> dict:
        # TODO: Move area calculation to OTE SDK with implementation of CVS-83153
        pixel_area = ((instance.x2 - instance.x1) * parameters.media_width) * (
            (instance.y2 - instance.y1) * parameters.media_height
        )
        percentage_area = 0
        if parameters.media_width != 0 and parameters.media_height != 0:
            percentage_area = pixel_area / (parameters.media_width * parameters.media_height)  # type: ignore
        shape = {
            "type": instance.type.name,
            "modification_date": DatetimeToMongo.forward(instance.modification_date),
            "area_percentage": percentage_area,
            "area_pixel": pixel_area,
        }

        if parameters.include_coordinates:
            shape["x1"] = instance.x1
            shape["y1"] = instance.y1
            shape["x2"] = instance.x2
            shape["y2"] = instance.y2

        return shape

    @staticmethod
    def backward(instance: dict) -> Rectangle:
        modification_date = DatetimeToMongo.backward(instance.get("modification_date"))
        return Rectangle(
            x1=instance["x1"],
            y1=instance["y1"],
            x2=instance["x2"],
            y2=instance["y2"],
            modification_date=modification_date,
        )


class EllipseToMongo(
    IMapperParametricForward[Ellipse, dict, ShapeToMongoForwardParameters],
    IMapperBackward[Ellipse, dict],
):
    """MongoDB mapper for `Ellipse` entities"""

    @staticmethod
    def forward(instance: Ellipse, parameters: ShapeToMongoForwardParameters) -> dict:
        # TODO: Move area calculation to OTE SDK with implementation of CVS-83153
        pixel_area = (
            math.pi
            * ((instance.x2 - instance.x1) * parameters.media_width / 2)
            * ((instance.y2 - instance.y1) * parameters.media_height / 2)
        )
        percentage_area = 0
        if parameters.media_width != 0 and parameters.media_height != 0:
            percentage_area = pixel_area / (parameters.media_width * parameters.media_height)  # type: ignore
        shape = {
            "type": instance.type.name,
            "modification_date": DatetimeToMongo.forward(instance.modification_date),
            "area_percentage": percentage_area,
            "area_pixel": pixel_area,
        }

        if parameters.include_coordinates:
            shape["x1"] = instance.x1
            shape["y1"] = instance.y1
            shape["x2"] = instance.x2
            shape["y2"] = instance.y2

        return shape

    @staticmethod
    def backward(instance: dict) -> Ellipse:
        return Ellipse(
            x1=instance["x1"],
            y1=instance["y1"],
            x2=instance["x2"],
            y2=instance["y2"],
            modification_date=DatetimeToMongo.backward(instance.get("modification_date")),
        )


class PointToMongo(IMapperSimple[Point, dict]):
    """MongoDB mapper for `Point` entities"""

    @staticmethod
    def forward(instance: Point) -> dict:
        return {"x": instance.x, "y": instance.y}

    @staticmethod
    def backward(instance: dict) -> Point:
        return Point(x=instance["x"], y=instance["y"])


class PolygonToMongo(
    IMapperParametricForward[Polygon, dict, ShapeToMongoForwardParameters],
    IMapperBackward[Polygon, dict],
):
    """MongoDB mapper for `Polygon` entities"""

    @staticmethod
    def forward(
        instance: Polygon,
        parameters: ShapeToMongoForwardParameters,
    ) -> dict:
        # TODO: Move area calculation to OTE SDK with implementation of CVS-83153
        pixel_area = ShapelyPolygon(
            [(point.x * parameters.media_width, point.y * parameters.media_height) for point in instance.points]
        ).area
        percentage_area = 0
        if parameters.media_width != 0 and parameters.media_height != 0:
            percentage_area = pixel_area / (parameters.media_width * parameters.media_height)
        shape = {
            "type": instance.type.name,
            "modification_date": DatetimeToMongo.forward(instance.modification_date),
            "area_percentage": percentage_area,
            "area_pixel": pixel_area,
        }

        if parameters.include_coordinates:
            shape["points"] = [PointToMongo.forward(p) for p in instance.points]

        return shape

    @staticmethod
    def backward(instance: dict) -> Polygon:
        points = [PointToMongo.backward(p) for p in instance["points"]]
        return Polygon(
            points=points,
            modification_date=DatetimeToMongo.backward(instance.get("modification_date")),
        )


class KeypointToMongo(
    IMapperParametricForward[Keypoint, dict, ShapeToMongoForwardParameters],
    IMapperBackward[Keypoint, dict],
):
    """MongoDB mapper for `Keypoint` entities"""

    @staticmethod
    def forward(
        instance: Keypoint,
        parameters: ShapeToMongoForwardParameters,
    ) -> dict:
        shape = {
            "type": instance.type.name,
            "modification_date": DatetimeToMongo.forward(instance.modification_date),
            "area_percentage": 1 / (parameters.media_width * parameters.media_height),
            "area_pixel": 1,
        }

        if parameters.include_coordinates:
            shape["x"] = instance.x
            shape["y"] = instance.y
            shape["is_visible"] = instance.is_visible

        return shape

    @staticmethod
    def backward(instance: dict) -> Keypoint:
        return Keypoint(
            x=instance["x"],
            y=instance["y"],
            is_visible=instance["is_visible"],
            modification_date=DatetimeToMongo.backward(instance.get("modification_date")),
        )
