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

from collections.abc import Sequence

import pytest
from pytest import FixtureRequest

from tests.fixtures.values import DummyValues, IDOffsets

from geti_types import ID, ProjectIdentifier
from sc_sdk.entities.color import Color
from sc_sdk.entities.label import Domain, Label
from sc_sdk.entities.label_schema import LabelGroup, LabelGroupType, LabelSchema, LabelSchemaView, LabelTree
from sc_sdk.entities.scored_label import LabelSource, ScoredLabel
from sc_sdk.repos import LabelRepo, LabelSchemaRepo


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
def fxt_empty_classification_label_sdk(fxt_ote_id):
    yield Label(
        name="Empty classification label",
        domain=Domain.CLASSIFICATION,
        color=Color.from_hex_str("#ff0000"),
        hotkey=DummyValues.LABEL_HOTKEY,
        is_empty=True,
        id_=fxt_ote_id(IDOffsets.CLASSIFICATION_LABELS + 100),
    )


@pytest.fixture
def fxt_classification_labels_sdk(fxt_ote_id, fxt_empty_classification_label_sdk):
    yield [
        Label(
            name=name,
            domain=Domain.CLASSIFICATION,
            hotkey=f"CTRL+{index}",
            creation_date=DummyValues.CREATION_DATE,
            id_=fxt_ote_id(IDOffsets.CLASSIFICATION_LABELS + index),
        )
        for index, name in enumerate(DummyValues.LABEL_NAMES)
    ] + [fxt_empty_classification_label_sdk]


@pytest.fixture
def fxt_classification_labels_persisted(
    request: FixtureRequest,
    fxt_classification_labels_sdk,
):
    def _build_and_persist_labels(project_identifier: ProjectIdentifier) -> list[Label]:
        label_repo = LabelRepo(project_identifier)
        label_repo.save_many(list(fxt_classification_labels_sdk))
        request.addfinalizer(lambda: label_repo.delete_all())
        return fxt_classification_labels_sdk

    yield _build_and_persist_labels


def label_schema_from_labels(labels: Sequence[Label]) -> LabelSchema:
    """
    Create a LabelSchema from a list of labels.

    :param labels: list of labels
    :return: LabelSchema from the given labels
    """
    label_group = LabelGroup(name="from_label_list", labels=labels)
    return LabelSchema(id_=LabelSchemaRepo.generate_id(), label_groups=[label_group])


@pytest.fixture
def fxt_empty_label_schema(fxt_ote_id):
    yield LabelSchema(id_=fxt_ote_id(IDOffsets.EMTPY_LABEL_SCHEMA))


@pytest.fixture
def fxt_label_with_id(fxt_mongo_id):
    def _build_item(id_offset: int = 0):
        return Label(
            name=DummyValues.LABEL_NAME,
            domain=Domain.DETECTION,
            color=Color.from_hex_str("#ff0000"),
            hotkey=DummyValues.LABEL_HOTKEY,
            id_=ID(fxt_mongo_id(id_offset)),
        )

    yield _build_item


@pytest.fixture
def fxt_detection_label_factory(fxt_mongo_id):
    def _build_label(index: int) -> Label:
        return Label(
            name=f"test detection label {index}",
            domain=Domain.DETECTION,
            color=Color.from_hex_str("#ff0000"),
            hotkey=DummyValues.LABEL_HOTKEY,
            id_=ID(fxt_mongo_id(2000 + index)),
        )

    yield _build_label


@pytest.fixture
def fxt_detection_label(fxt_detection_label_factory):
    yield fxt_detection_label_factory(0)


@pytest.fixture
def fxt_detection_label_rest(fxt_detection_label):
    yield {
        "id": str(fxt_detection_label.id_),
        "name": fxt_detection_label.name,
        "color": fxt_detection_label.color,
        "hotkey": fxt_detection_label.hotkey,
        "group": "",
        "is_empty": False,
        "parent_id": None,
    }


