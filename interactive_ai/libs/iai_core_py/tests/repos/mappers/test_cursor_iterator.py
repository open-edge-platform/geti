# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import pytest

from iai_core.entities.image import Image
from iai_core.entities.media import MediaPreprocessing, MediaPreprocessingStatus
from iai_core.repos import ImageRepo


class TestCursorIterator:
    def test_is_cursor_alive_check(self, request, fxt_image_entity, fxt_dataset_storage_persisted) -> None:
        """
        A cursor iterator will be exhausted once it has been iterated over. This test
        verifies that if it is attempted to iterate a second time on the cursor, an
        error is raised.
        """
        dataset_storage = fxt_dataset_storage_persisted
        image = Image(
            name="Test image",
            uploader_id="",
            id=ImageRepo.generate_id(),
            width=50,
            height=100,
            size=100,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )
        image_repo = ImageRepo(dataset_storage.identifier)
        image_repo.save(image)
        cursor_iterator = image_repo.get_all()
        images = list(cursor_iterator)
        assert len(images) > 0
        with pytest.raises(RuntimeError):
            list(cursor_iterator)

    def test_empty_cursor(self, fxt_dataset_storage) -> None:
        """
        Tests that an empty cursor returns a list on first iteration and raises an
        error on the second iteration.
        """
        cursor_iterator = ImageRepo(fxt_dataset_storage.identifier).get_all()
        assert list(cursor_iterator) == []
        with pytest.raises(RuntimeError):
            list(cursor_iterator)
