# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import http
import json

import requests

from models.error import AccountServiceError
from models.meta import CamelJsonizable

from config.env import account_service_grpc_gateway_address, api_v1_prefix, protocol


class UserMembershipRequest:
    def __init__(self, user_id, organization_name=None, sort_by=None, sort_direction=None, skip=None, limit=None):
        self.user_id = user_id
        self.organization_name = organization_name
        self.sort_by = sort_by
        self.sort_direction = sort_direction
        self.skip = skip
        self.limit = limit

    def to_json(self):
        return {
            "user_id": self.user_id,
            "organization_name": self.organization_name,
            "sort_by": self.sort_by,
            "sort_direction": self.sort_direction,
            "skip": self.skip,
            "limit": self.limit,
        }


class UserMembershipResponse:
    def __init__(self, id, organization_id, organization_name, status, created_at):
        self.id = id
        self.organization_id = organization_id
        self.organization_name = organization_name
        self.status = status
        self.created_at = created_at

    @classmethod
    def from_json(cls, json_data):
        id = json_data.get("id")
        organization_id = json_data.get("organizationId")
        organization_name = json_data.get("organizationName")
        status = json_data.get("status")
        created_at = json_data.get("createdAt")
        return cls(id, organization_id, organization_name, status, created_at)


class ListUserMembershipResponse:
    def __init__(self, memberships, total_count, total_matched_count, next_page=None):
        self.memberships = memberships
        self.total_count = total_count
        self.total_matched_count = total_matched_count
        self.next_page = next_page

    @classmethod
    def from_json(cls, json_data):
        memberships = [UserMembershipResponse.from_json(m) for m in json_data.get("memberships", [])]
        total_count = json_data.get("totalCount")
        total_matched_count = json_data.get("totalMatchedCount")
        next_page = json_data.get("nextPage")
        return ListUserMembershipResponse(memberships, total_count, total_matched_count, next_page)


class Membership(CamelJsonizable):
    def __init__(self, id, status, organization_id, user_id, created_at, created_by, last_logout_date=None):
        self.id = id
        self.status = status
        self.organization_id = organization_id
        self.last_logout_date = last_logout_date
        self.user_id = user_id
        self.created_at = created_at
        self.created_by = created_by

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
    def get_user_memberships(cls, request: UserMembershipRequest):
        response = requests.get(
            f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/users/{request.user_id}/memberships",
            params=request.to_json(),
        )
        json_returned = json.loads(response.content)
        if response.status_code != http.HTTPStatus.OK:
            raise AccountServiceError.from_json_response(json_returned, response.status_code)
        return ListUserMembershipResponse.from_json(json_returned)
