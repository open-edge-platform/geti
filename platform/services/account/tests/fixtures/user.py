# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import jwt
import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from models.user import RoleOperation, User, UserRole, UserRoleOperation

from fixtures.organization import organization

from config.consts import TEST_PHOTO_FILEPATH


@pytest.fixture
def user(organization):
    user = User.randomize(organization_id=organization.id)
    user_returned = user.create()
    yield user_returned
    user_returned.delete()


@pytest.fixture
def registered_user(organization):
    user = User.randomize(organization_id=organization.id, status="RGS")
    user_returned = user.create()
    yield user_returned
    user_returned.delete()


@pytest.fixture
def recreated_user(user):
    user_with_same_email = User.randomize(
        organization_id=user.organization_id,
        email=user.email,
        # external_id in cidaas stays the same across
        # different users with the same email
        external_id=user.external_id,
    )

    user.status = "DEL"
    user.modify()

    user_returned = user_with_same_email.create()
    assert user_returned.id != user.id
    assert user_returned.email == user.email
    assert user_returned.external_id == user.external_id
    assert user_returned.organization_id == user.organization_id
    yield user_returned
    user_returned.delete()


different_organization = organization


@pytest.fixture
def recreated_user_in_different_organization(user, different_organization):
    user_with_same_email = User.randomize(
        organization_id=different_organization.id,
        email=user.email,
        # external_id in cidaas stays the same across
        # different users with the same email
        external_id=user.external_id,
    )

    user.status = "DEL"
    user.modify()

    user_returned = user_with_same_email.create()
    assert user_returned.id != user.id
    assert user_returned.email == user.email
    assert user_returned.external_id == user.external_id
    assert user_returned.organization_id != user.organization_id
    yield user_returned
    user_returned.delete()


@pytest.fixture
def organization_admin(user, organization):
    role = UserRole("organization_admin", "organization", organization.id)
    user.set_roles([UserRoleOperation(role, RoleOperation.CREATE)])
    return user


@pytest.fixture
def organization_contributor(user, organization):
    role = UserRole("organization_contributor", "organization", organization.id)
    user.set_roles([UserRoleOperation(role, RoleOperation.CREATE)])
    return user


@pytest.fixture
def user_photo(user):
    user.add_photo(TEST_PHOTO_FILEPATH)
    yield
    user.delete_photo()


def _create_token(user):
    private_key = _generate_private_key()

    external_token_payload = {"email": user.email}

    token_payload = {
        "preferred_username": user.id,
        "organization_id": user.organization_id,
        "external_token": jwt.encode(payload=external_token_payload, algorithm="RS512", key=private_key),
    }

    return jwt.encode(payload=token_payload, algorithm="RS512", key=private_key)


@pytest.fixture
def signed_token(user) -> str:
    return _create_token(user)


@pytest.fixture
def registred_user_signed_token(registered_user) -> str:
    return _create_token(registered_user)


@pytest.fixture
def signed_token_invalid_user() -> str:
    invalid_user = User(id="123", organization_id="123", email="idontexist@gmail.com")
    return _create_token(invalid_user)


@pytest.fixture
def invalid_token_missing_email(user) -> str:
    private_key = _generate_private_key()

    external_token_payload = {}

    token_payload = {
        "preferred_username": user.id,
        "organization_id": user.organization_id,
        "external_token": jwt.encode(payload=external_token_payload, algorithm="RS512", key=private_key),
    }

    return jwt.encode(payload=token_payload, algorithm="RS512", key=private_key)


@pytest.fixture
def invalid_token_missing_external(user) -> str:
    private_key = _generate_private_key()

    token_payload = {"preferred_username": user.id, "organization_id": user.organization_id}

    return jwt.encode(payload=token_payload, algorithm="RS512", key=private_key)


def _generate_private_key():
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),  # Increase key size here
    )
