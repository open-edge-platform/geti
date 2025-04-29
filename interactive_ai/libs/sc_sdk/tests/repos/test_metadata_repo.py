# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch

import pytest
from pymongo.results import DeleteResult

from sc_sdk.entities.metadata import FloatMetadata, NullMetadataItem
from sc_sdk.entities.tensor import Tensor
from sc_sdk.repos import MetadataRepo
from sc_sdk.repos.storage.binary_repos import TensorBinaryRepo

from geti_types import ImageIdentifier


@pytest.mark.ScSdkComponent
class TestMetadataRepo:
    def test_indexes(self, fxt_dataset_storage) -> None:
        metadata_repo = MetadataRepo(fxt_dataset_storage.identifier)

        indexes_names = set(metadata_repo._collection.index_information().keys())

        assert indexes_names == {
            "_id_",
            "organization_id_-1_workspace_id_-1_project_id_-1_dataset_storage_id_-1__id_1",
            "dataset_storage_id_-1_project_id_-1_workspace_id_-1_organization_id_-1_content.schema_-1",
            "media_identifier_-1",
            "content.schema_-1",
            "content.prediction_id_-1",
        }

    def test_tensor_binary_repo(self, fxt_dataset_storage) -> None:
        metadata_repo = MetadataRepo(fxt_dataset_storage.identifier)
        tensor_binary_repo_1 = metadata_repo.tensor_binary_repo
        tensor_binary_repo_2 = metadata_repo.tensor_binary_repo

        assert isinstance(tensor_binary_repo_1, TensorBinaryRepo)
        assert id(tensor_binary_repo_1) == id(tensor_binary_repo_2)

    @pytest.mark.parametrize(
        "metadata_type",
        ["float_metadata", "tensor"],
        ids=["Float", "Tensor"],
    )
    def test_save(
        self,
        metadata_type,
        fxt_dataset_storage,
        fxt_metadata_item_factory,
        fxt_image_identifier,
    ) -> None:
        metadata_repo = MetadataRepo(fxt_dataset_storage.identifier)
        metadata_item = fxt_metadata_item_factory(
            metadata_type=metadata_type,
            media_identifier=fxt_image_identifier,
            dataset_storage=fxt_dataset_storage,
            save=False,
        )

        metadata_repo.save(metadata_item)

        # Check that the saved item can be retrieved
        reloaded_metadata_item = metadata_repo.get_by_id(metadata_item.id_)
        assert not isinstance(reloaded_metadata_item, NullMetadataItem)

        # Check that the reloaded metadata item has the right type
        match metadata_type:
            case "float_metadata":
                assert isinstance(reloaded_metadata_item.data, FloatMetadata)
            case "tensor":
                assert isinstance(reloaded_metadata_item.data, Tensor)

        # Check that attempting to save a metadata item twice raises an exception
        with pytest.raises(RuntimeError):
            metadata_repo.save(metadata_item)

    def test_delete_by_id(
        self,
        fxt_dataset_storage,
        fxt_metadata_item_factory,
        fxt_image_identifier,
    ) -> None:
        metadata_repo = MetadataRepo(fxt_dataset_storage.identifier)
        metadata_item = fxt_metadata_item_factory(
            media_identifier=fxt_image_identifier,
            dataset_storage=fxt_dataset_storage,
            save=True,
        )

        metadata_repo.delete_by_id(metadata_item.id_)

        reloaded_metadata_item = metadata_repo.get_by_id(metadata_item.id_)
        assert isinstance(reloaded_metadata_item, NullMetadataItem)

    def test_delete_all(
        self,
        fxt_dataset_storage,
        fxt_metadata_item_factory,
        fxt_image_identifier,
    ) -> None:
        metadata_repo = MetadataRepo(fxt_dataset_storage.identifier)
        fxt_metadata_item_factory(
            metadata_type="float_metadata",
            media_identifier=fxt_image_identifier,
            dataset_storage=fxt_dataset_storage,
            save=True,
        )

        metadata_repo.delete_all()

        reloaded_items = metadata_repo.get_all()
        assert set(reloaded_items) == set()

    def test_delete_all_by_type(
        self,
        fxt_dataset_storage,
        fxt_metadata_item_factory,
        fxt_image_identifier,
    ) -> None:
        metadata_repo = MetadataRepo(fxt_dataset_storage.identifier)
        fxt_metadata_item_factory(
            metadata_type="float_metadata",
            media_identifier=fxt_image_identifier,
            dataset_storage=fxt_dataset_storage,
            save=True,
        )
        tensor_metadata_item = fxt_metadata_item_factory(
            metadata_type="tensor",
            media_identifier=fxt_image_identifier,
            dataset_storage=fxt_dataset_storage,
            save=True,
        )

        # Delete floats
        metadata_repo.delete_all_by_type(FloatMetadata)
        reloaded_items_ids = [mi.id_ for mi in metadata_repo.get_all()]
        expected_kept_ids = {tensor_metadata_item.id_}
        assert set(reloaded_items_ids) == expected_kept_ids

        # Delete tensors
        metadata_repo.delete_all_by_type(Tensor)
        reloaded_items_ids = [mi.id_ for mi in metadata_repo.get_all()]
        assert set(reloaded_items_ids) == set()

    def test_delete_all_by_media_identifier(
        self,
        fxt_dataset_storage,
        fxt_metadata_item_factory,
        fxt_ote_id,
    ) -> None:
        metadata_repo = MetadataRepo(fxt_dataset_storage.identifier)
        image_identifier_1 = ImageIdentifier(image_id=fxt_ote_id(1))
        image_identifier_2 = ImageIdentifier(image_id=fxt_ote_id(2))
        # Create 2 metadata for the first image and 1 for the second
        for img_ident in (image_identifier_1, image_identifier_1, image_identifier_2):
            fxt_metadata_item_factory(
                metadata_type="float_metadata",
                media_identifier=img_ident,
                dataset_storage=fxt_dataset_storage,
                save=True,
            )

        metadata_repo.delete_all_by_media_identifier(image_identifier_1)

        reloaded_metadata_items = list(metadata_repo.get_all())
        assert len(reloaded_metadata_items) == 1
        assert reloaded_metadata_items[0].media_identifier == image_identifier_2

    def test_delete_all_with_filter_no_binaries(
        self,
        fxt_dataset_storage,
        fxt_metadata_item_factory,
        fxt_ote_id,
    ) -> None:
        # Arrange
        extra_filter = {"foo": "bar"}
        metadata_repo = MetadataRepo(fxt_dataset_storage.identifier)

        # Act
        with (
            patch.object(metadata_repo._collection, "delete_many") as mock_delete_many,
            patch.object(metadata_repo._collection, "find") as mock_find,
            patch.object(metadata_repo, "preliminary_query_match_filter", return_value={}),
            patch.object(metadata_repo.tensor_binary_repo, "delete_by_filename") as mock_tensor_delete_by_filename,
        ):
            mock_delete_many.return_value = DeleteResult({"n": 1}, True)
            metadata_repo.delete_all(extra_filter=extra_filter)

        # Assert
        mock_find.assert_called_once_with(extra_filter, {"content.schema": 1, "content.binary_filename": 1})
        mock_tensor_delete_by_filename.assert_not_called()
        mock_delete_many.assert_called_once_with(extra_filter)

    def test_delete_all_with_filter(
        self,
        fxt_dataset_storage,
        fxt_metadata_item_factory,
        fxt_ote_id,
    ) -> None:
        # Arrange
        extra_filter = {"foo": "bar"}
        metadata_repo = MetadataRepo(fxt_dataset_storage.identifier)

        # Act
        with (
            patch.object(metadata_repo._collection, "delete_many") as mock_delete_many,
            patch.object(metadata_repo._collection, "find") as mock_find,
            patch.object(metadata_repo, "preliminary_query_match_filter", return_value={}),
            patch.object(metadata_repo.tensor_binary_repo, "delete_by_filename") as mock_tensor_delete_by_filename,
        ):
            mock_find.return_value = [
                {"content": {"schema": "tensor", "binary_filename": "tensor_file"}},
            ]
            mock_delete_many.return_value = DeleteResult({"n": 1}, True)
            metadata_repo.delete_all(extra_filter=extra_filter)

        # Assert
        mock_find.assert_called_once_with(extra_filter, {"content.schema": 1, "content.binary_filename": 1})
        mock_tensor_delete_by_filename.assert_called_once_with(filename="tensor_file")
        mock_delete_many.assert_called_once_with(extra_filter)

    def test_delete_all_no_filter(
        self,
        fxt_dataset_storage,
        fxt_metadata_item_factory,
        fxt_ote_id,
    ) -> None:
        # Arrange
        metadata_repo = MetadataRepo(fxt_dataset_storage.identifier)

        # Act
        with (
            patch.object(metadata_repo._collection, "delete_many") as mock_delete_many,
            patch.object(metadata_repo, "preliminary_query_match_filter", return_value={}),
            patch.object(metadata_repo.tensor_binary_repo, "delete_all") as mock_tensor_delete_all,
        ):
            mock_delete_many.return_value = DeleteResult({"n": 1}, True)
            metadata_repo.delete_all()

        # Assert
        mock_tensor_delete_all.assert_called_once_with()
        mock_delete_many.assert_called_once_with({})
