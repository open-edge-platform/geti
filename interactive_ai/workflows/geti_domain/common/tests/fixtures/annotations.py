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

import pytest
from sc_sdk.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from sc_sdk.entities.annotation_scene_state import AnnotationSceneState
from sc_sdk.entities.shapes import Rectangle
from sc_sdk.repos import AnnotationSceneStateRepo

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
