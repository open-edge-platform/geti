# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

from unittest.mock import Mock

import pytest

from account_service_client import AccountServiceConnection

from .custom_usertype import custom_mock_usertype


@pytest.fixture
def mock_account_service_connection(mocker):
    connection = AccountServiceConnection()
    connection.client.organization_stub = Mock()
    connection.client.workspace_stub = Mock()
    connection.client.user_stub = Mock()
    yield connection


def test_create_default_organization_that_exist(mock_account_service_connection):
    mock_account_service_connection.client.organization_stub.find.total_matched_count = 1
    mock_account_service_connection.client.organization_stub.find.return_value = Mock(
        total_matched_count=1, organizations=[Mock(id="o123456")]
    )
    mock_account_service_connection.client.organization_stub.create.return_value = Mock(id="o098765")

    org_id = mock_account_service_connection.client.create_default_organization()

    assert org_id == "o123456"
    assert mock_account_service_connection.client.organization_stub.find.call_count == 1
    assert mock_account_service_connection.client.organization_stub.create.call_count == 0


def test_create_default_organization_that_does_not_exist(mock_account_service_connection):
    mock_account_service_connection.client.organization_stub.find.total_matched_count = 0
    mock_account_service_connection.client.organization_stub.find.return_value = Mock(total_matched_count=0)
    mock_account_service_connection.client.organization_stub.create.return_value = Mock(id="o098765")

    org_id = mock_account_service_connection.client.create_default_organization()

    assert org_id == "o098765"
    assert mock_account_service_connection.client.organization_stub.find.call_count == 1
    assert mock_account_service_connection.client.organization_stub.create.call_count == 1


def test_create_default_workspace_that_exist(mock_account_service_connection):
    mock_account_service_connection.client.workspace_stub.find.return_value = Mock(
        total_matched_count=1, workspaces=[Mock(id="w123456")]
    )

    workspace_id = mock_account_service_connection.client.create_default_workspace(organization_id="o123456")

    assert workspace_id == "w123456"
    assert mock_account_service_connection.client.workspace_stub.find.call_count == 1
    assert mock_account_service_connection.client.workspace_stub.create.call_count == 0


def test_create_default_workspace_that_does_not_exist(mock_account_service_connection):
    mock_account_service_connection.client.workspace_stub.find.return_value = Mock(total_matched_count=0, workspaces=[])
    mock_account_service_connection.client.workspace_stub.create.return_value = Mock(id="w123456")

    workspace_id = mock_account_service_connection.client.create_default_workspace(organization_id="o123456")

    assert workspace_id == "w123456"
    assert mock_account_service_connection.client.workspace_stub.find.call_count == 1
    assert mock_account_service_connection.client.workspace_stub.create.call_count == 1


def test_create_initial_user_that_exist(mock_account_service_connection):
    mock_account_service_connection.client.user_stub.find.return_value = Mock(
        total_matched_count=1, users=[Mock(id="u123456")]
    )

    user_id = mock_account_service_connection.client.create_initial_user(organization_id="o123456")

    assert user_id == "u123456"
    assert mock_account_service_connection.client.user_stub.find.call_count == 1
    assert mock_account_service_connection.client.user_stub.create.call_count == 0


def test_create_initial_user_that_does_not_exist(mock_account_service_connection):
    mock_account_service_connection.client.user_stub.find.return_value = Mock(total_matched_count=0, users=[])
    mock_account_service_connection.client.user_stub.create.return_value = Mock(id="u123456")

    user_id = mock_account_service_connection.client.create_initial_user(organization_id="o123456")

    assert user_id == "u123456"
    assert mock_account_service_connection.client.user_stub.find.call_count == 1
    assert mock_account_service_connection.client.user_stub.create.call_count == 1


def test_modify_initial_user_external_id(mock_account_service_connection):
    mock_account_service_connection.client.user_stub.modify.return_value = Mock(external_id="e_id")

    external_id = mock_account_service_connection.client.update_user_external_id(
        uid="u123456", organization_id="o123456", external_id="e_id"
    )

    assert external_id == "e_id"


def test_update_user_id_spicedb(mock_account_service_connection, mock_postgresql_connection):
    mock_user = custom_mock_usertype(uid="u123456", mail="example@dot.com")
    mock_account_service_connection.update_user_id_spicedb(
        postgresql_connection=mock_postgresql_connection, user_mail=mock_user["mail"], user_uid=mock_user["uid"]
    )


def test_update_user_id_spicedb_without_email(mock_account_service_connection, mock_postgresql_connection):
    mock_user = custom_mock_usertype(uid="u123456", mail=None)
    with pytest.raises(ValueError) as ex:
        mock_account_service_connection.update_user_id_spicedb(
            postgresql_connection=mock_postgresql_connection, user_mail=mock_user["mail"], user_uid=mock_user["uid"]
        )
    assert "Cannot update user because of missing email." in str(ex.value)
