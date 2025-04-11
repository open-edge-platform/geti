# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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

from sc_sdk.entities.label import Domain, Label
from sc_sdk.repos import LabelRepo


@pytest.mark.ScSdkComponent
class TestLabelRepo:
    def test_indexes(self, fxt_project_identifier) -> None:
        label_repo = LabelRepo(fxt_project_identifier)

        indexes_names = set(label_repo._collection.index_information().keys())

        assert indexes_names == {
            "_id_",
            "organization_id_-1_workspace_id_-1_project_id_-1__id_1",
        }

    def test_get_by_ids(self, request, fxt_project_identifier) -> None:
        # Arrange
        label_repo = LabelRepo(fxt_project_identifier)
        labels = [Label(name=f"label_{i}", domain=Domain.DETECTION, id_=label_repo.generate_id()) for i in range(3)]
        label_repo.save_many(labels)
        request.addfinalizer(lambda: label_repo.delete_all())
        ids_to_get = [labels[0].id_, labels[1].id_]

        # Act
        loaded_labels = label_repo.get_by_ids(label_ids=ids_to_get)

        # Assert
        assert set(loaded_labels.values()) == set(labels[:2])
        assert all(lbl.id_ == lbl_id for lbl_id, lbl in loaded_labels.items())
