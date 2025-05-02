# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from _pytest.fixtures import FixtureRequest

from iai_core_py.entities.color import Color
from iai_core_py.entities.label import Domain, Label
from iai_core_py.entities.label_schema import LabelGroup, LabelGroupType, LabelSchema
from iai_core_py.entities.project import Project
from iai_core_py.entities.task_node import TaskNode
from iai_core_py.repos import LabelRepo, LabelSchemaRepo

from .values import IDOffsets


class LabelSchemaExample:
    """
    Utility class to generate and manage a sample label schema.

    If no schema is provided from outside, one will be created with the following structure:
    - group 'plant_state'
      - label 'flowering'
        - subgroup 'flowering_state'
          - label 'flower_partial_visible'
          - label 'flower_fully_visible'
      - label 'no_plant'
      - label 'vegetative'
        - subgroup 'leaf_state'
          - label 'few_leaves'
    All groups are EXCLUSIVE with domain CLASSIFICATION
    The six labels are accessible through attributes with the same name of that label.

    The LabelSchema is accessible through the 'label_schema' attribute.
    """

    def __init__(
        self,
        request,
        project: Project,
        task_node: TaskNode,
        label_schema: LabelSchema | None = None,
        save_to_repo: bool = False,
    ) -> None:
        self.save_to_repo = save_to_repo
        self._request = request
        self.project = project
        self.task_node = task_node
        self.label_domain = task_node.task_properties.task_type.domain

        self.flowering = self.new_label_by_name("flowering")
        self.no_plant = self.new_label_by_name("no_plant")
        self.vegetative = self.new_label_by_name("vegetative")
        self.flower_partial_visible = self.new_label_by_name("flower_partial_visible")
        self.flower_fully_visible = self.new_label_by_name("flower_fully_visible")
        self.few_leaves = self.new_label_by_name("few_leaves")

        if label_schema is None:
            label_schema = LabelSchema(id_=LabelSchemaRepo.generate_id(), project_id=project.id_)
        if not label_schema.get_labels(include_empty=True):
            self.add_hierarchy(label_schema)
        self.label_schema = label_schema

    def new_label_by_name(self, name: str) -> Label:
        label = Label(name=name, domain=self.label_domain, color=Color.random(), id_=LabelRepo.generate_id())
        if self.save_to_repo:
            label_repo = LabelRepo(self.project.identifier)
            label_repo.save(label)
            self._request.addfinalizer(lambda: label_repo.delete_by_id(label.id_))
        return label

    def add_hierarchy(self, label_schema: LabelSchema):
        """Adds children to flowering, no_plant and vegetative"""
        label_schema.add_group(
            LabelGroup(
                "plant_state",
                [self.flowering, self.no_plant, self.vegetative],
                LabelGroupType.EXCLUSIVE,
            )
        )
        label_schema.add_group(
            LabelGroup(
                "flowering_state",
                [self.flower_fully_visible, self.flower_partial_visible],
                LabelGroupType.EXCLUSIVE,
            )
        )
        label_schema.add_child(self.flowering, self.flower_partial_visible)
        label_schema.add_child(self.flowering, self.flower_fully_visible)

        assert self.flowering == label_schema.get_parent(self.flower_partial_visible)
        assert label_schema.get_parent(self.no_plant) is None

        label_schema.add_group(LabelGroup("leaf_state", [self.few_leaves], LabelGroupType.EXCLUSIVE))
        label_schema.add_child(self.vegetative, self.few_leaves)
        if self.save_to_repo:
            label_schema_repo = LabelSchemaRepo(self.project.identifier)
            label_schema_repo.save(label_schema)
            self._request.addfinalizer(lambda: label_schema_repo.delete_by_id(label_schema.id_))


@pytest.fixture
def fxt_empty_label_schema(fxt_ote_id):
    yield LabelSchema(id_=fxt_ote_id(IDOffsets.EMTPY_LABEL_SCHEMA))


@pytest.fixture
def fxt_empty_label_schema_persisted(
    request: FixtureRequest,
    fxt_empty_label_schema,
    fxt_empty_project,
):
    label_schema_repo = LabelSchemaRepo(fxt_empty_project.identifier)
    label_schema_repo.save(fxt_empty_label_schema)
    request.addfinalizer(lambda: label_schema_repo.delete_by_id(fxt_empty_label_schema.id_))
    return fxt_empty_label_schema


@pytest.fixture
def fxt_label_schema_factory(
    fxt_ote_id,
    fxt_classification_labels,
    fxt_detection_labels,
    fxt_empty_detection_label,
    fxt_segmentation_labels,
    fxt_empty_segmentation_label,
    fxt_rotated_detection_labels,
    fxt_empty_rotated_detection_label,
):
    domain_to_label_properties = {
        Domain.DETECTION: {
            "labels": fxt_detection_labels,
            "empty_label": fxt_empty_detection_label,
            "id": IDOffsets.DETECTION_LABEL_SCHEMA,
        },
        Domain.CLASSIFICATION: {
            "labels": fxt_classification_labels,
            "id": IDOffsets.CLASSIFICATION_LABEL_SCHEMA,
        },
        Domain.SEGMENTATION: {
            "labels": fxt_segmentation_labels,
            "empty_label": fxt_empty_segmentation_label,
            "id": IDOffsets.SEGMENTATION_LABEL_SCHEMA,
        },
        Domain.ROTATED_DETECTION: {
            "labels": fxt_rotated_detection_labels,
            "empty_label": fxt_empty_rotated_detection_label,
            "id": IDOffsets.ROTATED_DETACTION_LABEL_SCHEMA,
        },
    }

    def _label_schema_factory(domain: Domain):
        id_ = domain_to_label_properties[domain]["id"]
        labels = domain_to_label_properties[domain]["labels"]
        empty_label = domain_to_label_properties[domain].get("empty_label", None)
        label_schema = LabelSchema(id_=fxt_ote_id(id_))
        label_group = LabelGroup(labels=labels, name=f"dummy {domain.name.lower()} label group")
        label_schema.add_group(label_group)
        if empty_label is not None:
            empty_label_group = LabelGroup(
                labels=[empty_label],
                name=f"dummy {domain.name.lower()} empty group",
                group_type=LabelGroupType.EMPTY_LABEL,
            )
            label_schema.add_group(empty_label_group)
        return label_schema

    yield _label_schema_factory


@pytest.fixture
def fxt_label_schema_example(request, fxt_empty_project, fxt_classification_task):
    yield LabelSchemaExample(request, project=fxt_empty_project, task_node=fxt_classification_task)


@pytest.fixture
def fxt_label_schema_example_persisted(
    request,
    fxt_empty_project,
    fxt_classification_task,
):
    yield LabelSchemaExample(request, project=fxt_empty_project, task_node=fxt_classification_task, save_to_repo=True)
