# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import base64
import os
import secrets
from unittest import mock
from unittest.mock import MagicMock, call, mock_open

import jwt
import ldap
import pytest
from geti_spicedb_tools import AccessResourceTypes, RoleMutationOperations, SpiceDBResourceTypes, SpiceDBUserRoles

from users_handler import string as utils_string
from users_handler.exceptions import InvalidEmail, UserAlreadyExists, UserHandlerError
from users_handler.users_handler import AuthorizationRelationships, UsersHandler, UserType

TEST_USER_PREFIX = os.environ.get("TEST_USER_PREFIX", "unit_tests_")
# environment variable is set explicitly so everyone should be aware that such environment variable is needed
# because we have singleton for SpiceDB, when env var is set using mock.patch.dict such change will be global
os.environ["SPICEDB_CREDENTIALS"] = "token"


@pytest.fixture
def random_user():
    user_id = TEST_USER_PREFIX + secrets.token_urlsafe(8)
    name = f"Test User {user_id}"
    mail = f"{user_id}@example.com"
    passwd = utils_string.random_str(32)
    password = base64.urlsafe_b64encode(passwd.encode()).decode()
    return name, user_id, mail, password


@pytest.fixture
def mock_user() -> UserType:
    mocked_user = MagicMock(spec=UserType)
    d = {"mail": "example@test.com", "uid": "fake user id"}
    mocked_user.__getitem__.side_effect = d.__getitem__
    return mocked_user


def test_base64():
    password = "helloworld".encode("ascii")
    encoded = UsersHandler._ab64_encode(password)
    decoded = UsersHandler._ab64_decode(encoded)
    assert decoded == password


@mock.patch.dict(os.environ, {"SPICEDB_CREDENTIALS": "token_and_ssl"})
def test_token_and_ssl(mocker, random_user):
    mocker.patch("users_handler.users_handler.ldap.initialize", MagicMock())
    change_user_rel_mock = mocker.patch("geti_spicedb_tools.spicedb.SpiceDB.change_user_relation", MagicMock())
    open_files_mock = mocker.patch("builtins.open", mock_open(read_data=b"fake body of cert/key"))
    uh_mock = UsersHandler(user="fake_user", password="fake_password", host="server", port=123)
    name, user_id, mail, password = random_user
    auth_rels = [
        AuthorizationRelationships(
            resource_type=SpiceDBResourceTypes.WORKSPACE,
            resource_id="123",
            relations=[SpiceDBUserRoles.WORKSPACE.value["admin"]],
        )
    ]

    return_value = uh_mock.add_user(
        name=name, uid=user_id, mail=mail, password=password, authorization_relationships=auth_rels
    )

    assert open_files_mock.call_count == 3  # 3 files are opened
    assert return_value and change_user_rel_mock.call_count == len(auth_rels)


@mock.patch.dict(os.environ, {"SPICEDB_CREDENTIALS": "token_and_ca"})
def test_token_and_ca(mocker, random_user):
    mocker.patch("users_handler.users_handler.ldap.initialize", MagicMock())
    change_user_rel_mock = mocker.patch("geti_spicedb_tools.spicedb.SpiceDB.change_user_relation", MagicMock())
    # force singleton to reinitialize
    mocker.patch("users_handler.users_handler.SpiceDB._instance", None)
    open_file_mock = mocker.patch("builtins.open", mock_open(read_data=b"fake body of cert/keys"))
    uh_mock = UsersHandler(user="fake_user", password="fake_password", host="server", port=123)
    name, user_id, mail, password = random_user
    auth_rels = [
        AuthorizationRelationships(
            resource_type=SpiceDBResourceTypes.WORKSPACE,
            resource_id="123",
            relations=[SpiceDBUserRoles.WORKSPACE.value["admin"]],
        )
    ]

    return_value = uh_mock.add_user(
        name=name, uid=user_id, mail=mail, password=password, authorization_relationships=auth_rels
    )
    assert open_file_mock.call_count == 1  # 1 file is opened
    assert return_value and change_user_rel_mock.call_count == len(auth_rels)


