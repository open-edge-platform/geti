# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import http
import json

import requests

from models.error import AccountServiceError
from models.meta import CamelJsonizable

from config.env import account_service_grpc_gateway_address, api_v1_prefix, protocol


class MembershipDeleteRequest(CamelJsonizable):
    def __init__(self, user_id, organization_id):
        self.user_id = user_id
        self.organization_id = organization_id


class UserStatusRequest(CamelJsonizable):
    def __init__(self, status, user_id, organization_id, created_by=None):
        self.status = status
        self.user_id = user_id
        self.organization_id = organization_id
        self.created_by = created_by


class MembershipStatusCreateRequest(CamelJsonizable):
    def __init__(self, status):
        self.status = status


class MembershipStatusRequest(CamelJsonizable):
    def __init__(self, status, user_id, organization_id):
        self.status = MembershipStatusCreateRequest(status=status)
        self.user_id = user_id
        self.organization_id = organization_id


class MembershipRequest:
    def __init__(
        self,
        organization_id,
        first_name=None,
        second_name=None,
        email=None,
        status=None,
        created_at=None,
        name=None,
        sort_by=None,
        sort_direction=None,
        skip=None,
        limit=None,
    ):
        self.organization_id = organization_id
        self.first_name = first_name
        self.second_name = second_name
        self.email = email
        self.status = status
        self.created_at = created_at
        self.name = name
        self.sort_by = sort_by
        self.sort_direction = sort_direction
        self.skip = skip
        self.limit = limit

    def to_json(self):
        return {
            "organization_id": self.organization_id,
            "first_name": self.first_name,
            "second_name": self.second_name,
            "email": self.email,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "name": self.name,
            "sort_by": self.sort_by,
            "sort_direction": self.sort_direction,
            "skip": self.skip,
            "limit": self.limit,
        }


class ListMembershipResponse:
    def __init__(self, memberships, total_count, total_matched_count, next_page=None):
        self.memberships = memberships
        self.total_count = total_count
        self.total_matched_count = total_matched_count
        self.next_page = next_page

    @classmethod
    def from_json(cls, json_data):
        memberships = [MembershipResponse.from_json(m) for m in json_data.get("memberships", [])]
        total_count = json_data.get("totalCount")
        total_matched_count = json_data.get("totalMatchedCount")
        next_page = json_data.get("nextPage")
        return ListMembershipResponse(memberships, total_count, total_matched_count, next_page)


class MembershipResponse:
    def __init__(self, id, user_id, first_name, second_name, email, status, created_at):
        self.id = id
        self.user_id = user_id
        self.first_name = first_name
        self.second_name = second_name
        self.email = email
        self.status = status
        self.created_at = created_at

    @classmethod
    def from_json(cls, json_data):
        id = json_data.get("id")
        user_id = json_data.get("userId")
        first_name = json_data.get("firstName")
        second_name = json_data.get("secondName")
        email = json_data.get("email")
        status = json_data.get("status")
        created_at = json_data.get("createdAt")
        return cls(id, user_id, first_name, second_name, email, status, created_at)


class UserStatus(CamelJsonizable):
    def __init__(self, id, status, organization_id, user_id, created_at, created_by, last_logout_date=None):
        self.id = id
        self.status = status
        self.organization_id = organization_id
        self.last_logout_date = last_logout_date
        self.user_id = user_id
        self.created_at = created_at
        self.created_by = created_by

    @classmethod
    def change(cls, request: UserStatusRequest):
        response = requests.put(
            f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/{request.organization_id}/users/{request.user_id}/statuses",
            json=request.to_json(),
        )
        json_returned = json.loads(response.content)
        if response.status_code != http.HTTPStatus.OK:
            raise AccountServiceError.from_json_response(json_returned, response.status_code)
        return cls.from_json(json_returned)

    @classmethod
    def modify(cls, request: MembershipStatusRequest):
        response = requests.put(
            f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/{request.organization_id}/memberships/{request.user_id}",
            json=request.to_json(),
        )
        json_returned = json.loads(response.content)
        if response.status_code != http.HTTPStatus.OK:
            raise AccountServiceError.from_json_response(json_returned, response.status_code)
        return cls.from_json(json_returned)

    @classmethod
    def logout(cls, signed_token):
        response = requests.post(
            f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/logout",
            headers={"x-auth-request-access-token": signed_token},
        )
        assert response.headers.get("Set-Cookie"), f"{response.headers}"
        if response.status_code != http.HTTPStatus.OK:
            json_returned = json.loads(response.content)
            raise AccountServiceError.from_json_response(json_returned, response.status_code)

    @classmethod
    def get_memberships(cls, request: MembershipRequest):
        response = requests.get(
            f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/{request.organization_id}/memberships",
            params=request.to_json(),
        )
        json_returned = json.loads(response.content)
        if response.status_code != http.HTTPStatus.OK:
            raise AccountServiceError.from_json_response(json_returned, response.status_code)
        return ListMembershipResponse.from_json(json_returned)

    @classmethod
    def delete(cls, request: MembershipDeleteRequest):
        response = requests.delete(
            f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/{request.organization_id}/memberships/{request.user_id}",
            params=request.to_json(),
        )
        json_returned = json.loads(response.content)
        if response.status_code != http.HTTPStatus.OK:
            raise AccountServiceError.from_json_response(json_returned, response.status_code)
