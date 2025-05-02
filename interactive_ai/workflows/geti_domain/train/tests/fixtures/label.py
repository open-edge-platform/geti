# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from geti_types import ID
from iai_core.entities.color import Color
from iai_core.entities.label import Domain, Label
from iai_core.entities.label_schema import LabelGroup, LabelSchema
from iai_core.entities.scored_label import ScoredLabel

from tests.fixtures.values import DummyValues


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
def fxt_scored_label(fxt_label):
    yield ScoredLabel(label_id=fxt_label.id_, probability=DummyValues.LABEL_PROBABILITY)


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
