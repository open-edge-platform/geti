import unittest
from unittest.mock import Mock

from services.rest_views.prediction_rest_views import PredictionRESTViews, RestShapeType
from services.visual_prompt_service import VPSPredictionResults

from geti_types import ID, ImageIdentifier
from sc_sdk.entities.shapes import Point, Polygon, Rectangle


class TestPredictionRESTViews(unittest.TestCase):
    def test_rectangle_shape_to_rest_returns_correct_representation(self):
        rectangle = Rectangle(x1=0.1, y1=0.2, x2=0.3, y2=0.4)
        result = PredictionRESTViews.rectangle_shape_to_rest(rectangle, media_height=1000, media_width=2000)
        expected = {
            "type": RestShapeType.RECTANGLE.name,
            "x": 200,
            "y": 200,
            "width": 400,
            "height": 200,
        }
        self.assertEqual(result, expected)

    def test_point_to_rest_returns_correct_representation(self):
        point = Point(x=0.5, y=0.5)
        result = PredictionRESTViews.point_to_rest(point, media_height=1000, media_width=2000)
        expected = {
            "x": 1000,
            "y": 500,
        }
        self.assertEqual(result, expected)

    def test_rotated_rectangle_shape_to_rest_raises_value_error_for_invalid_polygon(self):
        polygon = Polygon(points=[Point(0, 0), Point(1, 0), Point(1, 1)])
        with self.assertRaises(ValueError):
            PredictionRESTViews.rotated_rectangle_shape_to_rest(polygon, media_height=1000, media_width=2000)

    def test_rotated_rectangle_shape_to_rest_returns_correct_representation(self):
        polygon = Polygon(points=[Point(0, 0), Point(1, 0), Point(1, 1), Point(0, 1)])
        result = PredictionRESTViews.rotated_rectangle_shape_to_rest(polygon, media_height=1000, media_width=2000)
        expected = {
            "type": RestShapeType.ROTATED_RECTANGLE.name,
            "x": 1000.0,
            "y": 500.0,
            "width": 2000.0,
            "height": 1000.0,
            "angle": 180.0,
        }
        self.assertEqual(result, expected)

    def test_predictions_results_to_rest_returns_correct_representation(self):
        prediction_results = VPSPredictionResults(
            bboxes=[Mock(shape=Rectangle(x1=0.1, y1=0.2, x2=0.3, y2=0.4), get_labels=Mock(return_value=[]))],
            rotated_bboxes=[
                Mock(
                    shape=Polygon(points=[Point(0, 0), Point(1, 0), Point(1, 1), Point(0, 1)]),
                    get_labels=Mock(return_value=[]),
                )
            ],
            polygons=[
                Mock(
                    shape=Polygon(points=[Point(0, 0), Point(1, 0), Point(1, 1), Point(0, 1)]),
                    get_labels=Mock(return_value=[]),
                )
            ],
        )
        media_identifier = ImageIdentifier(image_id=ID("test_id"))
        result = PredictionRESTViews.predictions_results_to_rest(
            prediction_results, media_identifier, media_width=2000, media_height=1000
        )
        self.assertIn("predictions", result)
        self.assertIn("created", result)
        self.assertIn("media_identifier", result)
