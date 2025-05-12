# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import call, patch

import pytest

from iai_core.adapters.adapter import ReferenceAdapter
from iai_core.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from iai_core.entities.dataset_item import DatasetItem
from iai_core.entities.dataset_storage import DatasetStorage
from iai_core.entities.datasets import Dataset, DatasetIdentifier
from iai_core.entities.scored_label import ScoredLabel
from iai_core.entities.shapes import Rectangle
from iai_core.entities.subset import Subset
from iai_core.entities.video import VideoFrame
from iai_core.repos import AnnotationSceneRepo, DatasetRepo, ImageRepo, MetadataRepo
from iai_core.repos.base import SessionBasedRepo
from iai_core.repos.dataset_repo import _DatasetItemRepo

from geti_types import ProjectIdentifier


class TestDatasetItemRepo:
    def test_indexes(self, fxt_dataset_identifier) -> None:
        dataset_item_repo = _DatasetItemRepo(fxt_dataset_identifier)

        indexes_names = set(dataset_item_repo._collection.index_information().keys())

        assert indexes_names == {
            "_id_",
            "organization_id_-1_workspace_id_-1_project_id_-1_dataset_storage_id_-1_dataset_id_-1__id_1",
            "media_identifier_-1",
            "annotation_scene_id_-1",
        }

    def test_annotation_scene_repo(self, fxt_dataset_identifier) -> None:
        dataset_item_repo = _DatasetItemRepo(fxt_dataset_identifier)
        ann_scene_repo_1 = dataset_item_repo.annotation_scene_repo
        ann_scene_repo_2 = dataset_item_repo.annotation_scene_repo

        assert isinstance(ann_scene_repo_1, AnnotationSceneRepo)
        assert id(ann_scene_repo_1) == id(ann_scene_repo_2)

    def test_metadata_repo(self, fxt_dataset_identifier) -> None:
        dataset_item_repo = _DatasetItemRepo(fxt_dataset_identifier)
        metadata_repo_1 = dataset_item_repo.metadata_repo
        metadata_repo_2 = dataset_item_repo.metadata_repo

        assert isinstance(metadata_repo_1, MetadataRepo)
        assert id(metadata_repo_1) == id(metadata_repo_2)

    def test_save_shallow(
        self,
        request,
        fxt_dataset_storage_persisted,
        fxt_dataset_identifier,
        fxt_dataset_item,
    ) -> None:
        # Arrange
        dataset_item_repo = _DatasetItemRepo(fxt_dataset_identifier)
        request.addfinalizer(lambda: dataset_item_repo.delete_all())
        dataset_item: DatasetItem = fxt_dataset_item(1)
        item_ann_scene = dataset_item.annotation_scene
        item_image = dataset_item.media

        # Act
        dataset_item_repo.save_shallow(dataset_item)

        # Assert
        # When reloading the object, mock repos used in the mapper
        with (
            patch.object(ImageRepo, "get_by_id", return_value=item_image) as mock_image_get,
            patch.object(AnnotationSceneRepo, "get_by_id", return_value=item_ann_scene),
        ):
            reloaded_dataset_item = dataset_item_repo.get_by_id(dataset_item.id_)
            mock_image_get.assert_called_once_with(str(dataset_item.media_identifier.media_id))
            assert reloaded_dataset_item == dataset_item

    def test_save_deep(
        self,
        request,
        fxt_dataset_storage_persisted,
        fxt_dataset_identifier,
        fxt_dataset_item,
        fxt_metadata_item_factory,
    ) -> None:
        # Arrange
        dataset_item_repo = _DatasetItemRepo(fxt_dataset_identifier)
        request.addfinalizer(lambda: dataset_item_repo.delete_all())
        dataset_item: DatasetItem = fxt_dataset_item(1)
        item_ann_scene = dataset_item.annotation_scene
        item_image = dataset_item.media
        metadata_item = fxt_metadata_item_factory(
            dataset_storage=fxt_dataset_storage_persisted,
            media_identifier=item_image.media_identifier,
            metadata_type="float_metadata",
            dataset_item_id=dataset_item.id_,
            save=False,
        )
        dataset_item.metadata_adapters.append(ReferenceAdapter(metadata_item))

        # Act
        with (
            patch.object(AnnotationSceneRepo, "save") as mock_ann_scene_save,
            patch.object(MetadataRepo, "save") as mock_metadata_save,
        ):
            dataset_item_repo.save_deep(dataset_item)

        # Assert
        mock_ann_scene_save.assert_called_once_with(dataset_item.annotation_scene, mongodb_session=None)
        mock_metadata_save.assert_called_once_with(metadata_item, mongodb_session=None)
        # When reloading the object, mock repos used in the mapper
        with (
            patch.object(ImageRepo, "get_by_id", return_value=item_image) as mock_image_get,
            patch.object(AnnotationSceneRepo, "get_by_id", return_value=item_ann_scene),
        ):
            reloaded_dataset_item = dataset_item_repo.get_by_id(dataset_item.id_)
            mock_image_get.assert_called_once_with(str(dataset_item.media_identifier.media_id))
            assert reloaded_dataset_item == dataset_item

    def test_save_many_shallow(
        self,
        request,
        fxt_dataset_storage_persisted,
        fxt_dataset_identifier,
        fxt_dataset_item,
    ) -> None:
        dataset_item_repo = _DatasetItemRepo(fxt_dataset_identifier)
        dataset_item: DatasetItem = fxt_dataset_item(1)

        with patch.object(SessionBasedRepo, "save_many") as mock_save_many:
            dataset_item_repo.save_many_shallow([dataset_item])

        mock_save_many.assert_called_once_with([dataset_item], mongodb_session=None)

    def test_save_many_deep(
        self,
        request,
        fxt_dataset_storage_persisted,
        fxt_dataset_identifier,
        fxt_dataset_item,
    ) -> None:
        dataset_item_repo = _DatasetItemRepo(fxt_dataset_identifier)
        dataset_item: DatasetItem = fxt_dataset_item(1)

        with (
            patch.object(SessionBasedRepo, "save_many") as mock_save_many,
            patch.object(AnnotationSceneRepo, "save") as mock_ann_scene_save,
        ):
            dataset_item_repo.save_many_deep([dataset_item])

        mock_ann_scene_save.assert_called_once_with(dataset_item.annotation_scene, mongodb_session=None)
        mock_save_many.assert_called_once_with([dataset_item], mongodb_session=None)

    def test_get_all_docs(
        self,
        request,
        fxt_dataset_storage_persisted,
        fxt_dataset_identifier,
        fxt_dataset_item,
    ) -> None:
        # Arrange
        dataset_item_repo = _DatasetItemRepo(fxt_dataset_identifier)
        request.addfinalizer(lambda: dataset_item_repo.delete_all())

        assert not dataset_item_repo.get_all_docs(), "Database contains leftover items from other tests"
        dataset_item_1: DatasetItem = fxt_dataset_item(1)
        dataset_item_2: DatasetItem = fxt_dataset_item(2)
        dataset_item_repo.save_many_shallow([dataset_item_1, dataset_item_2])

        # Act
        fetched_docs = dataset_item_repo.get_all_docs()

        # Assert
        assert all(isinstance(doc, dict) for doc in fetched_docs)
        fetched_docs_ids = [str(doc["_id"]) for doc in fetched_docs]
        expected_ids = [str(dataset_item_1.id_), str(dataset_item_2.id_)]
        assert fetched_docs_ids == expected_ids

    def test_sample(
        self,
        request,
        fxt_dataset_storage_persisted,
        fxt_dataset_identifier,
        fxt_dataset_item,
    ) -> None:
        # Arrange
        dataset_item_repo = _DatasetItemRepo(fxt_dataset_identifier)
        request.addfinalizer(lambda: dataset_item_repo.delete_all())
        training_dataset_item_ids = set()
        for i in range(10):
            dataset_item = fxt_dataset_item(i)
            dataset_item.subset = Subset.TRAINING
            training_dataset_item_ids.add(dataset_item.id_)
            dataset_item_repo.save_shallow(dataset_item)

        testing_dataset_item = fxt_dataset_item(1000)
        testing_dataset_item.subset = Subset.TESTING
        dataset_item_repo.save_shallow(testing_dataset_item)

        dataset_item_ids = training_dataset_item_ids.union({testing_dataset_item.id_})

        # Act & Assert
        assert {item.id_ for item in dataset_item_repo.sample(-1)} == set()
        assert {item.id_ for item in dataset_item_repo.sample(0)} == set()
        assert {item.id_ for item in dataset_item_repo.sample(1)}.issubset(dataset_item_ids)
        assert {item.id_ for item in dataset_item_repo.sample(5)}.issubset(dataset_item_ids)
        assert {item.id_ for item in dataset_item_repo.sample(11)} == dataset_item_ids
        assert {item.id_ for item in dataset_item_repo.sample(100)} == dataset_item_ids

        # with subset filter
        all_training_items_id = {item.id_ for item in dataset_item_repo.sample(10, subset=Subset.TRAINING)}
        assert all_training_items_id == training_dataset_item_ids
        assert dataset_item_repo.sample(1, subset=Subset.TESTING)[0].id_ == testing_dataset_item.id_
        assert dataset_item_repo.sample(10, subset=Subset.VALIDATION) == ()

    def test_get_by_ids(
        self,
        request,
        fxt_dataset_storage_persisted,
        fxt_dataset_identifier,
        fxt_dataset_item,
    ) -> None:
        # Arrange
        dataset_item_repo = _DatasetItemRepo(fxt_dataset_identifier)
        request.addfinalizer(lambda: dataset_item_repo.delete_all())
        dataset_item_1: DatasetItem = fxt_dataset_item(1)
        dataset_item_2: DatasetItem = fxt_dataset_item(2)
        dataset_item_3: DatasetItem = fxt_dataset_item(3)
        dataset_item_repo.save_many_shallow([dataset_item_1, dataset_item_2, dataset_item_3])
        ids_to_fetch = [dataset_item_1.id_, dataset_item_3.id_]

        # Act
        loaded_items = list(dataset_item_repo.get_by_ids(dataset_item_ids=ids_to_fetch))
        with pytest.raises(ValueError):
            dataset_item_repo.get_by_ids(dataset_item_ids=[])

        # Assert
        assert len(loaded_items) == 2
        assert all(isinstance(item, DatasetItem) for item in loaded_items)
        fetched_ids = [item.id_ for item in loaded_items]
        assert fetched_ids == ids_to_fetch

    def test_get_by_media_identifiers(
        self,
        request,
        fxt_dataset_storage_persisted,
        fxt_dataset_identifier,
        fxt_dataset_item,
    ) -> None:
        # Arrange
        dataset_item_repo = _DatasetItemRepo(fxt_dataset_identifier)
        request.addfinalizer(lambda: dataset_item_repo.delete_all())
        # two items with media identifier #1, one item with media identifier #2
        dataset_item_1_1: DatasetItem = fxt_dataset_item(1)
        dataset_item_1_2: DatasetItem = fxt_dataset_item(1)
        dataset_item_2: DatasetItem = fxt_dataset_item(2)
        dataset_item_repo.save_many_shallow([dataset_item_1_1, dataset_item_1_2, dataset_item_2])
        assert dataset_item_1_1.media_identifier == dataset_item_1_2.media_identifier
        assert dataset_item_1_1.media_identifier != dataset_item_2.media_identifier
        media_identifier_to_fetch = dataset_item_1_1.media_identifier
        ids_to_fetch = [dataset_item_1_1.id_, dataset_item_1_2.id_]

        # Act
        loaded_items = list(dataset_item_repo.get_by_media_identifiers(media_identifiers=[media_identifier_to_fetch]))
        with pytest.raises(ValueError):
            dataset_item_repo.get_by_media_identifiers(media_identifiers=[])

        # Assert
        assert len(loaded_items) == 2
        assert all(isinstance(item, DatasetItem) for item in loaded_items)
        fetched_ids = [item.id_ for item in loaded_items]
        assert fetched_ids == ids_to_fetch

    def test_get_latest_annotation_scene_id(
        self,
        request,
        fxt_dataset_storage_persisted,
        fxt_dataset_identifier,
        fxt_dataset_item,
        fxt_annotation_scene_factory,
    ) -> None:
        # Arrange
        dataset_item_repo = _DatasetItemRepo(fxt_dataset_identifier)
        request.addfinalizer(lambda: dataset_item_repo.delete_all())
        # two items with media identifier #1, one item with media identifier #2
        dataset_item_1_1: DatasetItem = fxt_dataset_item(1)
        dataset_item_1_2: DatasetItem = fxt_dataset_item(1)
        dataset_item_2: DatasetItem = fxt_dataset_item(2)
        # create distinct annotation scenes
        dataset_item_1_1.annotation_scene = fxt_annotation_scene_factory(1)
        dataset_item_1_2.annotation_scene = fxt_annotation_scene_factory(2)
        dataset_item_2.annotation_scene = fxt_annotation_scene_factory(3)
        dataset_item_repo.save_many_shallow([dataset_item_1_1, dataset_item_1_2, dataset_item_2])
        assert dataset_item_1_1.media_identifier == dataset_item_1_2.media_identifier
        assert dataset_item_1_1.media_identifier != dataset_item_2.media_identifier

        # Act
        latest_scene_id = dataset_item_repo.get_latest_annotation_scene_id(
            media_identifier=dataset_item_1_1.media_identifier,
        )

        # Assert
        # The expected id is the one of the 2nd dataset item because the 1st has an
        # older id, while the 3rd item has a non-matching media identifier
        assert latest_scene_id == dataset_item_1_2.annotation_scene.id_

    def test_count_per_media_type(
        self,
        request,
        fxt_dataset_storage_persisted,
        fxt_dataset_identifier,
        fxt_dataset_item,
        fxt_video_entity,
        fxt_annotation_scene,
    ) -> None:
        # Arrange
        num_images, num_videos, num_frames = 2, 1, 3
        dataset_item_repo = _DatasetItemRepo(fxt_dataset_identifier)
        request.addfinalizer(lambda: dataset_item_repo.delete_all())
        dataset_items_image = [fxt_dataset_item(i) for i in range(num_images)]
        dataset_items_video = [
            DatasetItem(
                id_=DatasetRepo.generate_id(),
                media=VideoFrame(video=fxt_video_entity, frame_index=i),
                annotation_scene=fxt_annotation_scene,
            )
            for i in range(num_frames)
        ]
        dataset_item_repo.save_many_shallow(dataset_items_image + dataset_items_video)

        # Act
        counts = dataset_item_repo.count_per_media_type()

        # Assert
        assert counts == {
            "n_images": num_images,
            "n_videos": num_videos,
            "n_frames": num_frames,
            "n_samples": num_images + num_frames,
        }

    def test_count_per_subset(
        self,
        request,
        fxt_dataset_storage_persisted,
        fxt_dataset_identifier,
        fxt_dataset_item,
    ) -> None:
        # Arrange
        num_training, num_validation, num_testing = 3, 1, 2
        dataset_item_repo = _DatasetItemRepo(fxt_dataset_identifier)
        request.addfinalizer(lambda: dataset_item_repo.delete_all())
        dataset_items_training = [fxt_dataset_item(i, subset=Subset.TRAINING) for i in range(num_training)]
        dataset_items_validation = [fxt_dataset_item(i, subset=Subset.VALIDATION) for i in range(num_validation)]
        dataset_items_testing = [fxt_dataset_item(i, subset=Subset.TESTING) for i in range(num_testing)]
        dataset_item_repo.save_many_shallow(dataset_items_training + dataset_items_validation + dataset_items_testing)

        # Act
        counts = dataset_item_repo.count_per_subset()

        # Assert
        assert counts == {
            "TRAINING": num_training,
            "VALIDATION": num_validation,
            "TESTING": num_testing,
        }

    def test_delete_all_by_media_identifiers(
        self,
        request,
        fxt_dataset_storage_persisted,
        fxt_dataset_identifier,
        fxt_dataset_item,
    ) -> None:
        # Arrange
        dataset_item_repo = _DatasetItemRepo(fxt_dataset_identifier)
        request.addfinalizer(lambda: dataset_item_repo.delete_all())
        # two items with media identifier #1, one item with media identifier #2
        dataset_item_1_1: DatasetItem = fxt_dataset_item(1)
        dataset_item_1_2: DatasetItem = fxt_dataset_item(1)
        dataset_item_2: DatasetItem = fxt_dataset_item(2)
        dataset_item_repo.save_many_shallow([dataset_item_1_1, dataset_item_1_2, dataset_item_2])
        assert dataset_item_1_1.media_identifier == dataset_item_1_2.media_identifier
        assert dataset_item_1_1.media_identifier != dataset_item_2.media_identifier
        media_identifier_to_delete = dataset_item_1_1.media_identifier
        ids_after_delete = [dataset_item_2.id_]

        # Act
        deleted_items = dataset_item_repo.delete_all_by_media_identifiers(
            media_identifiers=[media_identifier_to_delete]
        )
        with pytest.raises(ValueError):
            dataset_item_repo.delete_all_by_media_identifiers(media_identifiers=[])

        # Assert
        assert len(deleted_items) == 2
        assert set(deleted_items) == {dataset_item_1_1.id_, dataset_item_1_2.id_}
        loaded_items = list(dataset_item_repo.get_all())
        assert len(loaded_items) == 1
        loaded_ids = [item.id_ for item in loaded_items]
        assert loaded_ids == ids_after_delete

    def test_delete_all_by_media_id(
        self,
        request,
        fxt_dataset_storage_persisted,
        fxt_dataset_identifier,
        fxt_dataset_item,
    ) -> None:
        # Arrange
        dataset_item_repo = _DatasetItemRepo(fxt_dataset_identifier)
        request.addfinalizer(lambda: dataset_item_repo.delete_all())
        # two items with media identifier #1, one item with media identifier #2
        dataset_item_1_1: DatasetItem = fxt_dataset_item(1)
        dataset_item_1_2: DatasetItem = fxt_dataset_item(1)
        dataset_item_2: DatasetItem = fxt_dataset_item(2)
        dataset_item_repo.save_many_shallow([dataset_item_1_1, dataset_item_1_2, dataset_item_2])
        assert dataset_item_1_1.media_identifier == dataset_item_1_2.media_identifier
        assert dataset_item_1_1.media_identifier != dataset_item_2.media_identifier
        media_id_to_delete = dataset_item_1_1.media_identifier.media_id
        ids_after_delete = [dataset_item_2.id_]

        # Act
        deleted_items = dataset_item_repo.delete_all_by_media_id(media_id=media_id_to_delete)

        # Assert
        assert len(deleted_items) == 2
        assert set(deleted_items) == {dataset_item_1_1.id_, dataset_item_1_2.id_}
        loaded_items = list(dataset_item_repo.get_all())
        assert len(loaded_items) == 1
        loaded_ids = [item.id_ for item in loaded_items]
        assert loaded_ids == ids_after_delete

    def test_assign_items_to_subset(
        self,
        request,
        fxt_dataset_storage_persisted,
        fxt_dataset_identifier,
        fxt_dataset_item,
    ) -> None:
        # Arrange
        dataset_item_repo = _DatasetItemRepo(fxt_dataset_identifier)
        request.addfinalizer(lambda: dataset_item_repo.delete_all())
        dataset_item: DatasetItem = fxt_dataset_item(1, subset=Subset.TRAINING)
        dataset_item_repo.save_shallow(dataset_item)

        # Act
        dataset_item_repo.assign_items_to_subset(dataset_items_ids=[dataset_item.id_], subset=Subset.VALIDATION)
        with pytest.raises(ValueError):
            dataset_item_repo.assign_items_to_subset(dataset_items_ids=[], subset=Subset.TRAINING)

        # Assert
        reloaded_item = dataset_item_repo.get_by_id(dataset_item.id_)
        assert reloaded_item.subset == Subset.VALIDATION

    def test_save_ignored_label_ids(
        self,
        fxt_dataset_storage_persisted,
        fxt_filled_ignore_label_dataset,
        fxt_classification_labels_persisted,
    ) -> None:
        # Arrange
        dataset = fxt_filled_ignore_label_dataset
        dataset_identifier = DatasetIdentifier.from_ds_identifier(
            dataset_storage_identifier=fxt_dataset_storage_persisted.identifier,
            dataset_id=dataset.id_,
        )
        project_identifier = ProjectIdentifier(
            workspace_id=fxt_dataset_storage_persisted.workspace_id,
            project_id=fxt_dataset_storage_persisted.project_id,
        )
        dataset_item_repo = _DatasetItemRepo(dataset_identifier)
        labels = fxt_classification_labels_persisted(project_identifier)
        label_id = labels[0].id_

        # Act
        dataset_item_repo.save_ignored_label_ids_for_dataset_item(dataset_item_id=dataset[0].id_, label_ids=[label_id])

        with pytest.raises(ValueError):
            dataset_item_repo.save_ignored_label_ids_for_dataset_item(dataset_item_id=dataset[0].id_, label_ids=[])

        # Assert
        loaded_dataset_item = dataset_item_repo.get_by_id(dataset[0].id_)
        assert loaded_dataset_item.ignored_label_ids == {label_id}


