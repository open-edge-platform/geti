# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import json

import requests
from requests.exceptions import HTTPError

from models.error import AccountServiceError
from models.meta import CamelJsonizable

from config.env import account_service_grpc_gateway_address, api_v1_prefix, protocol


class PersonalAccessTokenCreateRequest(CamelJsonizable):
    def __init__(self, organization_id, created_by, name, description, expires_at, user_id=None):
        self.organization_id = organization_id
        self.user_id = user_id
        self.created_by = created_by
        self.name = name
        self.description = description
        self.expires_at = expires_at


class PersonalAccessTokenExtendRequest(CamelJsonizable):
    def __init__(self, organization_id, user_id, id, expires_at):
        self.organization_id = organization_id
        self.user_id = user_id
        self.id = id
        self.expires_at = expires_at


class PersonalAccessTokenCreateResponse(CamelJsonizable):
    def __init__(
        self, id, partial, name, description, expires_at, organization_id, personal_access_token, user_id, created_at
    ):
        self.id = id
        self.partial = partial
        self.name = name
        self.description = description
        self.expires_at = expires_at
        self.organization_id = organization_id
        self.user_id = user_id
        self.personal_access_token = personal_access_token
        self.created_at = created_at


class PersonalAccessTokenResponse(CamelJsonizable):
    def __init__(self, id, partial, name, description, expires_at, organization_id, user_id, created_at):
        self.partial = partial
        self.name = name
        self.description = description
        self.expires_at = expires_at
        self.organization_id = organization_id
        self.user_id = user_id
        self.created_at = created_at


class PersonalAccessTokenFindRequest(CamelJsonizable):
    def __init__(
        self,
        name=None,
        description=None,
        partial=None,
        expires_at_from=None,
        expires_at_to=None,
        created_at_from=None,
        created_at_to=None,
        sort_by=None,
        sort_direction=None,
    ):
        self.name = name
        self.description = description
        self.partial = partial
        self.expires_at_from = expires_at_from
        self.expires_at_to = expires_at_to
        self.created_at_from = created_at_from
        self.created_at_to = created_at_to
        self.sort_by = sort_by
        self.sort_direction = sort_direction


class ListPersonalAccessTokensResponse(CamelJsonizable):
    def __init__(self, personal_access_tokens: list[PersonalAccessTokenResponse]):
        self.personal_access_tokens = personal_access_tokens

    @classmethod
    def from_json(cls, json_obj: dict):
        personal_access_tokens_returned = json_obj["personalAccessTokens"]
        personal_access_tokens = []
        for pat in personal_access_tokens_returned:
            personal_access_tokens.append(PersonalAccessTokenResponse.from_json(pat))

        json_obj["personalAccessTokens"] = personal_access_tokens
        return super().from_json(json_obj)


class PersonalAccessToken:
    @staticmethod
    def create(request: PersonalAccessTokenCreateRequest, headers: dict = None) -> PersonalAccessTokenCreateResponse:
        endpoint = f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/{request.organization_id}/users/{request.user_id}/personal_access_tokens"
        # uncomment if the FEATURE_FLAG_MANAGE_USERS is enabled
        # endpoint = f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/personal_access_tokens"
        request_body = request.to_json()
        response = requests.post(endpoint, json=request_body, headers=headers)
        json_returned = json.loads(response.content)
        try:
            response.raise_for_status()
        except HTTPError as http_err:
            raise AccountServiceError.from_json_response(
                json_response=json_returned, http_status_code=response.status_code
            ) from http_err
        return PersonalAccessTokenCreateResponse.from_json(json_returned)

    @staticmethod
    def get_org_from_token(token: str) -> str:
        endpoint = f"{api_v1_prefix}/personal_access_tokens/organization"
        base_url = f"{protocol}{account_service_grpc_gateway_address}{endpoint}"
        response = requests.get(base_url, headers={"x-auth-request-access-token": token})
        json_returned = json.loads(response.content)
        try:
            response.raise_for_status()
        except HTTPError as http_err:
            raise AccountServiceError.from_json_response(
                json_response=json_returned, http_status_code=response.status_code
            ) from http_err
        return json_returned["organizationId"]

    @staticmethod
    def get_by_hash(hash: str) -> PersonalAccessTokenResponse:
        endpoint = f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/personal_access_tokens/{hash}"
        response = requests.get(endpoint)
        json_returned = json.loads(response.content)
        try:
            response.raise_for_status()
        except HTTPError as http_err:
            raise AccountServiceError.from_json_response(
                json_response=json_returned, http_status_code=response.status_code
            ) from http_err
        return PersonalAccessTokenResponse.from_json(json_returned)

    @staticmethod
    def find(
        organization_id: str, user_id: str, request: PersonalAccessTokenFindRequest = None
    ) -> ListPersonalAccessTokensResponse:
        endpoint = f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/{organization_id}/users/{user_id}/personal_access_tokens"
        if request is None:
            request = PersonalAccessTokenFindRequest()
        query_params = request.to_json()
        req = requests.models.PreparedRequest()
        req.prepare_url(endpoint, query_params)
        response = requests.get(req.url)
        json_returned = json.loads(response.content)
        try:
            response.raise_for_status()
        except HTTPError as http_err:
            raise AccountServiceError.from_json_response(
                json_response=json_returned, http_status_code=response.status_code
            ) from http_err

        return ListPersonalAccessTokensResponse.from_json(json_returned)

    @staticmethod
    def revoke(organization_id, user_id, id, headers: dict) -> requests.Response:
        endpoint = f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/{organization_id}/users/{user_id}/personal_access_tokens/{id}"
        # uncomment if the FEATURE_FLAG_MANAGE_USERS is enabled
        # endpoint = f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/personal_access_tokens/{id}"
        response = requests.delete(endpoint, headers=headers)
        return response

    @staticmethod
    def extend(req: PersonalAccessTokenExtendRequest, headers: dict) -> PersonalAccessTokenResponse:
        endpoint = f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/{req.organization_id}/users/{req.user_id}/personal_access_tokens/{req.id}"
        # uncomment if the FEATURE_FLAG_MANAGE_USERS is enabled
        # endpoint = f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/personal_access_tokens/{req.id}"
        response = requests.patch(endpoint, json=req.to_json(), headers=headers)
        json_returned = json.loads(response.content)
        try:
            response.raise_for_status()
        except HTTPError as http_err:
            raise AccountServiceError.from_json_response(
                json_response=json_returned, http_status_code=response.status_code
            ) from http_err
        return PersonalAccessTokenResponse.from_json(json_returned)
