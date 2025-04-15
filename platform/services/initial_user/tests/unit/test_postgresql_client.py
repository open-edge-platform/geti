# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


def test_update_workspace_object_id(mock_postgresql_connection):
    workspace_id = "w123456"
    mock_postgresql_connection.update_workspace_object_id(workspace_id=workspace_id)
