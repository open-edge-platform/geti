# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

from common.utils import DEFAULT_ORGANIZATION_ID, DEFAULT_WORKSPACE_NAME, get_default_workspace_id, make_tarfile


def mock_workspace(mocker, name: str, workspace_id: str):
    mocked_workspaces = {"workspaces": [{"name": name, "id": workspace_id}]}
    mocker.patch("requests.get")
    mocker.patch("json.loads", return_value=mocked_workspaces)


def test_get_workspace_id(mocker):
    workspace_id = "lorem"
    mock_workspace(mocker, name=DEFAULT_WORKSPACE_NAME, workspace_id=workspace_id)
    result = get_default_workspace_id()
    assert result == workspace_id


def test_get_wrong_workspace_id(mocker):
    workspace_id = "ipsum"
    mock_workspace(mocker, name="Example Name", workspace_id=workspace_id)
    get_default_workspace_id.cache_clear()
    with pytest.raises(ValueError) as err:
        get_default_workspace_id(organization_id=DEFAULT_ORGANIZATION_ID)
    assert str(err.value) == f"{DEFAULT_WORKSPACE_NAME} does not exist."


def test_make_tarfile(mocker):
    example_source_files = ["file1.txt", "file2.txt", "file3.txt"]
    example_output_filename = "my_logs.tar.gz"
    example_format = 2
    example_compression_level = 1
    example_mode = "w:gz"

    mock_tarfile_open = mocker.patch("common.utils.tarfile.open")

    make_tarfile(output_filename=example_output_filename, paths=example_source_files)
    mock_tarfile_open.assert_called_once_with(
        name=example_output_filename, mode=example_mode, format=example_format, compresslevel=example_compression_level
    )