@mock.patch.dict(os.environ, {"SPICEDB_CREDENTIALS": "token"})
def test_token(mocker, random_user):
    mocker.patch("users_handler.users_handler.ldap.initialize", MagicMock())
    change_user_rel_mock = mocker.patch("geti_spicedb_tools.spicedb.SpiceDB.change_user_relation", MagicMock())
    # force singleton to reinitialize
    mocker.patch("users_handler.users_handler.SpiceDB._instance", None)
    open_file_mock = mocker.patch("builtins.open", mock_open(read_data=b"fake body of cert/keys"))
    uh_mock = UsersHandler(user="fake_user", password="fake_password", host="server", port=123)
    name, user_id, mail, password = random_user
    auth_rels = [
        AuthorizationRelationships(
            resource_type=SpiceDBResourceTypes.WORKSPACE,
            resource_id="123",
            relations=[SpiceDBUserRoles.WORKSPACE.value["admin"]],
        )
    ]

    return_value = uh_mock.add_user(
        name=name, uid=user_id, mail=mail, password=password, authorization_relationships=auth_rels
    )
    assert open_file_mock.call_count == 0  # no files opened
    assert return_value and change_user_rel_mock.call_count == len(auth_rels)


def test_auth_rel_add_user(mocker, random_user):
    mocker.patch("users_handler.users_handler.ldap.initialize", MagicMock())
    change_user_rel_mock = mocker.patch("geti_spicedb_tools.spicedb.SpiceDB.change_user_relation", MagicMock())
    mocker.patch("builtins.open", mock_open(read_data=b"fake body of cert/key"))
    uh_mock = UsersHandler(user="fake_user", password="fake_password", host="server", port=123)
    name, user_id, mail, password = random_user
    auth_rels = [
        AuthorizationRelationships(
            resource_type=SpiceDBResourceTypes.WORKSPACE,
            resource_id="123",
            relations=[SpiceDBUserRoles.WORKSPACE.value["admin"]],
        )
    ]

    return_value = uh_mock.add_user(
        name=name, uid=user_id, mail=mail, password=password, authorization_relationships=auth_rels
    )

    assert return_value and change_user_rel_mock.call_count == len(auth_rels)


def test_empty_auth_rel_add_user(mocker, random_user):
    mocker.patch("users_handler.users_handler.ldap.initialize", MagicMock())
    change_user_rel_mock = mocker.patch("geti_spicedb_tools.spicedb.SpiceDB.change_user_relation", MagicMock())
    uh_mock = UsersHandler(user="fake_user", password="fake_password", host="server", port=123)
    name, user_id, mail, password = random_user

    return_value = uh_mock.add_user(
        name=name, uid=user_id, mail=mail, password=password, authorization_relationships=[]
    )

    assert return_value and change_user_rel_mock.call_count == 0


def test_add_user_ldap_error(mocker, random_user):
    """
    Tests the UsersHandler.add_user method, negative case.

    Covers the scenario in which adding the user to LDAP raises an error.
    """
    ldap_init_mock = mocker.patch("users_handler.users_handler.ldap.initialize", MagicMock())
    ldap_conn_mock = MagicMock()
    ldap_conn_mock.add_s = MagicMock()
    ldap_conn_mock.add_s.side_effect = ldap.LDAPError
    ldap_init_mock.side_effect = [ldap_conn_mock]

    mocker.patch("geti_spicedb_tools.spicedb.SpiceDB.change_user_relation", MagicMock())
    del_rels_mock = mocker.patch("geti_spicedb_tools.spicedb.SpiceDB.delete_relations", MagicMock())
    mocker.patch("builtins.open", mock_open(read_data=b"fake body of cert/key"))

    uh_mock = UsersHandler(user="fake_user", password="fake_password", host="server", port=123)
    name, user_id, mail, password = random_user
    auth_rels = [
        AuthorizationRelationships(
            resource_type=SpiceDBResourceTypes.WORKSPACE,
            resource_id="123",
            relations=[SpiceDBUserRoles.WORKSPACE.value["admin"]],
        )
    ]

    with pytest.raises(UserHandlerError):
        uh_mock.add_user(name=name, uid=user_id, mail=mail, password=password, authorization_relationships=auth_rels)

    assert del_rels_mock.call_count == 1 and del_rels_mock.call_args.kwargs == {
        "user_id": uh_mock._base64_encode(user_id),
        "object_type": "user",
    }


