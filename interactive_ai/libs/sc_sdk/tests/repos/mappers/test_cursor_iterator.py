# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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

from sc_sdk.entities.image import Image
from sc_sdk.entities.media import MediaPreprocessing, MediaPreprocessingStatus
from sc_sdk.repos import ImageRepo


@pytest.mark.ScSdkComponent
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
