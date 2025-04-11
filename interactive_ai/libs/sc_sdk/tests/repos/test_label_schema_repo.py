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
from unittest.mock import ANY, call, patch

import pytest

from sc_sdk.entities.label import Domain, Label
from sc_sdk.entities.label_schema import LabelGroup, LabelSchema, LabelSchemaView, LabelTree
from sc_sdk.repos import LabelRepo, LabelSchemaRepo
from sc_sdk.repos.base import SessionBasedRepo


def make_tree_from_labels(labels: Sequence[Label]) -> LabelTree:
    label_tree = LabelTree()
    for lbl in labels:
        label_tree.add_node(lbl)
    for lbl in labels[1:]:
        label_tree.add_edge(labels[0], lbl)
    return label_tree


def make_group_from_labels(labels: Sequence[Label]) -> LabelGroup:
    return LabelGroup("test_label_group", labels=labels)


def assert_schemas_have_same_id_and_labels(ls1: LabelSchema, ls2: LabelSchema):
    assert ls1.id_ == ls2.id_
    labels_ids_1 = {lbl.id_ for lbl in ls1.label_tree.nodes}
    labels_ids_2 = {lbl.id_ for lbl in ls2.label_tree.nodes}
    assert labels_ids_1 == labels_ids_2


@pytest.mark.ScSdkComponent
class TestLabelSchemaRepo:
    def test_indexes(self, fxt_project_identifier) -> None:
        label_schema_repo = LabelSchemaRepo(fxt_project_identifier)

        indexes_names = set(label_schema_repo._collection.index_information().keys())

        assert indexes_names == {
            "_id_",
            "organization_id_-1_workspace_id_-1_project_id_-1__id_1",
            "task_node_id_-1",
        }

    @pytest.mark.parametrize("is_view", [False, True], ids=["full project schema", "task schema view"])
    def test_save(self, fxt_label_schema_repo, fxt_labels, fxt_ote_id, is_view) -> None:
        # Assert
        label_schema_repo = fxt_label_schema_repo
        project_labels = fxt_labels[:3]
        task_labels = project_labels[:2]
        label_tree = make_tree_from_labels(project_labels)
        label_group = make_group_from_labels(project_labels)
        label_schema = LabelSchema(
            id_=LabelSchemaRepo.generate_id(),
            label_tree=label_tree,
            label_groups=[label_group],
            project_id=fxt_label_schema_repo.identifier.project_id,
        )
        label_schema_view = LabelSchemaView.from_parent(
            parent_schema=label_schema,
            labels=task_labels,
            id_=LabelSchemaRepo.generate_id(),
        )
        with (
            patch.object(LabelRepo, "save_many") as mock_save_labels,
            patch.object(SessionBasedRepo, "save") as mock_super_save,
        ):
            # Act
            if is_view:
                label_schema_repo.save(label_schema_view)
            else:
                label_schema_repo.save(label_schema)

        # Assert
        # Note: the order in which the labels are saved is unstable, so we check with set()
        assert mock_save_labels.call_count == 1
        saved_labels = mock_save_labels.call_args_list[0].kwargs["instances"]
        if is_view:
            assert set(saved_labels) == set(task_labels)
            mock_super_save.assert_has_calls(
                [
                    call(label_schema, mongodb_session=ANY),
                    call(label_schema_view, mongodb_session=ANY),
                ]
            )
        else:
            assert set(saved_labels) == set(project_labels)
            mock_super_save.assert_called_once_with(label_schema, mongodb_session=ANY)

    def test_get_latest(  # note: the import order of the fixtures determines which schemas are saved first
        self,
        fxt_label_schema_repo,
        fxt_label_schema_1_persisted,
        fxt_label_schema_2_persisted,
        fxt_label_schema_view_persisted,
    ) -> None:
        # Arrange
        label_schema_repo: LabelSchemaRepo = fxt_label_schema_repo

        # Act
        schema_2_reloaded = label_schema_repo.get_latest()
        schema_view_reloaded = label_schema_repo.get_latest(include_views=True)

        # Assert
        assert_schemas_have_same_id_and_labels(schema_2_reloaded, fxt_label_schema_2_persisted)
        assert_schemas_have_same_id_and_labels(schema_view_reloaded, fxt_label_schema_view_persisted)

    def test_get_deleted_label_ids(  # note: the import order of the fixtures determines which schemas are saved first
        self,
        fxt_label_schema_repo,
        fxt_labels,
        fxt_label_schema_1_persisted,
        fxt_label_schema_2_persisted,
        fxt_label_schema_view_persisted,
    ) -> None:
        # Arrange
        label_schema_repo: LabelSchemaRepo = fxt_label_schema_repo
        label_schema_2_labels = fxt_label_schema_2_persisted.get_labels(True)
        label_schema_2_groups = fxt_label_schema_2_persisted.get_groups(True)
        fxt_label_schema_2_persisted.add_labels_to_group_by_group_name(
            group_name=label_schema_2_groups[0].name, labels=[fxt_labels[0]]
        )
        fxt_label_schema_2_persisted.deleted_label_ids = [label_schema_2_labels[0].id_]
        label_schema_repo.save(fxt_label_schema_2_persisted)

        # Act
        deleted_label_ids = label_schema_repo.get_deleted_label_ids()

        # Assert
        assert deleted_label_ids == (label_schema_2_labels[0].id_,)

    def test_get_latest_view_by_task(  # note: the import order of the fixtures determines which schemas are saved first
        self,
        fxt_label_schema_repo,
        fxt_label_schema_1_persisted,
        fxt_label_schema_view_persisted,
        fxt_label_schema_2_persisted,
    ) -> None:
        # Arrange
        label_schema_repo: LabelSchemaRepo = fxt_label_schema_repo

        # Act
        schema_view_reloaded = label_schema_repo.get_latest_view_by_task(
            task_node_id=fxt_label_schema_view_persisted.task_node_id,
        )

        # Assert
        assert_schemas_have_same_id_and_labels(schema_view_reloaded, fxt_label_schema_view_persisted)

    @pytest.fixture
    def fxt_labels(self, request, fxt_empty_project_persisted):
        label_repo = LabelRepo(fxt_empty_project_persisted.identifier)
        labels = [
            Label(name="label_1", domain=Domain.DETECTION, id_=LabelRepo.generate_id()),
            Label(name="label_2", domain=Domain.CLASSIFICATION, id_=LabelRepo.generate_id()),
            Label(name="label_3", domain=Domain.DETECTION, id_=LabelRepo.generate_id()),
            Label(name="label_4", domain=Domain.SEGMENTATION, id_=LabelRepo.generate_id()),
            Label(name="label_5", domain=Domain.DETECTION, id_=LabelRepo.generate_id()),
            Label(name="label_6", domain=Domain.DETECTION, id_=LabelRepo.generate_id()),
        ]
        for lbl in labels:
            label_repo.save(lbl)
            request.addfinalizer(lambda: label_repo.delete_by_id(lbl.id_))
        yield labels

    @pytest.fixture
    def fxt_label_schema_repo(self, fxt_empty_project_persisted):
        label_schema_repo = LabelSchemaRepo(fxt_empty_project_persisted.identifier)
        yield label_schema_repo

    @pytest.fixture
    def fxt_label_schema_1_persisted(self, request, fxt_mongo_id, fxt_labels, fxt_label_schema_repo):
        label_tree_12 = make_tree_from_labels(fxt_labels[:2])
        label_group = make_group_from_labels(fxt_labels[:2])
        label_schema_1 = LabelSchema(
            id_=LabelSchemaRepo.generate_id(),
            label_tree=label_tree_12,
            label_groups=[label_group],
            project_id=fxt_mongo_id(1),
        )
        fxt_label_schema_repo.save(label_schema_1)
        request.addfinalizer(lambda: fxt_label_schema_repo.delete_by_id(label_schema_1.id_))
        yield label_schema_1

    @pytest.fixture
    def fxt_label_schema_2_persisted(self, request, fxt_mongo_id, fxt_labels, fxt_label_schema_repo):
        label_tree_34 = make_tree_from_labels(fxt_labels[2:4])
        label_group = make_group_from_labels(fxt_labels[2:4])
        label_schema_2 = LabelSchema(
            id_=LabelSchemaRepo.generate_id(),
            label_tree=label_tree_34,
            label_groups=[label_group],
            project_id=fxt_mongo_id(1),
        )
        fxt_label_schema_repo.save(label_schema_2)
        request.addfinalizer(lambda: fxt_label_schema_repo.delete_by_id(label_schema_2.id_))
        yield label_schema_2

    @pytest.fixture
    def fxt_label_schema_3_persisted(self, request, fxt_mongo_id, fxt_labels, fxt_label_schema_repo):
        label_tree_56 = make_tree_from_labels(fxt_labels[4:6])
        label_group = make_group_from_labels(fxt_labels[4:6])
        label_schema_3 = LabelSchema(
            id_=LabelSchemaRepo.generate_id(),
            label_tree=label_tree_56,
            label_groups=[label_group],
            project_id=fxt_mongo_id(2),
        )
        fxt_label_schema_repo.save(label_schema_3)
        request.addfinalizer(lambda: fxt_label_schema_repo.delete_by_id(label_schema_3.id_))
        yield label_schema_3

    @pytest.fixture
    def fxt_label_schema_view_persisted(
        self,
        request,
        fxt_mongo_id,
        fxt_labels,
        fxt_label_schema_repo,
        fxt_label_schema_1_persisted,
    ):
        label_schema_view = LabelSchemaView.from_parent(
            parent_schema=fxt_label_schema_1_persisted,
            labels=[fxt_labels[0]],
            task_node_id=fxt_mongo_id(5),
            id_=LabelSchemaRepo.generate_id(),
        )
        fxt_label_schema_repo.save(label_schema_view)
        request.addfinalizer(lambda: fxt_label_schema_repo.delete_by_id(label_schema_view.id_))
        yield label_schema_view
