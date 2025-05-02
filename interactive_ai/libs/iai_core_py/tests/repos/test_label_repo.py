# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from iai_core.entities.label import Domain, Label
from iai_core.repos import LabelRepo


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