class TestDatasetRepo:
    def test_indexes(self, fxt_dataset_storage_identifier) -> None:
        # Arrange
        dataset_repo = DatasetRepo(fxt_dataset_storage_identifier)

        # Act
        indexes_names = set(dataset_repo._collection.index_information().keys())

        # Assert
        assert indexes_names == {
            "_id_",
            "organization_id_-1_workspace_id_-1_project_id_-1_dataset_storage_id_-1__id_1",
        }

    def test_get_dataset_item_repo(self, fxt_dataset_storage_identifier, fxt_ote_id) -> None:
        # Arrange
        dataset_id = fxt_ote_id(1)
        dataset_repo = DatasetRepo(fxt_dataset_storage_identifier)

        # Act
        dataset_item_repo = dataset_repo.get_dataset_item_repo(dataset_id)

        # Assert
        assert isinstance(dataset_item_repo, _DatasetItemRepo)

    def test_save_shallow(self, fxt_dataset_storage_identifier, fxt_dataset) -> None:
        # Arrange
        dataset_repo = DatasetRepo(fxt_dataset_storage_identifier)
        assert len(fxt_dataset) == 3

        with (
            patch.object(_DatasetItemRepo, "save_many_shallow") as mock_save_many_items,
            patch.object(SessionBasedRepo, "save") as mock_save,
        ):
            # Act
            dataset_repo.save_shallow(fxt_dataset)

            # Assert
            mock_save_many_items.assert_called_once_with(
                instances=tuple(fxt_dataset),
                mongodb_session=None,
            )
            mock_save.assert_called_once_with(fxt_dataset, mongodb_session=None)

    def test_save_deep(self, fxt_dataset_storage_identifier, fxt_dataset) -> None:
        # Arrange
        dataset_repo = DatasetRepo(fxt_dataset_storage_identifier)
        assert len(fxt_dataset) == 3

        with (
            patch.object(_DatasetItemRepo, "save_many_deep") as mock_save_many_items,
            patch.object(SessionBasedRepo, "save") as mock_save,
        ):
            # Act
            dataset_repo.save_deep(fxt_dataset)

            # Assert
            mock_save_many_items.assert_called_once_with(
                instances=tuple(fxt_dataset),
                mongodb_session=None,
            )
            mock_save.assert_called_once_with(fxt_dataset, mongodb_session=None)

    def test_save_immutable(self, fxt_dataset_storage_identifier) -> None:
        """Test that immutable datasets cannot be saved twice"""
        dataset_repo = DatasetRepo(fxt_dataset_storage_identifier)
        dataset = Dataset(id=DatasetRepo.generate_id(), mutable=False)
        assert dataset.ephemeral
        dataset_repo.save_shallow(dataset)
        assert not dataset.ephemeral
        with pytest.raises(ValueError):
            dataset_repo.save_shallow(dataset)

    def test_add_items_to_dataset(self, request, fxt_dataset_storage_identifier, fxt_dataset_item) -> None:
        # Arrange
        dataset_repo = DatasetRepo(fxt_dataset_storage_identifier)
        request.addfinalizer(lambda: dataset_repo.delete_all())
        dataset_items = [fxt_dataset_item(i) for i in range(4)]
        dataset = Dataset(id=dataset_repo.generate_id(), items=dataset_items[:2])  # initialize with 2 items
        dataset_repo.save_shallow(dataset)
        assert len(dataset_repo.get_by_id(dataset.id_)) == 2

        # Act
        dataset_repo.add_items_to_dataset(  # add the other 2 items
            dataset_id=dataset.id_, dataset_items=dataset_items[-2:]
        )
        with pytest.raises(ValueError):
            dataset_repo.add_items_to_dataset(dataset_id=dataset.id_, dataset_items=[])

        # Assert
        assert len(dataset_repo.get_by_id(dataset.id_)) == 4

    def test_get_items_from_dataset(self, request, fxt_dataset_storage_identifier, fxt_dataset_item) -> None:
        # Arrange
        dataset_repo = DatasetRepo(fxt_dataset_storage_identifier)
        request.addfinalizer(lambda: dataset_repo.delete_all())
        dataset_items = [fxt_dataset_item(i) for i in range(3)]
        dataset = Dataset(id=dataset_repo.generate_id(), items=dataset_items)
        dataset_repo.save_shallow(dataset)
        ids_to_get = [dataset_items[0].id_, dataset_items[1].id_]

        # Act
        loaded_items = list(dataset_repo.get_items_from_dataset(dataset_id=dataset.id_, dataset_item_ids=ids_to_get))

        # Assert
        assert len(loaded_items) == 2
        assert {item.id_ for item in loaded_items} == set(ids_to_get)

    def test_get_items_by_dataset_and_media_identifiers(self, fxt_dataset_storage_identifier, fxt_dataset_item) -> None:
        # Arrange
        dataset_repo = DatasetRepo(fxt_dataset_storage_identifier)
        dataset_items = [fxt_dataset_item(i) for i in range(2)]
        dataset = Dataset(id=dataset_repo.generate_id(), items=dataset_items)
        media_identifier_to_fetch = dataset_items[0].media_identifier
        with patch.object(_DatasetItemRepo, "get_by_media_identifiers", return_value=dataset_items) as mock_get_items:
            # Act
            loaded_items = dataset_repo.get_items_by_dataset_and_media_identifiers(
                dataset_id=dataset.id_, media_identifiers=[media_identifier_to_fetch]
            )

        # Assert
        mock_get_items.assert_called_once_with(media_identifiers=[media_identifier_to_fetch])
        assert loaded_items == dataset_items

    def test_get_latest_annotation_scene_id(
        self, fxt_dataset_storage_identifier, fxt_image_identifier, fxt_ote_id
    ) -> None:
        # Arrange
        dataset_repo = DatasetRepo(fxt_dataset_storage_identifier)
        dataset_id = fxt_ote_id(1)
        latest_ann_scene_id = fxt_ote_id(2)
        with patch.object(
            _DatasetItemRepo,
            "get_latest_annotation_scene_id",
            return_value=latest_ann_scene_id,
        ) as mock_get_ann_scene:
            # Act
            result_id = dataset_repo.get_latest_annotation_scene_id(
                dataset_id=dataset_id, media_identifier=fxt_image_identifier
            )

        # Assert
        mock_get_ann_scene.assert_called_once_with(media_identifier=fxt_image_identifier)
        assert result_id == latest_ann_scene_id

    def test_count_items(self, fxt_dataset_storage_identifier, fxt_ote_id) -> None:
        # Arrange
        dataset_repo = DatasetRepo(fxt_dataset_storage_identifier)
        dataset_id = fxt_ote_id(1)
        mocked_count_output = 12
        with patch.object(_DatasetItemRepo, "count", return_value=mocked_count_output) as mock_count:
            # Act
            num_items = dataset_repo.count_items(dataset_id=dataset_id)

        # Assert
        mock_count.assert_called_once_with()
        assert num_items == mocked_count_output

    def test_count_per_media_type(self, fxt_dataset_storage_identifier, fxt_ote_id) -> None:
        # Arrange
        dataset_repo = DatasetRepo(fxt_dataset_storage_identifier)
        dataset_id = fxt_ote_id(1)
        mocked_count_output = {"foo": 1}
        with patch.object(_DatasetItemRepo, "count_per_media_type", return_value=mocked_count_output) as mock_count:
            # Act
            counts = dataset_repo.count_per_media_type(dataset_id=dataset_id)

        # Assert
        mock_count.assert_called_once_with()
        assert counts == mocked_count_output

    def test_count_per_subset(self, fxt_dataset_storage_identifier, fxt_ote_id) -> None:
        # Arrange
        dataset_repo = DatasetRepo(fxt_dataset_storage_identifier)
        dataset_id = fxt_ote_id(1)
        mocked_count_output = {"foo": 1}
        with patch.object(_DatasetItemRepo, "count_per_subset", return_value=mocked_count_output) as mock_count:
            # Act
            counts = dataset_repo.count_per_subset(dataset_id=dataset_id)

        # Assert
        mock_count.assert_called_once_with()
        assert counts == mocked_count_output

    def test_delete_items_by_dataset_and_media_identifiers(
        self, fxt_dataset_storage_identifier, fxt_image_identifier, fxt_ote_id
    ) -> None:
        # Arrange
        dataset_repo = DatasetRepo(fxt_dataset_storage_identifier)
        dataset_id = fxt_ote_id(1)
        mocked_delete_output = (fxt_ote_id(2), fxt_ote_id(3))
        with patch.object(
            _DatasetItemRepo,
            "delete_all_by_media_identifiers",
            return_value=mocked_delete_output,
        ) as mock_delete_items:
            # Act
            delete_output = dataset_repo.delete_items_by_dataset_and_media_identifiers(
                dataset_id=dataset_id,
                media_identifiers=[fxt_image_identifier],
            )
            with pytest.raises(ValueError):
                dataset_repo.delete_items_by_dataset_and_media_identifiers(dataset_id=dataset_id, media_identifiers=[])

        # Assert
        mock_delete_items.assert_called_once_with(media_identifiers=[fxt_image_identifier])
        assert delete_output == mocked_delete_output

    def test_delete_items_by_dataset_and_media(
        self, fxt_dataset_storage_identifier, fxt_image_identifier, fxt_ote_id
    ) -> None:
        # Arrange
        dataset_repo = DatasetRepo(fxt_dataset_storage_identifier)
        dataset_id = fxt_ote_id(1)
        mocked_delete_output = (fxt_ote_id(2), fxt_ote_id(3))
        with patch.object(
            _DatasetItemRepo,
            "delete_all_by_media_id",
            return_value=mocked_delete_output,
        ) as mock_delete_items:
            # Act
            delete_output = dataset_repo.delete_items_by_dataset_and_media(
                dataset_id=dataset_id,
                media_id=fxt_image_identifier.media_id,
            )

        # Assert
        mock_delete_items.assert_called_once_with(media_id=fxt_image_identifier.media_id)
        assert delete_output == mocked_delete_output

    def test_delete_items_by_dataset(self, fxt_dataset_storage_identifier, fxt_ote_id) -> None:
        # Arrange
        dataset_repo = DatasetRepo(fxt_dataset_storage_identifier)
        dataset_id = fxt_ote_id(1)
        with patch.object(_DatasetItemRepo, "delete_all") as mock_delete_items:
            # Act
            dataset_repo.delete_items_by_dataset(dataset_id=dataset_id)

        # Assert
        mock_delete_items.assert_called_once_with()

    def test_delete_by_id(self, fxt_dataset_storage_identifier, fxt_image_identifier, fxt_ote_id) -> None:
        # Arrange
        dataset_repo = DatasetRepo(fxt_dataset_storage_identifier)
        dataset_id = fxt_ote_id(1)
        with (
            patch.object(DatasetRepo, "delete_items_by_dataset") as mock_delete_items,
            patch.object(SessionBasedRepo, "delete_by_id") as mock_delete_dataset,
        ):
            # Act
            dataset_repo.delete_by_id(dataset_id)

        # Assert
        mock_delete_items.assert_called_once_with(dataset_id=dataset_id)
        mock_delete_dataset.assert_called_once_with(dataset_id)

    def test_save_subsets_in_dataset(self, fxt_dataset_storage_identifier, fxt_dataset_item) -> None:
        # Arrange
        dataset_repo = DatasetRepo(fxt_dataset_storage_identifier)
        dataset_item_1 = fxt_dataset_item(1, subset=Subset.TRAINING)
        dataset_item_2 = fxt_dataset_item(2, subset=Subset.TRAINING)
        dataset_item_3 = fxt_dataset_item(3, subset=Subset.VALIDATION)
        dataset = Dataset(
            id=DatasetRepo.generate_id(),
            items=[dataset_item_1, dataset_item_2, dataset_item_3],
        )
        with patch.object(_DatasetItemRepo, "assign_items_to_subset") as mock_assign_items_to_subsets:
            # Act
            dataset_repo.save_subsets_in_dataset(dataset)

        # Assert
        mock_assign_items_to_subsets.assert_has_calls(
            [
                call(
                    dataset_items_ids=[dataset_item_1.id_, dataset_item_2.id_],
                    subset=Subset.TRAINING,
                ),
                call(dataset_items_ids=[dataset_item_3.id_], subset=Subset.VALIDATION),
            ]
        )


