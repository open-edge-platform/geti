# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from config.consts import TEST_PHOTO_FILEPATH


def test_add_photo(organization, organization_photo):
    # getting photo's presigned url is an indirect way of checking if there is a photo for organization -
    # after addition there should be the presigned url for org's photo
    assert organization.get_photo_presigned_url() is not None


def test_get_photo(organization, organization_photo):
    presigned_url = organization.get_photo_presigned_url()  # noqa: F841

    # TODO: fix after: CVS-116400
    # response = requests.get(presigned_url)
    # assert response.status_code == http.HTTPStatus.OK
    # with tempfile.NamedTemporaryFile(mode='wb', delete=False) as temp_file:
    #     temp_file.write(response.content)
    #
    # assert filecmp.cmp(TEST_PHOTO_FILEPATH, temp_file.name) is True
    #
    # os.remove(temp_file.name)


def test_delete_photo(organization):
    organization.add_photo(TEST_PHOTO_FILEPATH)
    organization.delete_photo()
    assert organization.get_photo_presigned_url() is None


def test_delete_photo_not_found(organization):
    # assert deletion wasn't performed because there was no photo to delete
    assert organization.delete_photo() is False