@pytest.fixture
def fxt_classification_label_factory(fxt_mongo_id):
    def _build_label(index: int) -> Label:
        return Label(
            name=f"test classification label {index}",
            domain=DummyValues.CLASSIFICATION_DOMAIN,
            color=Color.from_hex_str("#ff0000"),
            hotkey=DummyValues.LABEL_HOTKEY,
            id_=ID(fxt_mongo_id(1000 + index)),
        )

    yield _build_label


@pytest.fixture
def fxt_classification_label(fxt_classification_label_factory):
    yield fxt_classification_label_factory(0)


@pytest.fixture
def fxt_classification_label_rest(fxt_classification_label):
    yield {
        "id": str(fxt_classification_label.id_),
        "name": fxt_classification_label.name,
        "color": fxt_classification_label.color,
        "hotkey": fxt_classification_label.hotkey,
        "group": "",
        "is_empty": False,
        "parent_id": None,
    }


@pytest.fixture
def fxt_segmentation_label_factory(fxt_mongo_id):
    def _build_label(index: int) -> Label:
        return Label(
            name=f"test segmentation label {index}",
            domain=DummyValues.SEGMENTATION_DOMAIN,
            color=Color.from_hex_str("#ff0000"),
            hotkey=DummyValues.LABEL_HOTKEY,
            id_=ID(fxt_mongo_id(3000 + index)),
        )

    yield _build_label


@pytest.fixture
def fxt_segmentation_label(fxt_segmentation_label_factory):
    yield fxt_segmentation_label_factory(0)


@pytest.fixture
def fxt_anomaly_classification_labels(fxt_mongo_id):
    normal_label = Label(
        name="Normal",
        domain=Domain.ANOMALY_CLASSIFICATION,
        color=Color(red=139, green=174, blue=70),
        id_=fxt_mongo_id(51),
        is_anomalous=False,
    )
    anomalous_label = Label(
        name="Anomalous",
        domain=Domain.ANOMALY_CLASSIFICATION,
        color=Color(red=255, green=86, blue=98),
        id_=fxt_mongo_id(52),
        is_anomalous=True,
    )
    yield [normal_label, anomalous_label]


@pytest.fixture
def fxt_anomaly_classification_label(fxt_anomaly_classification_labels):
    yield fxt_anomaly_classification_labels[0]


@pytest.fixture
def fxt_anomaly_segmentation_labels(fxt_mongo_id):
    normal_label = Label(
        name="Normal",
        domain=Domain.ANOMALY_SEGMENTATION,
        color=Color(red=139, green=174, blue=70),
        id_=fxt_mongo_id(51),
        is_anomalous=False,
    )
    anomalous_label = Label(
        name="Anomalous",
        domain=Domain.ANOMALY_SEGMENTATION,
        color=Color(red=255, green=86, blue=98),
        id_=fxt_mongo_id(52),
        is_anomalous=True,
    )
    yield [normal_label, anomalous_label]


@pytest.fixture
def fxt_empty_detection_label(fxt_mongo_id):
    yield Label(
        name="Empty detection label",
        domain=Domain.DETECTION,
        color=Color.from_hex_str("#ff0000"),
        hotkey=DummyValues.LABEL_HOTKEY,
        is_empty=True,
        id_=ID(fxt_mongo_id(100)),
    )


@pytest.fixture
def fxt_empty_classification_label(fxt_mongo_id):
    yield Label(
        name="Empty classification label",
        domain=DummyValues.CLASSIFICATION_DOMAIN,
        color=Color.from_hex_str("#ff0000"),
        hotkey=DummyValues.LABEL_HOTKEY,
        is_empty=True,
        id_=ID(fxt_mongo_id(101)),
    )


@pytest.fixture
def fxt_empty_segmentation_label(fxt_mongo_id):
    yield Label(
        name="Empty segmentation label",
        domain=DummyValues.SEGMENTATION_DOMAIN,
        color=Color.from_hex_str("#ff0000"),
        hotkey=DummyValues.LABEL_HOTKEY,
        is_empty=True,
        id_=ID(fxt_mongo_id(102)),
    )


