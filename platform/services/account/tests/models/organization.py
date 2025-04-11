# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from __future__ import annotations

import http
import json
from copy import deepcopy

import requests
from utils.data_gen import gen_random_str

from models.error import AccountServiceError
from models.meta import CamelJsonizable, Meta, Randomizable
from models.user import User

from config.env import account_service_grpc_gateway_address, api_v1_prefix, protocol


class FindOrganizationRequest(CamelJsonizable):
    def __init__(
        self,
        id=None,
        name=None,
        country=None,
        location=None,
        type=None,
        cell_id=None,
        status=None,
        created_at_from=None,
        created_at_to=None,
        created_by=None,
        modified_at_from=None,
        modified_at_to=None,
        modified_by=None,
        skip=None,
        limit=None,
        sort_by=None,
        sort_direction=None,
        request_access_reason=None,
    ):
        self.id = id
        self.name = name
        self.country = country
        self.location = location
        self.type = type
        self.cell_id = cell_id
        self.status = status
        self.created_at_from = created_at_from
        self.created_at_to = created_at_to
        self.created_by = created_by
        self.modified_at_from = modified_at_from
        self.modified_at_to = modified_at_to
        self.modified_by = modified_by
        self.skip = skip
        self.limit = limit
        self.sort_by = sort_by
        self.sort_direction = sort_direction
        self.request_access_reason = request_access_reason


class ListOrganizationsResponse(CamelJsonizable):
    def __init__(self, organizations: list[OrganizationWithAdmins], total_count, total_matched_count, next_page):
        self.organizations = organizations
        self.total_count = total_count
        self.total_matched_count = total_matched_count
        self.next_page = next_page

    @classmethod
    def from_json(cls, json_obj: dict):
        orgs_returned = json_obj["organizations"]
        orgs = []
        for org in orgs_returned:
            orgs.append(OrganizationWithAdmins.from_json(org))

        json_obj["organizations"] = orgs
        return super().from_json(json_obj)


class Organization(Meta, Randomizable):
    def __init__(
        self,
        id="",
        name="",
        country="",
        location="",
        type="",
        cell_id="",
        status="",
        created_at=None,
        created_by="",
        modified_at=None,
        modified_by="",
        request_access_reason="",
    ):
        super().__init__(id, created_at, created_by, modified_at, modified_by)

        self.name = name
        self.country = country
        self.location = location
        self.type = type
        self.cell_id = cell_id
        self.status = status
        self.request_access_reason = request_access_reason

    @classmethod
    def randomize(cls, **kwargs):
        init_params = {
            "name": gen_random_str(),
            "country": "CAN",
            "location": "Ottawa",
            "type": "B2C",
            "cell_id": "1234",
            "status": "ACT",
            "request_access_reason": gen_random_str(),
        }
        init_params.update(kwargs)
        return cls(**init_params)

    def create(self, headers: dict = None):
        response = requests.post(
            f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations",
            json=self.to_json(),
            headers=headers,
        )
        json_returned = json.loads(response.content)
        if response.status_code != http.HTTPStatus.OK:
            raise AccountServiceError.from_json_response(json_returned, response.status_code)
        self.id = json_returned["id"]
        return Organization.from_json(json_returned)

    def modify(self, headers: dict = None):
        endpoint = f"{api_v1_prefix}/organizations/{self.id}"
        response = requests.put(
            f"{protocol}{account_service_grpc_gateway_address}{endpoint}", json=self.to_json(), headers=headers
        )
        assert response.status_code == http.HTTPStatus.OK
        json_returned = json.loads(response.content)
        return Organization.from_json(json_returned)

    def delete(self):
        response = requests.delete(
            f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/{self.id}"
        )
        assert response.status_code == http.HTTPStatus.OK

    def add_photo(self, photo_filepath: str):
        with open(photo_filepath, mode="rb") as photo_file:
            response = requests.post(
                f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/{self.id}/photos",
                files={"file": photo_file},
            )
            assert response.status_code == http.HTTPStatus.OK, (
                f"Got response {response.status_code}, expected {http.HTTPStatus.OK}"
            )

    def get_photo_presigned_url(self) -> str | None:
        response = requests.get(
            f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/{self.id}/photos"
        )
        if response.status_code == http.HTTPStatus.NOT_FOUND:
            return None
        assert response.status_code == http.HTTPStatus.OK, (
            f"Got response {response.status_code}, expected {http.HTTPStatus.OK}"
        )
        json_response = response.json()
        presigned_url = json_response["presignedUrl"]
        assert presigned_url is not None
        return presigned_url

    def delete_photo(self) -> bool:
        """returns True if photo has been deleted, False if it wasn't present already"""
        response = requests.delete(
            f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/{self.id}/photos"
        )
        assert response.status_code in (http.HTTPStatus.OK, http.HTTPStatus.NOT_FOUND)
        return response.status_code == http.HTTPStatus.OK

    def send_invitation(self, user: User = None, invitation_request: dict = None) -> None:
        if invitation_request is None:
            if user is None:
                raise ValueError("'invitation_request' or 'user' must be provided")
            invitation_request = {
                "organizationData": self.to_json(),
                "adminData": user.to_json(),
            }

        response = requests.post(
            f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/invitations",
            json=invitation_request,
        )

        json_returned = json.loads(response.content)
        if response.status_code != http.HTTPStatus.OK:
            raise AccountServiceError.from_json_response(json_returned, response.status_code)


class AdminSimpleData(CamelJsonizable):
    def __init__(self, first_name="", last_name="", email=""):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email


class OrganizationWithAdmins(Organization):
    def __init__(
        self,
        id="",
        name="",
        country="",
        location="",
        type="",
        cell_id="",
        status="",
        created_at=None,
        created_by="",
        modified_at=None,
        modified_by="",
        admins=None,
        request_access_reason="",
    ):
        super().__init__(
            id,
            name,
            country,
            location,
            type,
            cell_id,
            status,
            created_at,
            created_by,
            modified_at,
            modified_by,
            request_access_reason,
        )
        self.admins = admins

    def __eq__(self, other):
        if isinstance(other, Organization):
            copy_of_myself = deepcopy(self)
            del copy_of_myself.admins
            return copy_of_myself.__dict__ == other.__dict__
        return super().__eq__(other)

    @classmethod
    def from_json(cls, json_obj: dict):
        admins = []
        admins_json = json_obj["admins"]
        for admin_json in admins_json:
            admin = AdminSimpleData.from_json(admin_json)
            admins.append(admin)

        json_obj["admins"] = admins
        return super().from_json(json_obj)

    @classmethod
    def get(cls, id) -> OrganizationWithAdmins | None:
        response = requests.get(f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/{id}")
        if response.status_code == http.HTTPStatus.NOT_FOUND:
            return None
        assert response.status_code == http.HTTPStatus.OK
        org_returned = json.loads(response.content)
        return cls.from_json(org_returned)

    @classmethod
    def find(cls, request: FindOrganizationRequest) -> ListOrganizationsResponse:
        base_url = f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations"
        params = request.to_json()
        req = requests.models.PreparedRequest()
        req.prepare_url(base_url, params)
        response = requests.get(req.url)

        if response.status_code == http.HTTPStatus.BAD_REQUEST:
            raise AccountServiceError.from_json_response(json.loads(response.content), response.status_code)

        assert response.status_code == http.HTTPStatus.OK, (
            f"Got: {response.status_code} , expected: {http.HTTPStatus.OK}"
        )

        response_json = json.loads(response.content)
        return ListOrganizationsResponse.from_json(response_json)
