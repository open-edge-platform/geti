# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import datetime
import uuid
from typing import cast
from unittest.mock import MagicMock, patch

import datumaro as dm
import pytest
from geti_types import ID, DatasetStorageIdentifier
from iai_core.entities.annotation import Annotation
from iai_core.entities.datasets import Dataset
from iai_core.entities.label import Label
from iai_core.entities.label_schema import LabelSchema
from iai_core.entities.scored_label import ScoredLabel
from iai_core.entities.shapes import Ellipse, Keypoint, Point, Polygon, Rectangle

from jobs_common_extras.datumaro_conversion.mappers.annotation_scene_mapper import AnnotationSceneMapper, LabelMap
from jobs_common_extras.datumaro_conversion.mappers.dataset_item_mapper import (
    EllipseMapper,
    KeypointMapper,
    LabelMapper,
    PolygonMapper,
    RectangleMapper,
    RoIMapper,
    ShapeMapper,
)
from jobs_common_extras.datumaro_conversion.mappers.label_mapper import LabelSchemaMapper


@pytest.mark.CommonComponent
class TestLabelSchemaMapper:
    @pytest.mark.parametrize("include_empty", [True, False])
    def test_label_schema_mapper(
        self,
        fxt_dataset_and_label_schema: tuple[DatasetStorageIdentifier, Dataset, LabelSchema],
        include_empty: bool,
    ) -> None:
        _, _, expect = fxt_dataset_and_label_schema
        label_schema_info = LabelSchemaMapper.forward(label_schema=expect, include_empty=include_empty)

        actual_labels = list(label_schema_info.label_cat)
        expect_labels = expect.get_labels(include_empty)

        assert len(actual_labels) == len(expect_labels)

        for a_label, e_label in zip(actual_labels, expect_labels):
            assert a_label.name == e_label.id_
            assert f"__name__{e_label.name}" in a_label.attributes
            assert f"__color__{e_label.color.hex_str}" in a_label.attributes
            assert f"__hotkey__{e_label.hotkey}" in a_label.attributes
            assert f"{e_label.domain}" in a_label.attributes

        actual_groups = label_schema_info.label_cat.label_groups
        expect_groups = expect.get_groups(include_empty)

        assert len(actual_groups) == len(expect_groups)
        for a_group, e_group in zip(actual_groups, expect_groups):
            assert a_group.name == e_group.name
            a_grpname = a_group.group_type.name
            e_grpname = e_group.group_type.name
            assert a_grpname == e_grpname or (a_grpname == "RESTRICTED" and e_grpname == "EMPTY_LABEL")
            assert a_group.labels == [label.name for label in e_group.labels]


class TestRectangleMapper:
    def test_forward(self) -> None:
        modification_date = datetime.datetime.now(tz=datetime.timezone.utc)
        rectangle = Rectangle(0.2, 0.3, 0.4, 0.5, modification_date=modification_date)
        expected_mapped_rectangle = {
            "type": "RECTANGLE",
            "modification_date": modification_date.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "x1": 0.2,
            "y1": 0.3,
            "x2": 0.4,
            "y2": 0.5,
        }

        mapped_rectangle = RectangleMapper.forward(rectangle)

        assert mapped_rectangle == expected_mapped_rectangle


class TestEllipseMapper:
    def test_forward(self) -> None:
        modification_date = datetime.datetime.now(tz=datetime.timezone.utc)
        ellipse = Ellipse(0.2, 0.3, 0.4, 0.5, modification_date=modification_date)
        expected_mapped_ellipse = {
            "type": "ELLIPSE",
            "modification_date": modification_date.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "x1": 0.2,
            "y1": 0.3,
            "x2": 0.4,
            "y2": 0.5,
        }

        mapped_ellipse = EllipseMapper.forward(ellipse)

        assert mapped_ellipse == expected_mapped_ellipse


class TestPolygonMapper:
    def test_forward(self) -> None:
        modification_date = datetime.datetime.now(tz=datetime.timezone.utc)
        polygon = Polygon(
            points=[Point(0.1, 0.2), Point(0.3, 0.4), Point(0.5, 0.2)],
            modification_date=modification_date,
        )
        expected_mapped_polygon = {
            "type": "POLYGON",
            "modification_date": modification_date.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "points": [
                {"x": 0.1, "y": 0.2},
                {"x": 0.3, "y": 0.4},
                {"x": 0.5, "y": 0.2},
            ],
        }

        mapped_polygon = PolygonMapper.forward(polygon)

        assert mapped_polygon == expected_mapped_polygon