@pytest.fixture
def fxt_label(fxt_mongo_id):
    yield Label(
        name=DummyValues.LABEL_NAME,
        domain=Domain.DETECTION,
        color=DummyValues.LABEL_COLOR,
        hotkey=DummyValues.LABEL_HOTKEY,
        id_=ID(fxt_mongo_id(1)),
    )


@pytest.fixture
def fxt_label_rest(fxt_label):
    yield {
        "id": str(fxt_label.id_),
        "name": DummyValues.LABEL_NAME,
        "color": "#ff0000ff",
        "hotkey": DummyValues.LABEL_HOTKEY,
        "group": "",
        "is_empty": False,
        "is_anomalous": False,
        "parent_id": None,
    }


@pytest.fixture(scope="function")
def fxt_classification_labels_good_bad():
    return [
        Label(
            name="good",
            domain=Domain.CLASSIFICATION,
            color=Color(red=0, green=255, blue=0),
            id_=LabelRepo.generate_id(),
        ),
        Label(
            name="bad", domain=Domain.CLASSIFICATION, color=Color(red=255, green=0, blue=0), id_=LabelRepo.generate_id()
        ),
    ]


@pytest.fixture(scope="function")
def fxt_classification_label_schema_good_bad(fxt_classification_labels_good_bad):
    return LabelSchemaView.from_labels(fxt_classification_labels_good_bad)


@pytest.fixture
def fxt_classification_labels(fxt_classification_label, fxt_empty_classification_label):
    return [fxt_classification_label, fxt_empty_classification_label]


@pytest.fixture
def fxt_classification_label_schema(fxt_classification_labels):
    yield LabelSchemaView.from_labels(fxt_classification_labels)


@pytest.fixture
def fxt_classification_label_schema_factory(
    fxt_classification_label_factory, fxt_empty_classification_label, fxt_mongo_id
):
    """
    Create a label schema for a classification task with a customizable number of labels
    """

    def _build_schema(
        num_labels: int = 2,
        multilabel: bool = False,
        hierarchical: bool = False,
        **kwargs,
    ) -> LabelSchema:
        """
        :param num_labels: total number of labels
        :param multilabel: if True, each label is put in a separate exclusive group
        :param hierarchical: if True, the first label is set as parent of the other ones
        """
        if num_labels == 1:
            schema = label_schema_from_labels([fxt_classification_label_factory(0), fxt_empty_classification_label])
        else:
            labels = [fxt_classification_label_factory(i) for i in range(num_labels)]
            if multilabel:
                groups = [
                    LabelGroup(
                        name=f"test classification group {i}",
                        labels=[labels[i]],
                        group_type=LabelGroupType.EXCLUSIVE,
                    )
                    for i in range(num_labels)
                ]
                schema = LabelSchema(id_=fxt_mongo_id(21), label_groups=groups)
            else:
                schema = label_schema_from_labels(labels=labels)
            if hierarchical:
                for child in labels[1:]:
                    schema.add_child(labels[0], child)
        return schema

    yield _build_schema


@pytest.fixture(scope="function")
def fxt_detection_labels(fxt_empty_detection_label, fxt_detection_label):
    return [fxt_empty_detection_label, fxt_detection_label]


@pytest.fixture
def fxt_detection_label_schema(fxt_detection_labels):
    yield LabelSchemaView.from_labels(fxt_detection_labels)


@pytest.fixture
def fxt_detection_label_schema_factory(fxt_detection_label_factory, fxt_empty_detection_label):
    """
    Create a label schema for a detection task with a customizable number of labels
    """

    def _build_schema(num_labels: int = 1, **kwargs) -> LabelSchema:
        """
        :param num_labels: total number of labels
        """
        if num_labels == 1:
            schema = label_schema_from_labels([fxt_detection_label_factory(0), fxt_empty_detection_label])
        else:
            schema = label_schema_from_labels([fxt_detection_label_factory(i) for i in range(num_labels)])
        return schema

    yield _build_schema


@pytest.fixture
def fxt_segmentation_labels(fxt_segmentation_label, fxt_empty_segmentation_label):
    return [fxt_segmentation_label, fxt_empty_segmentation_label]


