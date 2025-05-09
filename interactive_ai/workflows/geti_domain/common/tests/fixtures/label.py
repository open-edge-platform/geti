# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from _pytest.fixtures import FixtureRequest
from geti_types import ID, ProjectIdentifier
from iai_core.entities.label import Color, Domain, Label
from iai_core.entities.label_schema import LabelGroup, LabelSchema, LabelSchemaView
from iai_core.entities.scored_label import ScoredLabel
from iai_core.repos import LabelRepo

from tests.fixtures.values import DummyValues, IDOffsets


@pytest.fixture
def fxt_label_schema_id(fxt_mongo_id):
    return fxt_mongo_id(14)


@pytest.fixture
def fxt_detection_label_schema(fxt_mongo_id, fxt_label_schema_id):
    label_schema = LabelSchema(fxt_label_schema_id)
    label_schema.add_group(
        LabelGroup(
            name="default detection",
            labels=[
                Label(name="detection label", domain=Domain.DETECTION, id_=fxt_mongo_id(1)),
                Label(
                    name="Empty detection label",
                    domain=Domain.DETECTION,
                    is_empty=True,
                    id_=fxt_mongo_id(7),
                ),
            ],
        )
    )
    yield label_schema


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
        id_=ID(fxt_mongo_id(13)),
        is_anomalous=True,
    )


@pytest.fixture
def fxt_anomaly_labels_factory(fxt_mongo_id):
    def _build_anom_labels(domain: Domain) -> list[Label]:
        if domain not in (
            Domain.ANOMALY_CLASSIFICATION,
            Domain.ANOMALY_SEGMENTATION,
            Domain.ANOMALY_DETECTION,
        ):
            raise ValueError("This fixtures only generates anomaly labels.")
        normal_label = Label(
            name="dummy_normal_label",
            domain=domain,
            color=Color.from_hex_str("#00BF00"),
            hotkey=DummyValues.LABEL_HOTKEY,
            id_=ID(fxt_mongo_id(1)),
            is_anomalous=False,
        )
        anomalous_label = Label(
            name="dummy_anomalous_label",
            domain=domain,
            color=Color.from_hex_str("#ff0000"),
            hotkey=DummyValues.LABEL_HOTKEY,
            id_=ID(fxt_mongo_id(2)),
            is_anomalous=True,
        )
        return [normal_label, anomalous_label]

    yield _build_anom_labels


@pytest.fixture
def fxt_scored_label(fxt_label):
    yield ScoredLabel(
        label_id=fxt_label.id_,
        is_empty=fxt_label.is_empty,
        probability=DummyValues.LABEL_PROBABILITY,
    )


@pytest.fixture
def fxt_anomalous_scored_label(fxt_anomalous_label):
    yield ScoredLabel(
        label_id=fxt_anomalous_label.id_,
        is_empty=fxt_anomalous_label.is_empty,
        probability=DummyValues.LABEL_PROBABILITY,
    )


@pytest.fixture
def fxt_classification_label_schema(fxt_classification_labels):
    yield LabelSchemaView.from_labels(fxt_classification_labels)


@pytest.fixture
def fxt_segmentation_label_schema(fxt_segmentation_labels):
    yield LabelSchemaView.from_labels(fxt_segmentation_labels)


@pytest.fixture
def fxt_keypoint_label(fxt_mongo_id):
    yield [
        Label(
            name="head",
            domain=Domain.KEYPOINT_DETECTION,
            id_=ID(fxt_mongo_id(1)),
            color=Color.from_hex_str("#ff0000"),
            hotkey=DummyValues.LABEL_HOTKEY,
            is_anomalous=False,
        ),
        Label(
            name="tail",
            domain=Domain.KEYPOINT_DETECTION,
            id_=ID(fxt_mongo_id(2)),
            color=Color.from_hex_str("#ffff00"),
            hotkey=DummyValues.LABEL_HOTKEY,
            is_anomalous=False,
        ),
    ]