def test_auth_rel_modify_user_relation(mocker):
    mocker.patch("users_handler.users_handler.ldap.initialize", MagicMock())
    mocker.patch("users_handler.users_handler.SpiceDB.__init__", MagicMock(return_value=None))
    uh_mock = UsersHandler(user="fake_user", password="fake_password", host="server", port=123)

    mocker_change = mocker.patch("users_handler.users_handler.SpiceDB.change_user_relation", MagicMock())
    user_id = "fake_user@test.com"
    user_encoded_id = uh_mock._base64_encode("fake_user@test.com")
    relationships = [
        AuthorizationRelationships(
            resource_type=SpiceDBResourceTypes.WORKSPACE,
            resource_id="123",
            relations=[SpiceDBUserRoles.WORKSPACE.value["admin"]],
            operation="CREATE",
        )
    ]
    uh_mock.modify_user_roles(user_id, relationships)
    assert mocker_change.call_count == 1
    mocker_change.assert_called_once_with(
        resource_type=SpiceDBResourceTypes.WORKSPACE,
        user_id=user_encoded_id,
        resource_id="123",
        relations=[SpiceDBUserRoles.WORKSPACE.value["admin"]],
        operation="CREATE",
    )
    mocker_change.assert_has_calls(
        [
            call(
                resource_type=SpiceDBResourceTypes.WORKSPACE,
                user_id=user_encoded_id,
                resource_id="123",
                relations=[SpiceDBUserRoles.WORKSPACE.value["admin"]],
                operation="CREATE",
            )
        ]
    )


def test_auth_rel_delete_user(mocker):
    mocker.patch("users_handler.users_handler.ldap.initialize", MagicMock())
    delete_relations_mock = mocker.patch("geti_spicedb_tools.spicedb.SpiceDB.delete_relations", MagicMock())
    uh_mock = UsersHandler(user="fake_user", password="fake_password", host="server", port=123)
    user_id = "fake_user@test.com"
    ret = uh_mock.delete_user(user_id)

    delete_relations_mock.assert_called_once()
    assert ret


def test_generate_unique_uid(mocker):
    """Tests the UsersHandler._generate_unique_uid method."""
    mocker.patch("users_handler.users_handler.ldap.initialize", MagicMock())
    mocker.patch("geti_spicedb_tools.spicedb.SpiceDB", MagicMock())
    validate_unique_entry_mock = mocker.patch(
        "users_handler.users_handler.UsersHandler.validate_unique_entry", MagicMock()
    )
    validate_unique_entry_mock.side_effect = [UserAlreadyExists, None]
    uh_mock = UsersHandler(user="fake_user", password="fake_password", host="server", port=123)
    random_str_mock = mocker.patch("users_handler.users_handler.utils_string.random_str", MagicMock())
    random_str_mock.side_effect = ["uid1", "uid2"]

    uid_actual = uh_mock._generate_unique_uid()

    assert uid_actual == "uid2"


