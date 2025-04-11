# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from __future__ import annotations

import http
import json
import urllib
from datetime import datetime
from enum import Enum

import requests
from utils.data_gen import gen_random_b64, gen_random_str

from models.error import AccountServiceError
from models.meta import CamelJsonizable, DictComparable, Meta, Randomizable

from config.env import account_service_grpc_gateway_address, api_v1_prefix, protocol


class RoleOperation(str, Enum):
    CREATE = "CREATE"
    DELETE = "DELETE"
    TOUCH = "TOUCH"


class UserRole(CamelJsonizable, DictComparable):
    def __init__(self, role: str, resource_type: str, resource_id: str):
        self.role = role
        self.resource_type = resource_type
        self.resource_id = resource_id


class UserRoleOperation(CamelJsonizable):
    def __init__(self, role: UserRole, operation: RoleOperation):
        self.role = role
        self.operation = operation

    def to_json(self):
        return {"role": self.role.to_json(), "operation": self.operation.value}

    @classmethod
    def from_json(cls, json_obj):
        return cls(role=UserRole.from_json(json_obj["role"]), operation=RoleOperation(json_obj["operation"]))


class FindUserRequest(CamelJsonizable):
    def __init__(
        self,
        name=None,
        first_name=None,
        second_name=None,
        email=None,
        external_id=None,
        country=None,
        status=None,
        last_successful_login_from=None,
        last_successful_login_to=None,
        role=None,
        resource_type=None,
        resource_id=None,
        workspace_id=None,
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
    ):
        self.name = name
        self.first_name = first_name
        self.second_name = second_name
        self.email = email
        self.external_id = external_id
        self.country = country
        self.status = status
        self.last_successful_login_from = last_successful_login_from
        self.last_successful_login_to = last_successful_login_to
        self.role = role
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.workspace_id = workspace_id
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


class GetUsersRequest:
    def __init__(
        self,
        name=None,
        first_name=None,
        second_name=None,
        email=None,
        external_id=None,
        country=None,
        status=None,
        last_successful_login_from=None,
        last_successful_login_to=None,
        created_at_from=None,
        created_at_to=None,
        modified_at_from=None,
        modified_at_to=None,
        user_consent_from=None,
        user_consent_to=None,
        skip=None,
        limit=None,
        sort_by=None,
        sort_direction=None,
    ):
        self.name = name
        self.first_name = first_name
        self.second_name = second_name
        self.email = email
        self.external_id = external_id
        self.country = country
        self.status = status
        self.last_successful_login_from = last_successful_login_from
        self.last_successful_login_to = last_successful_login_to
        self.created_at_from = created_at_from
        self.created_at_to = created_at_to
        self.modified_at_from = modified_at_from
        self.modified_at_to = modified_at_to
        self.user_consent_from = user_consent_from
        self.user_consent_to = user_consent_to
        self.skip = skip
        self.limit = limit
        self.sort_by = sort_by
        self.sort_direction = sort_direction

    def to_json(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}


