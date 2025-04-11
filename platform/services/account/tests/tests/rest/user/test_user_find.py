# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import http

from fixtures.organization import organization
from fixtures.user import user
from models.error import AccountServiceError
from models.organization import Organization
from models.user import FindUserRequest, RoleOperation, User, UserRole, UserRoleOperation
from models.user_status import UserStatus, UserStatusRequest
from models.workspace import Workspace

from config.env import FF_MANAGE_USERS


def test_find_by_name(user):
    """Check if it is possible to find user by first name, second name, email using single name parameter"""
    find_requests = [
        FindUserRequest(name=user.first_name),
        FindUserRequest(name=user.second_name),
        FindUserRequest(name=user.email),
    ]
    returned_users = []
    for request in find_requests:
        returned_users.extend(User.find(user.organization_id, request).users)

    assert len(returned_users) == 3
    assert returned_users[0] == returned_users[1] == returned_users[2]


user1 = user
user2 = user
user3 = user


def test_find_users(user, user1, user2, user3):
    find_request = FindUserRequest(second_name=user2.second_name)
    find_response = User.find(user.organization_id, find_request)

    assert find_response.total_matched_count == 1
    for user in find_response.users:
        assert user.second_name == find_request.second_name
    assert find_response.total_count >= 4


def test_find_users_complex():
    orga = Organization.randomize()
    orga_returned = orga.create()
    usera1 = User.randomize(organization_id=orga_returned.id)
    usera1_returned = usera1.create()
    usera2 = User.randomize(organization_id=orga_returned.id)
    usera2_returned = usera2.create()

    orgb = Organization.randomize()
    orgb_returned = orgb.create()
    userb1 = User.randomize(organization_id=orgb_returned.id)
    userb1.create()
    userb2 = User.randomize(organization_id=orgb_returned.id)
    userb2.create()

    find_request = FindUserRequest()
    find_response = User.find(orga_returned.id, find_request)
    assert find_response.total_matched_count == 2
    found_users_ids = [user.id for user in find_response.users]
    assert usera1_returned.id in found_users_ids
    assert usera2_returned.id in found_users_ids

    userb2.delete()
    userb1.delete()
    orgb.delete()

    usera2.delete()
    usera1.delete()
    orga.delete()


def test_find_users_multi(user):
    orga = Organization.randomize()
    orga_returned = orga.create()
    worka = Workspace.randomize(organization_id=orga_returned.id)
    _ = worka.create()
    usera = User.randomize(organization_id=orga_returned.id)
    usera.send_invitation([])
    orgb = Organization.randomize()
    orgb_returned = orgb.create()
    workb = Workspace.randomize(organization_id=orgb_returned.id)
    _ = workb.create()
    userb = User.randomize(organization_id=orgb_returned.id, external_id=usera.external_id, first_name=usera.first_name)
    userb.send_invitation([])

    find_request = FindUserRequest(external_id=usera.external_id)
    find_response = User.find("", find_request)
    assert find_response.total_matched_count == 2
    usera.delete()
    userb.delete()
    orga.delete()
    orgb.delete()


def test_find_users_complex_sort_asc():
    orga = Organization.randomize()
    orga_returned = orga.create()
    usera1 = User.randomize(organization_id=orga_returned.id)
    usera1_returned = usera1.create()
    usera1_returned.status = "SSP"
    usera1_returned.modify()
    usera1_returned = User.get_by_id(usera1_returned.id, organization_id=orga_returned.id)
    usera1_returned.organization_status = orga_returned.status

    usera2 = User.randomize(organization_id=orga_returned.id)
    usera2_returned = usera2.create()

    orgb = Organization.randomize()
    orgb_returned = orgb.create()
    userb1 = User.randomize(organization_id=orgb_returned.id)
    userb1.create()
    userb2 = User.randomize(organization_id=orgb_returned.id)
    userb2.create()

    find_request = FindUserRequest(sort_by="status", sort_direction="asc")
    find_response = User.find(orga_returned.id, find_request)
    assert find_response.total_matched_count == 2
    found_users_ids = [user.id for user in find_response.users]
    assert usera1_returned.id in found_users_ids
    assert usera2_returned.id in found_users_ids
    # user 1 has suspended status - which should be sorted after active user in ascending order
    assert find_response.users[1].id == usera1_returned.id

    userb2.delete()
    userb1.delete()
    orgb.delete()

    usera2.delete()
    usera1.delete()
    orga.delete()


def test_find_users_complex_nonexistent_org():
    orga = Organization.randomize()
    orga_returned = orga.create()
    usera1 = User.randomize(organization_id=orga_returned.id)
    usera1.create()
    usera2 = User.randomize(organization_id=orga_returned.id)
    usera2.create()

    orgb = Organization.randomize()
    orgb_returned = orgb.create()
    userb1 = User.randomize(organization_id=orgb_returned.id)
    userb1.create()
    userb2 = User.randomize(organization_id=orgb_returned.id)
    userb2.create()

    find_request = FindUserRequest()
    find_response = User.find("392d4d04-cf37-4ff7-bb88-7b87bf1e2fc4", find_request)
    assert find_response.total_matched_count == 0
    assert len(find_response.users) == 0

    userb2.delete()
    userb1.delete()
    orgb.delete()

    usera2.delete()
    usera1.delete()
    orga.delete()


