# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from __future__ import annotations

import http
import json

import requests
from utils.data_gen import gen_random_str

from models.error import AccountServiceError
from models.meta import CamelJsonizable, DictComparable, Meta, Randomizable

from config.env import account_service_grpc_gateway_address, api_v1_prefix, protocol


class FindWorkspaceRequest(CamelJsonizable):
    def __init__(
        self,
        name=None,
        billing_child_account_id=None,
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
        self.billing_child_account_id = billing_child_account_id
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


class ListWorkspacesResponse(CamelJsonizable):
    def __init__(self, workspaces, total_count, total_matched_count, next_page):
        self.workspaces = workspaces
        self.total_count = total_count
        self.total_matched_count = total_matched_count
        self.next_page = next_page

    @classmethod
    def from_json(cls, json_obj: dict):
        workspaces_returned = json_obj["workspaces"]
        workspaces = []
        for workspace in workspaces_returned:
            workspaces.append(Workspace.from_json(workspace))

        json_obj["workspaces"] = workspaces
        return super().from_json(json_obj)


class Workspace(Meta, DictComparable, Randomizable):
    def __init__(
        self, id="", name="", created_at=None, created_by="", modified_at=None, modified_by="", organization_id=""
    ):
        super().__init__(id, created_at, created_by, modified_at, modified_by)

        self.name = name
        self.organization_id = organization_id

    @classmethod
    def randomize(cls, organization_id, **kwargs):
        init_params = {"name": gen_random_str(), "organization_id": organization_id}
        init_params.update(kwargs)
        return cls(**init_params)

    def create(self, headers: dict = None):
        response = requests.post(
            f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/{self.organization_id}/workspaces",
            json=self.to_json(),
            headers=headers,
        )
        json_returned = json.loads(response.content)
        if response.status_code != http.HTTPStatus.OK:
            raise AccountServiceError.from_json_response(json_returned, response.status_code)

        self.id = json_returned["id"]
        return Workspace.from_json(json_returned)

    def delete(self):
        response = requests.delete(
            f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/{self.organization_id}/workspaces/{self.id}"
        )
        assert response.status_code == http.HTTPStatus.OK, (
            f"Got: {response.status_code} , expected: {http.HTTPStatus.OK}"
        )

    @classmethod
    def get(cls, id, organization_id) -> Workspace | None:
        response = requests.get(
            f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/{organization_id}/workspaces/{id}"
        )
        if response.status_code == http.HTTPStatus.NOT_FOUND:
            return None
        assert response.status_code == http.HTTPStatus.OK, (
            f"Got: {response.status_code} , expected: {http.HTTPStatus.OK}"
        )
        workspace_returned = json.loads(response.content)
        return cls.from_json(workspace_returned)

    @classmethod
    def find(cls, organization_id, request: FindWorkspaceRequest) -> ListWorkspacesResponse:
        base_url = f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/{organization_id}/workspaces"
        query_params = request.to_json()
        req = requests.models.PreparedRequest()
        req.prepare_url(base_url, query_params)
        response = requests.get(req.url)

        assert response.status_code == http.HTTPStatus.OK

        response_json = json.loads(response.content)
        return ListWorkspacesResponse.from_json(response_json)

    def update(self, headers: dict = None):
        response = requests.put(
            f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/{self.organization_id}/workspaces/{self.id}",
            json=self.to_json(),
            headers=headers,
        )
        assert response.status_code == http.HTTPStatus.OK, (
            f"Got: {response.status_code} , expected: {http.HTTPStatus.OK}"
        )
        workspace_returned = json.loads(response.content)
        return Workspace.from_json(workspace_returned)
