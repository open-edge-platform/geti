# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from sc_sdk.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from sc_sdk.entities.color import Color
from sc_sdk.entities.label import Domain, Label
from sc_sdk.entities.scored_label import ScoredLabel
from sc_sdk.entities.shapes import Point, Polygon, Rectangle
from sc_sdk.utils.time_utils import now

from geti_types import ID


class TestAnnotation:
    rectangle = Rectangle(x1=0.5, x2=1.0, y1=0.0, y2=0.5)
    labels: list[ScoredLabel] = []
    annotation = Annotation(shape=rectangle, labels=labels)

    car = Label(
        name="car",
        domain=Domain.DETECTION,
        color=Color(red=16, green=15, blue=56, alpha=255),
        is_empty=True,
        id_=ID("car_label"),
    )
    person = Label(
        name="person",
        domain=Domain.DETECTION,
        color=Color(red=11, green=18, blue=38, alpha=200),
        is_empty=False,
        id_=ID("person_label"),
    )
    car_label = ScoredLabel(label_id=car.id_, is_empty=car.is_empty)
    person_label = ScoredLabel(label_id=person.id_, is_empty=person.is_empty)
    labels2 = [car_label, person_label]

    def test_annotation_get_labels(self):
        """
        <b>Description:</b>
        Check Annotation get_labels method

        <b>Input data:</b>
        Initialized instance of Annotation

        <b>Expected results:</b>
        Test passes if Annotation get_labels method returns correct values

        <b>Steps</b>
        1. Create Annotation instances
        2. Check returning value of get_labels method
        3. Check returning value of get_labels method with include_empty=True
        """
        annotation = Annotation(shape=self.rectangle, labels=self.labels2)

        assert annotation.get_labels() == [self.person_label]
        assert annotation.get_labels(include_empty=True) == [self.car_label, self.person_label]

    def test_annotation_get_label_ids(self):
        """
        <b>Description:</b>
        Check Annotation get_label_ids method

        <b>Input data:</b>
        Initialized instance of Annotation

        <b>Expected results:</b>
        Test passes if Annotation get_label_ids method returns correct values

        <b>Steps</b>
        1. Create Annotation instances
        2. Check returning value of get_label_ids method
        3. Check returning value of get_label_ids method with include_empty=True
        """

        annotation = Annotation(shape=self.rectangle, labels=self.labels2)

        assert annotation.get_label_ids() == {ID("person_label")}
        assert annotation.get_label_ids(include_empty=True) == {
            ID("car_label"),
            ID("person_label"),
        }

    def test_annotation_append_label(self):
        """
        <b>Description:</b>
        Check Annotation append_label method

        <b>Input data:</b>
        Initialized instance of Annotation

        <b>Expected results:</b>
        Test passes if Annotation append_label method correct appending label

        <b>Steps</b>
        1. Create Annotation instances
        2. Append label
        3. Check labels
        """

        annotation = self.annotation

        annotation.append_label(label=self.car_label)
        assert annotation.get_labels() == []  # car_label is empty

        annotation.append_label(label=self.person_label)
        assert annotation.get_labels() == [self.person_label]

    def test_annotation_set_labels(self):
        """
        <b>Description:</b>
        Check Annotation set_labels method

        <b>Input data:</b>
        Initialized instance of Annotation

        <b>Expected results:</b>
        Test passes if Annotation set_labels method correct setting label

        <b>Steps</b>
        1. Create Annotation instances
        2. Set labels
        3. Check labels
        """

        annotation = self.annotation
        assert annotation.get_labels() != []

        annotation.set_labels(labels=[])
        assert annotation.get_labels() == []

        annotation.set_labels(labels=self.labels2)
        assert annotation.get_labels() == [self.person_label]