@pytest.fixture
def fxt_filled_ignore_label_dataset(
    request,
    fxt_mongo_id,
    fxt_dataset_storage_persisted,
    fxt_classification_labels_persisted,
    fxt_detection_labels_persisted,
    fxt_image_entity,
):
    """
    Create a persisted dataset with 2 dataset items where:
      - the first item has an annotation with a not-ignored classification label
      - the second item has an annotation with two annotations:
        - one not-ignored classification label
        - one ignored detection label
    """
    dataset_storage: DatasetStorage = fxt_dataset_storage_persisted
    project_identifier = ProjectIdentifier(
        workspace_id=dataset_storage.workspace_id,
        project_id=dataset_storage.project_id,
    )
    cls_labels = fxt_classification_labels_persisted(project_identifier)
    det_labels = fxt_detection_labels_persisted(project_identifier)
    dataset_repo = DatasetRepo(dataset_storage.identifier)

    annotation_scene_1 = AnnotationScene(
        kind=AnnotationSceneKind.ANNOTATION,
        media_identifier=fxt_image_entity.media_identifier,
        media_height=1,
        media_width=1,
        id_=AnnotationSceneRepo.generate_id(),
        annotations=[
            Annotation(
                shape=Rectangle.generate_full_box(),
                labels=[ScoredLabel(label_id=cls_labels[0].id_, is_empty=cls_labels[0].is_empty)],
            )
        ],
    )
    annotation_scene_2 = AnnotationScene(
        kind=AnnotationSceneKind.ANNOTATION,
        media_identifier=fxt_image_entity.media_identifier,
        media_height=1,
        media_width=1,
        id_=AnnotationSceneRepo.generate_id(),
        annotations=[
            Annotation(
                shape=Rectangle.generate_full_box(),
                labels=[ScoredLabel(label_id=det_labels[0].id_, is_empty=det_labels[0].is_empty)],
            ),
            Annotation(
                shape=Rectangle.generate_full_box(),
                labels=[ScoredLabel(label_id=cls_labels[0].id_, is_empty=cls_labels[0].is_empty)],
            ),
        ],
    )
    dataset_item_1 = DatasetItem(
        media=fxt_image_entity,
        annotation_scene=annotation_scene_1,
        ignored_label_ids=[],
        id_=DatasetRepo.generate_id(),
    )
    dataset_item_2 = DatasetItem(
        media=fxt_image_entity,
        annotation_scene=annotation_scene_2,
        ignored_label_ids=[det_labels[0].id_],
        id_=DatasetRepo.generate_id(),
    )
    dataset = Dataset(id=DatasetRepo.generate_id(), items=[dataset_item_1, dataset_item_2])
    request.addfinalizer(lambda: dataset_repo.delete_by_id(dataset.id_))
    dataset_repo.save_deep(dataset)

    yield dataset
