# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import filecmp
import http
import os
import tempfile
from urllib.parse import urlparse

import requests
from models.user import User

from config.consts import TEST_PHOTO_FILEPATH
from config.env import s3_public_address


def test_add_photo(user, user_photo):
    # getting photo's presigned url is an indirect way of checking if there is a photo for user -
    # after addition there should be the presigned url for user's photo
    assert user.get_photo_presigned_url() is not None


def test_get_photo(user, user_photo):
    presigned_url = user.get_photo_presigned_url(x_forwarded_host_header=s3_public_address)
    assert presigned_url != ""

    returned_user = User.get_by_id(user.id, user.organization_id)
    assert returned_user.presigned_url != ""

    parsed_presigned_url = urlparse(presigned_url)
    presigned_url_path_with_removed_platform_prefix = parsed_presigned_url.path.removeprefix("/api/v1/fileservice")
    parsed_presigned_url = parsed_presigned_url._replace(
        path=presigned_url_path_with_removed_platform_prefix, scheme="http"
    )

    response = requests.get(parsed_presigned_url.geturl())
    assert response.status_code == http.HTTPStatus.OK
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as temp_file:
        temp_file.write(response.content)

    assert filecmp.cmp(TEST_PHOTO_FILEPATH, temp_file.name) is True

    os.remove(temp_file.name)


def test_delete_photo(user):
    user.add_photo(TEST_PHOTO_FILEPATH)
    user.delete_photo()
    assert user.get_photo_presigned_url() is None


def test_delete_photo_not_found(user):
    # assert deletion wasn't performed because there was no photo to delete
    assert user.delete_photo() is False
