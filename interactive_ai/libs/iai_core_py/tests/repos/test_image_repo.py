#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#
from typing import TYPE_CHECKING

import cv2

from iai_core.entities.image import Image, NullImage
from iai_core.entities.media import ImageExtensions, MediaPreprocessing, MediaPreprocessingStatus
from iai_core.repos import ImageRepo

if TYPE_CHECKING:
    from iai_core.entities.dataset_storage import DatasetStorage


class TestImageRepo:
    def test_save_image(self, fxt_dataset_storage_persisted) -> None:
        """
        <b>Description:</b>
        Check that an image is correctly saved and loaded by the ImageRepo

        <b>Input data:</b>
        1. An image of shape [100, 50, 3]

        <b>Expected results:</b>
        Test passes if the image that's saved to the ImageRepo
        and later retrieved is the same as the image that was created

        <b>Steps</b>
        1. Create test image
        2. Save test image to ImageRepo
        3. Compare created image to image retrieved from ImageRepo
        """
        dataset_storage: DatasetStorage = fxt_dataset_storage_persisted
        image = Image(
            name="Test image",
            uploader_id="",
            id=ImageRepo.generate_id(),
            width=50,
            height=100,
            size=100,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )
        repo = ImageRepo(dataset_storage.identifier)
        repo.save(image)

        image_two = repo.get_by_id(image.id_)
        image_identifiers = repo.get_all_identifiers()
        assert image.media_identifier in image_identifiers
        assert image.width == image_two.width, "The width did not match after saving and fetching"
        assert image.height == image_two.height, "The height did not match after saving and fetching"
        assert image.size == image_two.size, "The size did not match after saving and fetching"

    def test_delete_by_id(self, request, fxt_random_annotated_image_factory, fxt_dataset_storage_persisted) -> None:
        """
        <b>Description:</b>
        Tests the ImageRepo's ability to delete an image document, binary files and thumbnail binary

        <b>Input data:</b>
        A randomly generated image

        <b>Expected results:</b>
        Test passes if the delete_by_id method properly deletes all entities

        <b>Steps</b>
        1. Generate a random image and save it, and save a thumbnail for it
        2. Delete the image by ID
        3. Check that the image, the image binary and the thumbnail binary are deleted.
        """
        dataset_storage = fxt_dataset_storage_persisted
        image_repo = ImageRepo(dataset_storage.identifier)

        image_numpy, _ = fxt_random_annotated_image_factory(image_width=100, image_height=200, labels=[])
        image = Image(
            name="test",
            uploader_id="",
            id=ImageRepo.generate_id(),
            extension=ImageExtensions.JPG,
            width=100,
            height=200,
            size=100,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )
        image_repo.save(image)
        request.addfinalizer(lambda: image_repo.delete_by_id(image.id_))

        # Generate a thumbnail
        image_filename = str(image.id_)
        thumbnail_filename = Image.thumbnail_filename_by_image_id(str(image.id_))
        resized_media = cv2.resize(image_numpy, (2, 2), interpolation=cv2.INTER_AREA)
        image_repo.thumbnail_binary_repo.save(dst_file_name=thumbnail_filename, data_source=resized_media.tobytes())
        request.addfinalizer(lambda: image_repo.thumbnail_binary_repo.delete_by_filename(filename=thumbnail_filename))

        assert image_repo.thumbnail_binary_repo.exists(filename=thumbnail_filename)

        # Delete the image
        image_repo.delete_by_id(image.id_)

        # Assert all entities are deleted
        fetched_image = image_repo.get_by_id(image.id_)
        assert isinstance(fetched_image, NullImage)
        assert not image_repo.binary_repo.exists(filename=image_filename)
        assert not image_repo.thumbnail_binary_repo.exists(filename=thumbnail_filename)

    def test_get_image_info_by_ids(self, request, fxt_dataset_storage_persisted) -> None:
        """
        <b>Description:</b>
        Check that image info is correctly loaded by the ImageRepo

        <b>Input data:</b>
        1. 5 images

        <b>Expected results:</b>
        Test passes if the correct

        <b>Steps</b>
        1. Create test images and save them to the repo
        2. Obtain image info by id
        3. Compare created image to image info retrieved from ImageRepo
        """
        dataset_storage: DatasetStorage = fxt_dataset_storage_persisted
        image = Image(
            name="Test image",
            uploader_id="Author",
            id=ImageRepo.generate_id(),
            width=50,
            height=100,
            size=100,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )
        repo = ImageRepo(dataset_storage.identifier)
        request.addfinalizer(lambda: repo.delete_all())
        image_ids = []
        for i in range(5):
            id_ = repo.generate_id()
            image.id_ = id_
            image_ids.append(id_)
            repo.save(image)

        image_id_to_image = repo.get_image_by_ids(ids=image_ids[0:5:2])

        assert len(image_id_to_image.keys()) == 3
        assert list(image_id_to_image.keys()) == image_ids[0:5:2]