def test_get_user_roles(mocker):
    mocker.patch("users_handler.users_handler.ldap.initialize", MagicMock())
    return_value = [("123", "admin"), ("234", "contributor")]
    get_user_roles_mock = mocker.patch("geti_spicedb_tools.spicedb.SpiceDB.get_user_roles")
    get_user_roles_mock.return_value = return_value

    uh = UsersHandler(user="fake_user", password="fake_password", host="server", port=123)
    response = uh.get_user_roles(
        uid="test_user",
        resource_type="workspace",
        resource_id="1234",
    )

    assert response == return_value
    get_user_roles_mock.assert_called_once_with(
        user_id="dGVzdF91c2Vy",  # `echo -n test_user | base64`
        resource_type="workspace",
        resource_id="1234",
    )


def test_would_modify_user_roles_remove_all_workspace_roles_works_when_not_removing_any_roles(mocker):
    mocker.patch("users_handler.users_handler.ldap.initialize", MagicMock())
    return_value = [("123", "admin"), ("234", "contributor")]
    get_user_roles_mock = mocker.patch("geti_spicedb_tools.spicedb.SpiceDB.get_user_roles")
    get_user_roles_mock.return_value = return_value

    uh = UsersHandler(user="fake_user", password="fake_password", host="server", port=123)

    result = uh.would_modify_user_roles_remove_all_workspace_roles(
        uid="test_user",
        authorization_relationships=[
            AuthorizationRelationships(
                resource_type=SpiceDBResourceTypes.WORKSPACE,
                resource_id="123",
                relations=[SpiceDBUserRoles.WORKSPACE.value["admin"]],
                operation=RoleMutationOperations.DELETE,
            )
        ],
    )

    assert result is False


def test_would_modify_user_roles_remove_all_workspace_roles_works_when_empty_roles(mocker):
    mocker.patch("users_handler.users_handler.ldap.initialize", MagicMock())
    return_value = []
    get_user_roles_mock = mocker.patch("geti_spicedb_tools.spicedb.SpiceDB.get_user_roles")
    get_user_roles_mock.return_value = return_value

    uh = UsersHandler(user="fake_user", password="fake_password", host="server", port=123)

    result = uh.would_modify_user_roles_remove_all_workspace_roles(
        uid="test_user",
        authorization_relationships=[
            AuthorizationRelationships(
                resource_type=SpiceDBResourceTypes.WORKSPACE,
                resource_id="123",
                relations=[SpiceDBUserRoles.WORKSPACE.value["admin"]],
                operation=RoleMutationOperations.DELETE,
            )
        ],
    )

    assert result is True


def test_would_modify_user_roles_remove_all_workspace_roles_works_when_removing_all_roles(mocker):
    mocker.patch("users_handler.users_handler.ldap.initialize", MagicMock())
    return_value = [("123", "admin")]
    get_user_roles_mock = mocker.patch("geti_spicedb_tools.spicedb.SpiceDB.get_user_roles")
    get_user_roles_mock.return_value = return_value

    uh = UsersHandler(user="fake_user", password="fake_password", host="server", port=123)

    authorization_relationships = []

    for resource_type in AccessResourceTypes:
        for role in ["admin", "contributor"]:
            for object_id in ["123", "234"]:
                if role not in SpiceDBUserRoles[resource_type.name].value:
                    continue
                relation = SpiceDBUserRoles[resource_type.name].value[role]
                authorization_relationships.append(
                    AuthorizationRelationships(
                        resource_type=resource_type,
                        resource_id=object_id,
                        relations=[relation],
                        operation=RoleMutationOperations.DELETE,
                    )
                )
    result = uh.would_modify_user_roles_remove_all_workspace_roles(
        uid="test_user", authorization_relationships=authorization_relationships
    )

    assert result is True