class GetUsersResponse:
    def __init__(
        self,
        id,
        first_name,
        second_name,
        email,
        external_id,
        country,
        photo_location,
        registration_token,
        last_successful_login,
        current_successful_login,
        created_at,
        created_by,
        modified_at,
        modified_by,
        telemetry_consent,
        telemetry_consent_at,
        user_consent,
        user_consent_at,
    ):
        self.id = id
        self.first_name = first_name
        self.second_name = second_name
        self.email = email
        self.external_id = external_id
        self.country = country
        self.photo_location = photo_location
        self.registration_token = registration_token
        self.last_successful_login = last_successful_login
        self.current_successful_login = current_successful_login
        self.created_at = created_at
        self.created_by = created_by
        self.modified_at = modified_at
        self.modified_by = modified_by
        self.telemetry_consent = telemetry_consent
        self.telemetry_consent_at = telemetry_consent_at
        self.user_consent = user_consent
        self.user_consent_at = user_consent_at

    @classmethod
    def from_json(cls, json_data):
        id = json_data.get("id")
        first_name = json_data.get("firstName")
        second_name = json_data.get("second_Name")
        email = json_data.get("email")
        external_id = json_data.get("externalId")
        country = json_data.get("country")
        photo_location = json_data.get("photoLocation")
        registration_token = json_data.get("registrationToken")
        last_successful_login = cls.parse_timestamp(json_data.get("lastSuccessfulLogin"))
        current_successful_login = cls.parse_timestamp(json_data.get("currentSuccessfulLogin"))
        created_at = cls.parse_timestamp(json_data.get("createdAt"))
        created_by = json_data.get("createdBy")
        modified_at = cls.parse_timestamp(json_data.get("modifiedAt"))
        modified_by = json_data.get("modifiedBy")
        telemetry_consent = json_data.get("telemetryConsent")
        telemetry_consent_at = cls.parse_timestamp(json_data.get("telemetryConsentAt"))
        user_consent = json_data.get("userConsent")
        user_consent_at = cls.parse_timestamp(json_data.get("userConsentAt"))
        return cls(
            id,
            first_name,
            second_name,
            email,
            external_id,
            country,
            photo_location,
            registration_token,
            last_successful_login,
            current_successful_login,
            created_at,
            created_by,
            modified_at,
            modified_by,
            telemetry_consent,
            telemetry_consent_at,
            user_consent,
            user_consent_at,
        )

    @staticmethod
    def parse_timestamp(timestamp):
        if timestamp:
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return None


class ListUsersResponseNextPage(CamelJsonizable):
    def __init__(self, limit: int, skip: int):
        self.limit = limit
        self.skip = skip


class ListUsersResponse(CamelJsonizable):
    def __init__(
        self, users: list[User], total_count: int, total_matched_count: int, next_page: ListUsersResponseNextPage
    ):
        self.users = users
        self.total_count = total_count
        self.total_matched_count = total_matched_count
        self.next_page = next_page

    @classmethod
    def from_json(cls, json_obj: dict):
        users_returned = json_obj["users"]
        users = []
        for user in users_returned:
            users.append(User.from_json(user))

        json_obj["users"] = users

        next_page_returned = json_obj["nextPage"]
        next_page = ListUsersResponseNextPage.from_json(next_page_returned)
        json_obj["nextPage"] = next_page

        return super().from_json(json_obj)


class RolePayload(CamelJsonizable):
    def __init__(self, role: str, resource_id: str):
        self.role = role
        self.resource_id = resource_id


class RolesResponse(CamelJsonizable):
    def __init__(self, roles: list[RolePayload]):
        self.roles = roles


class ListGetUsersResponse(CamelJsonizable):
    def __init__(
        self,
        users: list[GetUsersResponse],
        total_count: int,
        total_matched_count: int,
        next_page: ListUsersResponseNextPage,
    ):
        self.users = users
        self.total_count = total_count
        self.total_matched_count = total_matched_count
        self.next_page = next_page

    @classmethod
    def from_json(cls, json_obj: dict):
        users_returned = json_obj["users"]
        users = []
        for user in users_returned:
            users.append(GetUsersResponse.from_json(user))

        json_obj["users"] = users

        next_page_returned = json_obj["nextPage"]
        next_page = ListUsersResponseNextPage.from_json(next_page_returned)
        json_obj["nextPage"] = next_page

        return super().from_json(json_obj)


class SendInvitationResponse(CamelJsonizable):
    def __init__(self, user_id):
        self.user_id = user_id


# noinspection DuplicatedCode
class OrganizationExtended(CamelJsonizable):
    def __init__(
        self,
        organization_name=None,
        user_status=None,
        organization_status=None,
        organization_id=None,
        organization_created_at=None,
    ):
        self.organization_name = organization_name
        self.user_status = user_status
        self.organization_status = organization_status
        self.organization_id = organization_id
        self.organization_created_at = organization_created_at