class TestAnnotationScene:
    creation_date = now()
    labels: list[ScoredLabel] = []
    rectangle = Rectangle(x1=0.5, x2=1.0, y1=0.0, y2=0.5)
    annotation = Annotation(shape=rectangle, labels=labels)

    point1 = Point(0.3, 0.1)
    point2 = Point(0.8, 0.3)
    point3 = Point(0.6, 0.2)
    points = [point1, point2, point3]
    polygon = Polygon(points=points)
    annotation2 = Annotation(shape=polygon, labels=labels)

    annotations = [annotation, annotation2]

    annotation_scene_entity = AnnotationScene(kind=AnnotationSceneKind.ANNOTATION, annotations=annotations)

    def test_annotation_scene_entity_contains_any(self):
        """
        <b>Description:</b>
        Check Annotation contains_any method

        <b>Input data:</b>
        Initialized instance of AnnotationScene

        <b>Expected results:</b>
        Test passes if AnnotationScene contains_any method returns correct values

        <b>Steps</b>
        1. Create AnnotationScene instances
        2. Check returning value of contains_any method
        """

        annotation_scene_entity = self.annotation_scene_entity
        annotation_scene_entity.annotations = self.annotations

        car = Label(ID("car"), name="car", domain=Domain.DETECTION, is_empty=True)
        person = Label(ID("person"), name="person", domain=Domain.DETECTION)
        tree = Label(ID("tree"), name="tree", domain=Domain.DETECTION)
        car_label = ScoredLabel(label_id=car.id_, is_empty=car.is_empty)
        person_label = ScoredLabel(label_id=person.id_, is_empty=person.is_empty)
        tree_label = ScoredLabel(label_id=tree.id_, is_empty=tree.is_empty)
        labels = [car_label]
        labels2 = [car_label, person_label]

        annotation = Annotation(shape=self.rectangle, labels=labels2)
        annotations = [annotation]
        annotation_scene_entity2 = AnnotationScene(kind=AnnotationSceneKind.ANNOTATION, annotations=annotations)

        assert annotation_scene_entity.contains_any(labels=labels) is False
        assert annotation_scene_entity2.contains_any(labels=labels2) is True
        assert annotation_scene_entity2.contains_any(labels=[tree_label]) is False

    def test_annotation_scene_entity_append_annotation(self):
        """
        <b>Description:</b>
        Check Annotation append_annotation method

        <b>Input data:</b>
        Initialized instance of AnnotationScene

        <b>Expected results:</b>
        Test passes if AnnotationScene append_annotation method returns correct values

        <b>Steps</b>
        1. Create AnnotationScene instances
        2. Check returning value of append_annotation method
        """

        annotation_scene_entity = self.annotation_scene_entity

        tree = Label(ID("tree"), name="tree", domain=Domain.DETECTION)
        tree_label = ScoredLabel(label_id=tree.id_, is_empty=tree.is_empty)
        labels = [tree_label]
        annotation = Annotation(shape=self.rectangle, labels=labels)

        assert len(annotation_scene_entity.annotations) == 2

        annotation_scene_entity.append_annotation(annotation)
        assert len(annotation_scene_entity.annotations) == 3

    def test_annotation_scene_entity_append_annotations(self):
        """
        <b>Description:</b>
        Check Annotation append_annotations method

        <b>Input data:</b>
        Initialized instance of AnnotationScene

        <b>Expected results:</b>
        Test passes if AnnotationScene append_annotations method returns correct values

        <b>Steps</b>
        1. Create AnnotationScene instances
        2. Check returning value of append_annotations method
        """

        annotation_scene_entity = self.annotation_scene_entity
        annotation_scene_entity.append_annotations(self.annotations)
        assert len(annotation_scene_entity.annotations) == 6

    def test_annotation_scene_entity_get_labels(self):
        """
        <b>Description:</b>
        Check Annotation get_labels method

        <b>Input data:</b>
        Initialized instance of AnnotationScene

        <b>Expected results:</b>
        Test passes if AnnotationScene get_labels method returns correct values

        <b>Steps</b>
        1. Create AnnotationScene instances
        2. Check returning value of get_labels method
        """

        annotation_scene_entity = self.annotation_scene_entity

        assert annotation_scene_entity.get_label_ids() == {ID("tree")}

    def test_annotation_scene_entity_get_label_ids(self):
        """
        <b>Description:</b>
        Check Annotation get_label_ids method

        <b>Input data:</b>
        Initialized instance of AnnotationScene

        <b>Expected results:</b>
        Test passes if AnnotationScene get_label_ids method returns correct values

        <b>Steps</b>
        1. Create AnnotationScene instances
        2. Check returning value of get_label_ids method
        """

        annotation_scene_entity = self.annotation_scene_entity

        assert annotation_scene_entity.get_label_ids() == {ID("tree")}

        bus = Label(name="bus", domain=Domain.DETECTION, id_=ID(123456789))
        bus_label = ScoredLabel(label_id=bus.id_, is_empty=bus.is_empty)
        labels = [bus_label]
        annotation = Annotation(shape=self.rectangle, labels=labels)
        annotation_scene_entity.append_annotation(annotation)

        assert annotation_scene_entity.get_label_ids() == {ID("tree"), ID(123456789)}