def test_find_users_complex_pagination():
    orga = Organization.randomize()
    orga_returned = orga.create()
    orga_users = []
    for _ in range(10):
        usera = User.randomize(organization_id=orga_returned.id)
        usera_returned = usera.create()
        orga_users.append(usera_returned)

    orgb = Organization.randomize()
    orgb_returned = orgb.create()
    orgb_users = []
    for _ in range(50):
        userb = User.randomize(organization_id=orgb_returned.id)
        userb_returned = userb.create()
        orgb_users.append(userb_returned)

    find_request = FindUserRequest(limit=20)
    find_response = User.find(orgb_returned.id, find_request)
    assert len(find_response.users) == 20
    assert find_response.total_matched_count == 50
    assert find_response.next_page.limit == 20
    assert find_response.next_page.skip == 20

    find_request = FindUserRequest(limit=20, skip=find_response.next_page.skip)
    find_response = User.find(orgb_returned.id, find_request)
    assert len(find_response.users) == 20
    assert find_response.total_matched_count == 50
    assert find_response.next_page.limit == 10
    assert find_response.next_page.skip == 40

    find_request = FindUserRequest(limit=15, skip=find_response.next_page.skip)
    find_response = User.find(orgb_returned.id, find_request)
    # users exhausted, 10 left
    assert len(find_response.users) == 10
    assert find_response.total_matched_count == 50
    assert find_response.next_page.limit == 0

    orgb.delete()
    orga.delete()


org0 = organization
org1 = organization
org2 = organization


def test_find_users_proper_total_count_change_status(org0, org1, org2):
    org0_users = []
    for _ in range(4):
        user = User.randomize(organization_id=org0.id, status="RGS")
        user_created = user.create()
        org0_users.append(user_created)

    org1_users = []
    for _ in range(5):
        user = User.randomize(organization_id=org1.id, status="RGS")
        role = UserRole("organization_admin", "organization", org1.id)
        role_ops = [UserRoleOperation(role, RoleOperation.CREATE)]
        user_created = user.create()
        user_created.set_roles(role_ops)
        org1_users.append(user_created)

    if not FF_MANAGE_USERS:
        req = UserStatusRequest(status="ACT", user_id=org1_users[0].id, organization_id=org1.id)
        UserStatus.change(req)
        req = UserStatusRequest(status="SSP", user_id=org1_users[0].id, organization_id=org1.id)
        UserStatus.change(req)
        org1_users[0].status = "SSP"
        req = UserStatusRequest(status="ACT", user_id=org1_users[2].id, organization_id=org1.id)
        UserStatus.change(req)
        org1_users[2].status = "ACT"
        req = UserStatusRequest(status="ACT", user_id=org1_users[4].id, organization_id=org1.id)
        UserStatus.change(req)
        org1_users[4].status = "ACT"

    org2_users = []
    for _ in range(6):
        user = User.randomize(organization_id=org2.id)
        user_created = user.create()
        org2_users.append(user_created)

    find_request = FindUserRequest(email=org1_users[0].email)
    find_response = User.find(org1.id, find_request)

    assert find_response.total_matched_count == 1
    for user in find_response.users:
        org1_users_ids = [org1_user.id for org1_user in org1_users]
        assert user.id in org1_users_ids
    assert find_response.total_count == 5

    find_request = FindUserRequest(email=org0_users[0].email)
    find_response = User.find(org0.id, find_request)

    assert find_response.total_matched_count == 1
    for user in find_response.users:
        org0_users_ids = [org0_user.id for org0_user in org0_users]
        assert user.id in org0_users_ids
    assert find_response.total_count == 4


def test_find_users_proper_total_count_modify_user_status(org0, org1, org2):
    org0_users = []
    for _ in range(4):
        user = User.randomize(organization_id=org0.id, status="RGS")
        user_created = user.create()
        org0_users.append(user_created)

    org1_users = []
    for _ in range(5):
        user = User.randomize(organization_id=org1.id, status="RGS")
        user_created = user.create()
        org1_users.append(user_created)

    org1_users[0].status = "ACT"
    org1_users[0].modify()

    org1_users[0].status = "SSP"
    org1_users[0].modify()

    org1_users[2].status = "ACT"
    org1_users[2].modify()

    org1_users[4].status = "ACT"
    org1_users[4].modify()

    org2_users = []
    for _ in range(6):
        user = User.randomize(organization_id=org2.id)
        user_created = user.create()
        org2_users.append(user_created)

    find_request = FindUserRequest(email=org1_users[0].email)
    find_response = User.find(org1.id, find_request)

    assert find_response.total_matched_count == 1
    for user in find_response.users:
        org1_users_ids = [org1_user.id for org1_user in org1_users]
        assert user.id in org1_users_ids
    assert find_response.total_count == 5

    find_request = FindUserRequest(email=org0_users[0].email)
    find_response = User.find(org0.id, find_request)

    assert find_response.total_matched_count == 1
    for user in find_response.users:
        org0_users_ids = [org0_user.id for org0_user in org0_users]
        assert user.id in org0_users_ids
    assert find_response.total_count == 4


def test_find_users_exclude_deleted_status(organization):
    nondeleted_users = []
    for _ in range(10):
        user = User.randomize(organization_id=organization.id, status="ACT")
        user_created = user.create()
        nondeleted_users.append(user_created)

    for _ in range(5):
        user = User.randomize(organization_id=organization.id, status="SSP")
        user_created = user.create()
        nondeleted_users.append(user_created)

    for _ in range(5):
        user = User.randomize(organization_id=organization.id, status="DEL")
        user.create()

    find_request = FindUserRequest()
    find_response = User.find(organization_id=organization.id, request=find_request)

    assert {usr.id for usr in find_response.users} == {usr.id for usr in nondeleted_users}
    assert find_response.total_matched_count == 15
    assert find_response.total_count == 15


def test_find_users_invalid_organization_id():
    find_request = FindUserRequest()
    try:
        User.find(organization_id="000000000000000000000001", request=find_request)
    except AccountServiceError as error:
        assert "malformed organization's UUID" in error.message
        assert "SQLSTATE" not in error.message
        assert error.status_code == http.HTTPStatus.BAD_REQUEST
