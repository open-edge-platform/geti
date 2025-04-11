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
from _pytest.fixtures import FixtureRequest

from sc_sdk.entities.label import Color, Domain, Label
from sc_sdk.entities.label_schema import LabelSchemaView
from sc_sdk.entities.scored_label import ScoredLabel
from sc_sdk.repos import LabelRepo

from .values import DummyValues, IDOffsets
from geti_types import ID, ProjectIdentifier


@pytest.fixture
def fxt_empty_classification_label(fxt_ote_id):
    yield Label(
        name="Empty classification label",
        domain=Domain.CLASSIFICATION,
        color=Color.from_hex_str("#ff0000"),
        hotkey=DummyValues.LABEL_HOTKEY,
        is_empty=True,
        id_=fxt_ote_id(IDOffsets.CLASSIFICATION_LABELS + 100),
    )


@pytest.fixture
def fxt_classification_labels(fxt_ote_id, fxt_empty_classification_label):
    yield [
        Label(
            name=name,
            domain=Domain.CLASSIFICATION,
            hotkey=f"CTRL+{index}",
            creation_date=DummyValues.CREATION_DATE,
            id_=fxt_ote_id(IDOffsets.CLASSIFICATION_LABELS + index),
        )
        for index, name in enumerate(DummyValues.LABEL_NAMES)
    ] + [fxt_empty_classification_label]


@pytest.fixture
def fxt_classification_labels_persisted(
    request: FixtureRequest,
    fxt_classification_labels,
):
    def _build_and_persist_labels(project_identifier: ProjectIdentifier) -> list[Label]:
        label_repo = LabelRepo(project_identifier)
        label_repo.save_many(list(fxt_classification_labels))
        request.addfinalizer(lambda: label_repo.delete_all())
        return fxt_classification_labels

    yield _build_and_persist_labels


@pytest.fixture
def fxt_empty_detection_label(fxt_ote_id):
    yield Label(
        name="Empty detection label",
        domain=Domain.DETECTION,
        color=Color.from_hex_str("#ff0000"),
        hotkey=DummyValues.LABEL_HOTKEY,
        is_empty=True,
        id_=fxt_ote_id(IDOffsets.DETECTION_LABELS + 100),
    )


@pytest.fixture
def fxt_detection_labels(fxt_ote_id, fxt_empty_detection_label):
    yield [
        Label(
            name=name,
            domain=Domain.DETECTION,
            hotkey=f"CTRL+{index}",
            creation_date=DummyValues.CREATION_DATE,
            id_=fxt_ote_id(IDOffsets.DETECTION_LABELS + index),
        )
        for index, name in enumerate(DummyValues.LABEL_NAMES)
    ] + [fxt_empty_detection_label]


@pytest.fixture
def fxt_detection_labels_persisted(
    request: FixtureRequest,
    fxt_detection_labels,
):
    def _build_and_persist_labels(project_identifier: ProjectIdentifier) -> list[Label]:
        label_repo = LabelRepo(project_identifier)
        label_repo.save_many(list(fxt_detection_labels))
        request.addfinalizer(lambda: label_repo.delete_all())
        return fxt_detection_labels

    yield _build_and_persist_labels


@pytest.fixture
def fxt_segmentation_labels(fxt_ote_id, fxt_empty_segmentation_label):
    yield [
        Label(
            name=name,
            domain=Domain.SEGMENTATION,
            hotkey=f"CTRL+{index}",
            creation_date=DummyValues.CREATION_DATE,
            id_=fxt_ote_id(IDOffsets.SEGMENTATION_LABELS + index),
        )
        for index, name in enumerate(DummyValues.LABEL_NAMES)
    ] + [fxt_empty_segmentation_label]


@pytest.fixture
def fxt_empty_segmentation_label(fxt_ote_id):
    yield Label(
        name="Empty segmentation label",
        domain=Domain.SEGMENTATION,
        color=Color.from_hex_str("#ff0000"),
        hotkey=DummyValues.LABEL_HOTKEY,
        is_empty=True,
        id_=fxt_ote_id(IDOffsets.SEGMENTATION_LABELS + 100),
    )


@pytest.fixture
def fxt_segmentation_labels_persisted(
    request: FixtureRequest,
    fxt_segmentation_labels,
):
    def _build_and_persist_labels(project_identifier: ProjectIdentifier) -> list[Label]:
        label_repo = LabelRepo(project_identifier)
        label_repo.save_many(list(fxt_segmentation_labels))
        request.addfinalizer(lambda: label_repo.delete_all())
        return fxt_segmentation_labels

    yield _build_and_persist_labels


@pytest.fixture
def fxt_rotated_detection_labels(fxt_ote_id):
    yield [
        Label(
            name=name,
            domain=Domain.ROTATED_DETECTION,
            hotkey=f"CTRL+{index}",
            creation_date=DummyValues.CREATION_DATE,
            id_=fxt_ote_id(IDOffsets.ROTATED_DETECTION_LABELS + index),
        )
        for index, name in enumerate(DummyValues.LABEL_NAMES)
    ]


@pytest.fixture
def fxt_empty_rotated_detection_label(fxt_ote_id):
    yield Label(
        name="Empty rotated detection label",
        domain=Domain.ROTATED_DETECTION,
        color=Color.from_hex_str("#ff0000"),
        hotkey=DummyValues.LABEL_HOTKEY,
        is_empty=True,
        id_=fxt_ote_id(IDOffsets.ROTATED_DETECTION_LABELS + 100),
    )


@pytest.fixture
def fxt_label(fxt_mongo_id):
    yield Label(
        name=DummyValues.LABEL_NAME,
        domain=Domain.DETECTION,
        color=Color.from_hex_str("#ff0000"),
        hotkey=DummyValues.LABEL_HOTKEY,
        id_=ID(fxt_mongo_id(1)),
    )


@pytest.fixture
def fxt_anomalous_label(fxt_mongo_id):
    yield Label(
        name=DummyValues.LABEL_NAME,
        domain=Domain.ANOMALY_DETECTION,
        color=Color.from_hex_str("#ff0000"),
        hotkey=DummyValues.LABEL_HOTKEY,
        id_=ID(fxt_mongo_id(2)),
        is_anomalous=True,
    )


@pytest.fixture
def fxt_scored_label(fxt_label):
    yield ScoredLabel(label_id=fxt_label.id_, probability=DummyValues.LABEL_PROBABILITY)


@pytest.fixture
def fxt_anomalous_scored_label(fxt_anomalous_label):
    yield ScoredLabel(label_id=fxt_anomalous_label.id_, probability=DummyValues.LABEL_PROBABILITY)


@pytest.fixture
def fxt_detection_label_schema(fxt_detection_labels):
    yield LabelSchemaView.from_labels(fxt_detection_labels)


@pytest.fixture
def fxt_classification_label_schema(fxt_classification_labels):
    yield LabelSchemaView.from_labels(fxt_classification_labels)


@pytest.fixture
def fxt_segmentation_label_schema(fxt_segmentation_labels):
    yield LabelSchemaView.from_labels(fxt_segmentation_labels)