class UserProfileData(CamelJsonizable):
    def __init__(
        self,
        status=None,
        organization_id=None,
        organization_status=None,
        telemetry_consent=None,
        telemetry_consent_at=None,
        user_consent=None,
        user_consent_at=None,
        organizations: list[OrganizationExtended] = None,
    ):
        self.status = status
        self.organization_id = organization_id
        self.organization_status = organization_status
        self.organizations = organizations
        self.telemetry_consent = telemetry_consent
        self.telemetry_consent_at = telemetry_consent_at
        self.user_consent = user_consent
        self.user_consent_at = user_consent_at

    @classmethod
    def from_json(cls, json_obj: dict):
        extended_organizations_returned = json_obj["organizations"]
        extended_organizations = []
        for organization in extended_organizations_returned:
            extended_organizations.append(OrganizationExtended.from_json(organization))

        json_obj["organizations"] = extended_organizations

        return super().from_json(json_obj)


class User(Meta, Randomizable):
    def __init__(
        self,
        id="",
        first_name="",
        created_at=None,
        created_by="",
        modified_at=None,
        modified_by="",
        second_name="",
        email="",
        external_id="",
        country="",
        status="",
        organization_id="",
        organization_status="",
        last_successful_login=None,
        last_logout_date=None,
        current_successful_login=None,
        roles=None,
        telemetry_consent=None,
        telemetry_consent_at=None,
        user_consent=None,
        user_consent_at=None,
        presigned_url="",
    ):
        super().__init__(id, created_at, created_by, modified_at, modified_by)

        self.first_name = first_name
        self.second_name = second_name
        self.email = email
        self.external_id = external_id
        self.country = country
        self.status = status
        self.organization_id = organization_id
        self.organization_status = organization_status
        self.last_successful_login = last_successful_login
        self.last_logout_date = last_logout_date
        self.current_successful_login = current_successful_login
        self.roles = roles
        self.telemetry_consent = telemetry_consent
        self.telemetry_consent_at = telemetry_consent_at
        self.user_consent = user_consent
        self.user_consent_at = user_consent_at
        self.presigned_url = presigned_url

    def __repr__(self):
        return (
            f"User({self.id=}, {self.first_name=}, {self.email=}, {self.external_id}, {self.country}, {self.status}, "
            f"{self.organization_id=}, {self.organization_status=}, {self.last_successful_login=}, {self.current_successful_login=},{self.created_at=}, "
            f"{self.created_by=}, {self.modified_at=}, {self.modified_by=})"
        )

    def __hash__(self):
        return hash(repr(self))

    @classmethod
    def randomize(cls, organization_id, **kwargs):
        init_params = {
            "first_name": gen_random_str(),
            "second_name": gen_random_str(),
            "email": f"{gen_random_str()}@example.com",
            "external_id": gen_random_b64(),
            "country": "POL",
            "status": "ACT",
            "organization_id": organization_id,
        }
        init_params.update(kwargs)
        return cls(**init_params)

    def create(self, headers: dict = None) -> User:
        response = requests.post(
            f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/{self.organization_id}/users",
            json=self.to_json(),
            headers=headers,
        )
        json_returned = json.loads(response.content)
        if response.status_code != http.HTTPStatus.OK:
            raise AccountServiceError.from_json_response(json_returned, response.status_code)
        self.id = json_returned["id"]
        return User.from_json(json_returned)

    def delete(self):
        response = requests.delete(
            f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/{self.organization_id}/users/{self.id}"
        )
        assert response.status_code == http.HTTPStatus.OK, (
            f"Got: {response.status_code} , expected: {http.HTTPStatus.OK}"
        )

    def get_roles(self, resource_type: str) -> list[UserRole]:
        response = requests.get(
            f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/{self.organization_id}/users/{self.id}/roles/{resource_type}"
        )
        response_json = response.json()
        if response.status_code != http.HTTPStatus.OK:
            raise AccountServiceError.from_json_response(
                json_response=response_json, http_status_code=response.status_code
            )
        roles_dict_list = response_json["roles"]
        roles: list[UserRole] = []
        for role_dict in roles_dict_list:
            role = UserRole.from_json(role_dict)
            roles.append(role)
        return roles

    def get_user_roles(self) -> dict:
        response = requests.get(
            f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/{self.organization_id}/membership/{self.id}/roles"
        )
        response_json = response.json()
        if response.status_code != http.HTTPStatus.OK:
            raise AccountServiceError.from_json_response(
                json_response=response_json, http_status_code=response.status_code
            )
        return response_json

    def assign_user_role(self, payload: RolePayload):
        response = requests.post(
            f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/{self.organization_id}/membership/{self.id}/roles",
            json=payload.to_json(),
        )
        response_json = response.json()
        if response.status_code != http.HTTPStatus.OK:
            raise AccountServiceError.from_json_response(
                json_response=response_json, http_status_code=response.status_code
            )

    def delete_role(self, payload: RolePayload):
        # Construct the query parameters from the payload
        query_params = {
            "role": payload.role,
            "resource_id": payload.resource_id,
        }

        # Build the URL with query parameters
        url = (
            f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/"
            f"{self.organization_id}/membership/{self.id}/roles"
        )

        response = requests.delete(url, params=query_params)

        # Parse and handle the response
        response_json = response.json()
        if response.status_code != http.HTTPStatus.OK:
            raise AccountServiceError.from_json_response(
                json_response=response_json, http_status_code=response.status_code
            )

    def set_roles(self, role_ops: list[UserRoleOperation]):
        roles_in_request_body = []
        request_body = {"roles": roles_in_request_body}

        for role_op in role_ops:
            roles_in_request_body.append(role_op.to_json())
        response = requests.put(
            f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}"
            f"/organizations/{self.organization_id}/users/{self.id}/roles",
            json=request_body,
        )
        response_json = response.json()
        if response.status_code != http.HTTPStatus.OK:
            raise AccountServiceError.from_json_response(
                json_response=response_json, http_status_code=response.status_code
            )

    @classmethod
    def find(cls, organization_id: str, request: FindUserRequest) -> ListUsersResponse:
        endpoint = f"{api_v1_prefix}/organizations/{organization_id}/users"
        base_url = f"{protocol}{account_service_grpc_gateway_address}{endpoint}"
        query_params = request.to_json()
        req = requests.models.PreparedRequest()
        req.prepare_url(base_url, query_params)
        response = requests.get(req.url)

        response_json = json.loads(response.content)

        if response.status_code != http.HTTPStatus.OK:
            raise AccountServiceError.from_json_response(response_json, response.status_code)

        return ListUsersResponse.from_json(response_json)

    def modify(self, headers: dict = None):
        endpoint = f"{api_v1_prefix}/organizations/{self.organization_id}/users/{self.id}"
        response = requests.put(
            f"{protocol}{account_service_grpc_gateway_address}{endpoint}", json=self.to_json(), headers=headers
        )

        response_json = json.loads(response.content)

        if response.status_code != http.HTTPStatus.OK:
            raise AccountServiceError.from_json_response(response_json, response.status_code)

        return User.from_json(response_json)

    @classmethod
    def get_by_external_id(cls, id):
        endpoint = f"{api_v1_prefix}/organizations/users/external"
        base_url = f"{protocol}{account_service_grpc_gateway_address}{endpoint}"
        # noinspection PyUnresolvedReferences
        urlencoded_id = urllib.parse.quote_plus(id)
        query_params = {"id": urlencoded_id}
        req = requests.models.PreparedRequest()
        req.prepare_url(base_url, query_params)
        response = requests.get(req.url)
        json_response = json.loads(response.content)
        if response.status_code != http.HTTPStatus.OK:
            raise AccountServiceError.from_json_response(json_response, response.status_code)
        return User.from_json(json_response)

    @classmethod
    def get_by_id(cls, id, organization_id):
        endpoint = f"{api_v1_prefix}/organizations/{organization_id}/users/{id}"
        response = requests.get(f"{protocol}{account_service_grpc_gateway_address}{endpoint}")
        if response.status_code == http.HTTPStatus.NOT_FOUND:
            return None
        assert response.status_code == http.HTTPStatus.OK
        user_returned = json.loads(response.content)
        return cls.from_json(user_returned)

    @classmethod
    def get_active_user(cls, organization_id, token):
        endpoint = f"{api_v1_prefix}/organizations/{organization_id}/activeUser"
        response = requests.get(
            f"{protocol}{account_service_grpc_gateway_address}{endpoint}",
            headers={"x-auth-request-access-token": token},
        )
        if response.status_code == http.HTTPStatus.NOT_FOUND:
            return None
        assert response.status_code == http.HTTPStatus.OK
        user_returned = json.loads(response.content)
        return cls.from_json(user_returned)

    @staticmethod
    def get_user_profile(token) -> UserProfileData:
        endpoint = f"{api_v1_prefix}/profile"
        response = requests.get(
            f"{protocol}{account_service_grpc_gateway_address}{endpoint}",
            headers={"x-auth-request-access-token": token},
        )
        json_response = json.loads(response.content)
        if response.status_code != http.HTTPStatus.OK:
            raise AccountServiceError.from_json_response(json_response, response.status_code)
        return UserProfileData.from_json(json_response)

    def add_photo(self, photo_filepath: str):
        with open(photo_filepath, mode="rb") as photo_file:
            response = requests.post(
                f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}"
                f"/organizations/{self.organization_id}/users/{self.id}/photos",
                files={"file": photo_file},
            )
            assert response.status_code == http.HTTPStatus.OK

    def get_photo_presigned_url(self, x_forwarded_host_header: str = None) -> str | None:
        request_headers = {}
        if x_forwarded_host_header:
            request_headers["x-forwarded-host"] = x_forwarded_host_header
        response = requests.get(
            f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}"
            f"/organizations/{self.organization_id}/users/{self.id}/photos",
            headers=request_headers,
        )
        if response.status_code == http.HTTPStatus.NOT_FOUND:
            return None
        assert response.status_code == http.HTTPStatus.OK
        json_response = response.json()
        presigned_url = json_response["presignedUrl"]
        assert presigned_url is not None
        return presigned_url

    def delete_photo(self) -> bool:
        """returns True if photo has been deleted, False if it wasn't present already"""
        response = requests.delete(
            f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}"
            f"/organizations/{self.organization_id}/users/{self.id}/photos"
        )
        assert response.status_code in (http.HTTPStatus.OK, http.HTTPStatus.NOT_FOUND)
        return response.status_code == http.HTTPStatus.OK

    def send_invitation(self, initial_role_ops: list[UserRoleOperation]) -> SendInvitationResponse:
        invitation_request = {"user": self.to_json(), "roles": [role_op.to_json() for role_op in initial_role_ops]}
        response = requests.post(
            f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}"
            f"/organizations/{self.organization_id}/users/invitations",
            json=invitation_request,
        )
        json_returned = json.loads(response.content)
        if response.status_code != http.HTTPStatus.OK:
            raise AccountServiceError.from_json_response(json_returned, response.status_code)
        invitation_response = SendInvitationResponse.from_json(json_returned)
        self.id = invitation_response.user_id
        return invitation_response

    @classmethod
    def get_users_list(cls, request: GetUsersRequest) -> ListUsersResponse:
        response = requests.get(
            f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/users", params=request.to_json()
        )
        json_returned = json.loads(response.content)
        if response.status_code != http.HTTPStatus.OK:
            raise AccountServiceError.from_json_response(json_returned, response.status_code)
        return ListGetUsersResponse.from_json(json_returned)