@pytest.fixture
def fxt_segmentation_label_schema(fxt_segmentation_labels):
    yield LabelSchemaView.from_labels(fxt_segmentation_labels)


@pytest.fixture
def fxt_segmentation_label_schema_factory(fxt_segmentation_label_factory, fxt_empty_segmentation_label):
    """
    Create a label schema for a segmentation task with a customizable number of labels
    """

    def _build_schema(num_labels: int = 2, **kwargs) -> LabelSchema:
        """
        :param num_labels: total number of labels
        """
        if num_labels == 1:
            schema = label_schema_from_labels([fxt_segmentation_label_factory(0), fxt_empty_segmentation_label])
        else:
            schema = label_schema_from_labels([fxt_segmentation_label_factory(i) for i in range(num_labels)])
        return schema

    yield _build_schema


@pytest.fixture
def fxt_anomaly_classificaction_label_schema(fxt_anomaly_classification_labels):
    yield LabelSchemaView.from_labels(fxt_anomaly_classification_labels)


@pytest.fixture
def fxt_anomaly_segmentation_label_schema(fxt_anomaly_segmentation_labels):
    yield LabelSchemaView.from_labels(fxt_anomaly_segmentation_labels)


@pytest.fixture
def fxt_label_schema(fxt_label):
    yield LabelSchemaView.from_labels([fxt_label])


@pytest.fixture
def fxt_detection_classification_label_schema(
    fxt_detection_label_schema, fxt_classification_label_schema, fxt_mongo_id
):
    det_labels = fxt_detection_label_schema.get_labels(include_empty=True)
    cls_labels = fxt_classification_label_schema.get_labels(include_empty=True)
    det_label_group = LabelGroup(
        name="Detection Group",
        labels=det_labels,
        group_type=LabelGroupType.EXCLUSIVE,
    )
    cls_label_group = LabelGroup(
        name="Classification Group",
        labels=cls_labels,
        group_type=LabelGroupType.EXCLUSIVE,
    )
    non_empty_det_label = next(label for label in det_labels if not label.is_empty)
    label_tree = LabelTree()
    for cls_label in cls_labels:
        label_tree.add_child(non_empty_det_label, cls_label)
    yield LabelSchema(id_=fxt_mongo_id(11), label_tree=label_tree, label_groups=[det_label_group, cls_label_group])


@pytest.fixture
def fxt_detection_classification_label_schema_factory(
    fxt_detection_label_schema_factory,
    fxt_classification_label_schema_factory,
):
    def _build_schema(
        num_det_labels: int = 1,
        num_cls_labels: int = 2,
        multilabel_cls: bool = False,
        hierarchical_cls: bool = False,
    ) -> LabelSchema:
        """
        :param num_det_labels: total number of detection labels
        :param num_cls_labels: total number of classification labels
        :param multilabel_cls: if True, each classification label is put in a separate exclusive group
        :param hierarchical_cls: if True, the first classification label is set as parent of the other ones
        """
        det_labels = fxt_detection_label_schema_factory(num_labels=num_det_labels).get_labels(include_empty=True)
        cls_labels = fxt_classification_label_schema_factory(
            num_labels=num_cls_labels,
            multilabel=multilabel_cls,
            hierarchical=hierarchical_cls,
        ).get_labels(include_empty=True)
        det_label_group = LabelGroup(
            name="Detection Group",
            labels=det_labels,
            group_type=LabelGroupType.EXCLUSIVE,
        )
        if multilabel_cls:
            cls_label_groups = [
                LabelGroup(
                    name=f"Classification group {i}",
                    labels=[cls_labels[i]],
                    group_type=LabelGroupType.EXCLUSIVE,
                )
                for i in range(num_cls_labels)
            ]
        else:
            cls_label_groups = [
                LabelGroup(
                    name="Classification Group",
                    labels=cls_labels,
                    group_type=LabelGroupType.EXCLUSIVE,
                )
            ]
        groups = [det_label_group, *cls_label_groups]
        non_empty_det_label = next(label for label in det_labels if not label.is_empty)
        label_tree = LabelTree()
        if hierarchical_cls:
            label_tree.add_child(non_empty_det_label, cls_labels[0])
            for cls_child in cls_labels[1:]:
                label_tree.add_child(cls_labels[0], cls_child)
        else:
            for cls_label in cls_labels:
                label_tree.add_child(non_empty_det_label, cls_label)
        return LabelSchema(id_=LabelSchemaRepo.generate_id(), label_tree=label_tree, label_groups=groups)

    yield _build_schema


