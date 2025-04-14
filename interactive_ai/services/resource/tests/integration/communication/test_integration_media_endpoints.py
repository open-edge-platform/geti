# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import tempfile
from http import HTTPStatus
from unittest.mock import patch

import numpy as np
import pytest
from PIL import Image

from managers.project_manager import ProjectManager


@pytest.fixture
def fxt_random_image_file():
    random_image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    img = Image.fromarray(random_image)
    with tempfile.TemporaryDirectory() as temp_dir:
        image_path = f"{temp_dir}/test_jpeg.jpeg"
        img.save(image_path)
        yield image_path


class TestMediaRESTEndpoint:
    @pytest.mark.parametrize("fxt_filled_image_dataset_storage", [1], indirect=True)
    def test_image_upload_filter_endpoint_images(
        self,
        fxt_organization_id,
        fxt_resource_rest,
        fxt_filled_image_dataset_storage,
        fxt_project,
        fxt_random_image_file,
    ):
        """
        Tests the image upload endpoint
        """
        with open(fxt_random_image_file, "rb") as image_file:
            file = [
                (
                    "file",
                    (
                        "test_jpeg.jpeg",
                        image_file,
                        "image/jpeg",
                    ),
                ),
            ]
        with (
            patch.object(
                ProjectManager,
                "get_project_by_id",
                return_value=fxt_project,
            ),
            patch.object(
                ProjectManager,
                "get_dataset_storage_by_id",
                return_value=fxt_filled_image_dataset_storage,
            ),
        ):
            url = (
                f"/api/v1/organizations/{str(fxt_organization_id)}/workspaces/{str(fxt_filled_image_dataset_storage.workspace_id)}"
                f"/projects/{fxt_project.id_}/datasets/{fxt_filled_image_dataset_storage.id_}/media/images"
            )

            result = fxt_resource_rest.post(url, files=file, data={"upload_info": '"foo"'})
            assert result.status_code == HTTPStatus.BAD_REQUEST
            data = result.json()
            expected_error = (
                "upload_info must be a dictionary in json format. Received 'foo' of type <class 'str'> instead."
            )
            assert data["message"] == expected_error
