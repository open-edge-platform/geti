# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from iai_core.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from iai_core.entities.annotation_scene_state import AnnotationSceneState
from iai_core.entities.shapes import Rectangle
from iai_core.repos import AnnotationSceneStateRepo

from tests.fixtures.values import DummyValues


@pytest.fixture
def fxt_rectangle_annotation(fxt_scored_label):
    yield Annotation(
        shape=Rectangle(
            x1=DummyValues.X,
            x2=DummyValues.X + DummyValues.WIDTH,
            y1=DummyValues.Y,
            y2=DummyValues.Y + DummyValues.HEIGHT,
            modification_date=DummyValues.MODIFICATION_DATE,
        ),
        labels=[fxt_scored_label],
        id_=DummyValues.UUID,
    )


@pytest.fixture
def fxt_anomalous_rectangle_annotation(fxt_anomalous_scored_label):
    yield Annotation(
        shape=Rectangle(
            x1=DummyValues.X,
            x2=DummyValues.X + DummyValues.WIDTH,
            y1=DummyValues.Y,
            y2=DummyValues.Y + DummyValues.HEIGHT,
            modification_date=DummyValues.MODIFICATION_DATE,
        ),
        labels=[fxt_anomalous_scored_label],
        id_=DummyValues.UUID,
    )


@pytest.fixture
def fxt_annotation_scene(
    fxt_ote_id,
    fxt_image_identifier,
    fxt_rectangle_annotation,
):
    yield AnnotationScene(
        kind=DummyValues.ANNOTATION_SCENE_KIND,
        media_identifier=fxt_image_identifier,
        media_height=DummyValues.MEDIA_HEIGHT,
        media_width=DummyValues.MEDIA_WIDTH,
        id_=fxt_ote_id(),
        last_annotator_id=DummyValues.ANNOTATION_EDITOR_NAME,
        creation_date=DummyValues.MODIFICATION_DATE,
        annotations=[
            fxt_rectangle_annotation,
        ],
    )


@pytest.fixture
def fxt_annotation_scene_factory(
    fxt_ote_id,
    fxt_image_identifier,
    fxt_rectangle_annotation,
):
    def _build_scene(index: int = 0) -> AnnotationScene:
        return AnnotationScene(
            kind=DummyValues.ANNOTATION_SCENE_KIND,
            media_identifier=fxt_image_identifier,
            media_height=DummyValues.MEDIA_HEIGHT,
            media_width=DummyValues.MEDIA_WIDTH,
            id_=fxt_ote_id(index),
            last_annotator_id=DummyValues.ANNOTATION_EDITOR_NAME,
            creation_date=DummyValues.MODIFICATION_DATE,
            annotations=[
                fxt_rectangle_annotation,
            ],
        )

    yield _build_scene


@pytest.fixture
def fxt_annotation_scene_anomalous(
    fxt_ote_id,
    fxt_image_identifier,
    fxt_anomalous_rectangle_annotation,
):
    yield AnnotationScene(
        kind=DummyValues.ANNOTATION_SCENE_KIND,
        media_identifier=fxt_image_identifier,
        media_height=DummyValues.MEDIA_HEIGHT,
        media_width=DummyValues.MEDIA_WIDTH,
        id_=fxt_ote_id(),
        last_annotator_id=DummyValues.ANNOTATION_EDITOR_NAME,
        creation_date=DummyValues.MODIFICATION_DATE,
        annotations=[
            fxt_anomalous_rectangle_annotation,
        ],
    )


@pytest.fixture
def fxt_annotation_scene_prediction(
    fxt_ote_id,
    fxt_image_identifier,
    fxt_rectangle_annotation,
):
    yield AnnotationScene(
        kind=AnnotationSceneKind.PREDICTION,
        media_identifier=fxt_image_identifier,
        media_height=DummyValues.MEDIA_HEIGHT,
        media_width=DummyValues.MEDIA_WIDTH,
        id_=fxt_ote_id(),
        last_annotator_id=DummyValues.ANNOTATION_EDITOR_NAME,
        creation_date=DummyValues.MODIFICATION_DATE,
        annotations=[
            fxt_rectangle_annotation,
        ],
    )


@pytest.fixture
def fxt_annotation_scene_state(fxt_annotation_scene, fxt_rectangle_annotation):
    yield AnnotationSceneState(
        media_identifier=fxt_annotation_scene.media_identifier,
        annotation_scene_id=fxt_annotation_scene.id_,
        annotation_state_per_task={},
        unannotated_rois={},
        id_=AnnotationSceneStateRepo.generate_id(),
    )