def test_get_user_from_jwt_header(mocker):
    """
    Tests the get_user_from_jwt_header method.

    Covers a positive, non-error scenario.
    """
    mocker.patch("users_handler.users_handler.ldap.initialize", MagicMock())
    mocker.patch("geti_spicedb_tools.spicedb.SpiceDB", MagicMock())

    # Mock the user returned by get_user with an arbitrary, unique object.
    get_user_mock = mocker.patch("users_handler.users_handler.UsersHandler.get_user")
    user_expected = MagicMock(UserType)
    get_user_mock.side_effect = [user_expected]

    uid: str = "admin@example.com"

    jwt_decode_mock = mocker.patch("users_handler.users_handler.jwt.decode")
    jwt_decode_mock.return_value = {
        "preferred_username": uid,
    }

    users_handler = UsersHandler(user="fake_user", password="fake_password", host="server", port=123)

    user_actual: UserType = users_handler.get_user_from_jwt_header(header="FAKE JWT VALUE")

    assert user_actual is user_expected and get_user_mock.call_args.args == (uid,)

    jwt_decode_mock.assert_called_once_with(
        jwt="FAKE JWT VALUE",
        options={
            "verify_signature": False,
            "verify_exp": True,
        },
    )


def test_get_user_from_jwt_header_fails_for_invalid_jwt(mocker):
    """
    Tests the get_user_from_jwt_header method for invalid JWT
    """
    mocker.patch("users_handler.users_handler.ldap.initialize", MagicMock())
    mocker.patch("geti_spicedb_tools.spicedb.SpiceDB", MagicMock())

    jwt_decode_mock = mocker.patch("users_handler.users_handler.jwt.decode")
    jwt_decode_mock.side_effect = jwt.DecodeError("Invalid JWT")

    users_handler = UsersHandler(user="fake_user", password="fake_password", host="server", port=123)

    with pytest.raises(TypeError, match=r"Problem during JWT decoding"):
        users_handler.get_user_from_jwt_header(header="FAKE JWT VALUE")

    jwt_decode_mock.assert_called_once_with(
        jwt="FAKE JWT VALUE",
        options={
            "verify_signature": False,
            "verify_exp": True,
        },
    )


@pytest.mark.parametrize(
    "invalid_uid",
    (
        pytest.param(None, id="simulate missing key in JWT"),
        pytest.param(False, id="bool instead of string"),
        pytest.param(12, id="int instead of string"),
        pytest.param([], id="list instead of string"),
        pytest.param({}, id="dict instead of string"),
    ),
)
def test_get_user_from_jwt_header_fails_for_invalid_uid(mocker, invalid_uid):
    """
    Tests the get_user_from_jwt_header method for invalid UID in the JWT
    """
    mocker.patch("users_handler.users_handler.ldap.initialize", MagicMock())
    mocker.patch("geti_spicedb_tools.spicedb.SpiceDB", MagicMock())

    jwt_decode_mock = mocker.patch("users_handler.users_handler.jwt.decode")
    jwt_decode_mock.return_value = {
        "preferred_username": invalid_uid,
    }

    users_handler = UsersHandler(user="fake_user", password="fake_password", host="server", port=123)

    with pytest.raises(TypeError, match=rf"Expected the uid to be an instance of {str}, got {type(invalid_uid)}."):
        users_handler.get_user_from_jwt_header(header="FAKE JWT VALUE")

    jwt_decode_mock.assert_called_once_with(
        jwt="FAKE JWT VALUE",
        options={
            "verify_signature": False,
            "verify_exp": True,
        },
    )


@pytest.mark.parametrize(
    ["email", "should_pass"],
    [
        ("user@example.com", True),
        ("jan.pawel@gmail.com", True),
        ("name_123~!#$%^&*{}|-=+@sub.domain.com", True),
        ("invalid-email", False),
        ("@missing-username.com", False),
        ("user@invalid domain.com", False),
        ("email@example", False),
        ("Joe <email@example.com>", False),
        ("email@example.com (Joe Smith)", False),
        ("t@s", False),
        ("verylongemailaddressthatsahouldnotpassinthewholeworld@example.com", False),
        ("GoodEmailExample../@intel.com", False),
    ],
)
def test_is_email_valid(email, should_pass):
    if should_pass:
        assert UsersHandler.is_email_valid(email)
    else:
        with pytest.raises(InvalidEmail):
            UsersHandler.is_email_valid(email)