@pytest.fixture
def fxt_detection_segmentation_label_schema_factory(
    fxt_detection_label_schema_factory,
    fxt_segmentation_label_schema_factory,
):
    def _build_schema(num_det_labels: int = 2, num_seg_labels: int = 2) -> LabelSchema:
        det_labels = fxt_detection_label_schema_factory(num_labels=num_det_labels).get_labels(include_empty=True)
        cls_labels = fxt_segmentation_label_schema_factory(num_labels=num_seg_labels).get_labels(include_empty=True)
        det_label_group = LabelGroup(
            name="Detection Group",
            labels=det_labels,
            group_type=LabelGroupType.EXCLUSIVE,
        )
        seg_label_group = LabelGroup(
            name="Segmentation Group",
            labels=cls_labels,
            group_type=LabelGroupType.EXCLUSIVE,
        )
        return LabelSchema(id_=LabelSchemaRepo.generate_id(), label_groups=[det_label_group, seg_label_group])

    yield _build_schema


@pytest.fixture
def fxt_label_source(fxt_ote_id):
    yield LabelSource(user_id="dummy_user", model_id=fxt_ote_id(1), model_storage_id=fxt_ote_id(2))


@pytest.fixture
def fxt_scored_label(fxt_label, fxt_ote_id, fxt_label_source):
    yield ScoredLabel(
        label_id=fxt_label.id_,
        is_empty=fxt_label.is_empty,
        probability=DummyValues.LABEL_PROBABILITY,
        label_source=fxt_label_source,
    )


@pytest.fixture
def fxt_scored_label_rest(fxt_scored_label):
    yield {
        "id": str(fxt_scored_label.id_),
        "probability": DummyValues.LABEL_PROBABILITY,
        "source": {
            "user_id": fxt_scored_label.label_source.user_id,
            "model_id": str(fxt_scored_label.label_source.model_id),
            "model_storage_id": str(fxt_scored_label.label_source.model_storage_id),
        },
    }


@pytest.fixture
def fxt_classification_scored_label_rest_factory(
    fxt_classification_label_schema_factory,
):
    def _build_scored_label(num_labels: int, idx: int = 0):
        label_schema = fxt_classification_label_schema_factory(num_labels=num_labels)
        labels = label_schema.get_labels(False)
        return {
            "id": str(labels[idx].id_),
            "name": labels[idx].name,
            "probability": 0.5,
            "color": "#ff0000ff",
        }

    yield _build_scored_label


@pytest.fixture
def fxt_detection_scored_label_rest_factory(fxt_detection_label_schema_factory):
    def _build_scored_label(num_labels: int, idx: int = 0):
        label_schema = fxt_detection_label_schema_factory(num_labels=num_labels)
        labels = label_schema.get_labels(False)
        return {
            "id": str(labels[idx].id_),
            "name": labels[idx].name,
            "probability": 0.5,
            "color": "#ff0000ff",
        }

    yield _build_scored_label


@pytest.fixture
def fxt_segmentation_scored_label_rest_factory(fxt_segmentation_label_schema_factory):
    def _build_scored_label(num_labels: int, idx: int = 0):
        label_schema = fxt_segmentation_label_schema_factory(num_labels=num_labels)
        labels = label_schema.get_labels(False)
        return {
            "id": str(labels[idx].id_),
            "name": labels[idx].name,
            "probability": 0.5,
            "color": "#ff0000ff",
        }

    yield _build_scored_label