class TestKeypointMapper:
    def test_forward(self) -> None:
        modification_date = datetime.datetime.now(tz=datetime.timezone.utc)
        keypoint = Keypoint(x=0.5, y=0.6, is_visible=True, modification_date=modification_date)
        expected_mapped_keypoint = {
            "type": "KEYPOINT",
            "points": [0.5, 0.6],
            "modification_date": modification_date.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "visibility": [dm.Points.Visibility.visible],
        }

        mapped_keypoint = KeypointMapper.forward(keypoint)

        assert mapped_keypoint == expected_mapped_keypoint


class TestShapeMapper:
    @pytest.mark.parametrize(
        "shape",
        [
            Rectangle(0.2, 0.3, 0.4, 0.5),
            Ellipse(0.2, 0.3, 0.4, 0.5),
            Polygon(points=[Point(0.1, 0.2), Point(0.3, 0.4), Point(0.5, 0.2)]),
        ],
        ids=["rectangle", "ellipse", "polygon"],
    )
    def test_forward(self, shape) -> None:
        mock_mapped_shape = {"key": "value"}
        with (
            patch.object(RectangleMapper, "forward", return_value=mock_mapped_shape) as mock_rectangle_forward,
            patch.object(EllipseMapper, "forward", return_value=mock_mapped_shape) as mock_ellipse_forward,
            patch.object(PolygonMapper, "forward", return_value=mock_mapped_shape) as mock_polygon_forward,
        ):
            mapped_shape = ShapeMapper.forward(shape)

        if isinstance(shape, Rectangle):
            mock_rectangle_forward.assert_called_once_with(shape)
        elif isinstance(shape, Ellipse):
            mock_ellipse_forward.assert_called_once_with(shape)
        else:
            mock_polygon_forward.assert_called_once_with(shape)
        assert mapped_shape == mock_mapped_shape


class TestRoiMapper:
    def test_forward(self) -> None:
        roi_id = ID(str(uuid.uuid4()))
        roi_date = datetime.datetime.now(tz=datetime.timezone.utc)
        mocked_label = cast(Label, MagicMock(spec=Label))
        label_id = ID(str(uuid.uuid4()))
        label_map = {label_id: mocked_label}
        roi_label = ScoredLabel(label_id=label_id, is_empty=False, probability=0.8)
        roi = Annotation(shape=Rectangle(0.2, 0.3, 0.4, 0.5), labels=[roi_label], id_=roi_id)
        mocked_mapped_label = {"_id": str(label_id), "name": "cat"}
        mocked_mapped_shape = {"type": "rectangle", "modification_date": roi_date}
        expected_mapped_roi = {
            "id": str(roi_id),
            "shape": mocked_mapped_shape,
            "labels": [{"label": mocked_mapped_label, "probability": 0.8}],
        }

        with (
            patch.object(ShapeMapper, "forward", return_value=mocked_mapped_shape) as mock_shape_forward,
            patch.object(LabelMapper, "forward", return_value=mocked_mapped_label) as mock_label_forward,
        ):
            mapped_roi = RoIMapper.forward(roi=roi, label_id_to_label=label_map, include_empty=True)

        mock_shape_forward.assert_called_once()
        mock_label_forward.assert_called_once_with(mocked_label)
        assert mapped_roi == expected_mapped_roi


class TestAnnotationSceneMapper:
    def test_forward(self, fxt_annotation_scene, fxt_anomalous_rectangle_annotation) -> None:
        fxt_annotation_scene.append_annotation(fxt_anomalous_rectangle_annotation)
        mocked_label_map = MagicMock(spec=LabelMap)
        mocked_label_map.include_empty = True
        task_label_id = next(
            iter(annotation.get_labels()[0].label_id for annotation in fxt_annotation_scene.annotations)
        )
        mocked_label_map.get_dm_label_by_sc_label_id = lambda arg: 5 if arg == task_label_id else None
        expected_mapped_annotation_scene = [
            dm.Bbox(
                x=240,
                y=120,
                w=160,
                h=60,
                label=5,
                attributes=None,
            )
        ]

        mapped_annotation_scene = AnnotationSceneMapper(label_map=mocked_label_map).forward(fxt_annotation_scene)

        assert mapped_annotation_scene == expected_mapped_annotation_scene
