# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from __future__ import annotations

import http
import json

import requests

from models.error import AccountServiceError
from models.meta import CamelJsonizable, Meta

from config.env import account_service_grpc_gateway_address, api_v1_prefix, protocol


class UserSettingsResponse(CamelJsonizable):
    def __init__(self, message):
        self.message = message


class UserSettingsCreateRequest(CamelJsonizable):
    def __init__(self, settings=None, project_id=None):
        self.settings = settings
        self.project_id = project_id


class UserSettings(Meta):
    def __init__(
        self,
        id=None,
        user_id=None,
        organization_id=None,
        project_id=None,
        settings=None,
        created_at=None,
        created_by=None,
        modified_at=None,
        modified_by=None,
    ):
        super().__init__(id, created_at, created_by, modified_at, modified_by)
        self.user_id = user_id
        self.organization_id = organization_id
        self.project_id = project_id
        self.settings = settings

    def create(self, headers: dict = None) -> UserSettingsResponse:
        url = f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/user_settings"
        payload = UserSettingsCreateRequest(settings=self.settings)
        if not self.project_id:
            response = requests.post(
                url,
                json=payload.to_json(),
                headers=headers,
            )
        else:
            req = requests.models.PreparedRequest()
            req.prepare_url(url, UserSettings(project_id=self.project_id).to_json())
            url = req.url
            response = requests.post(url, json=payload.to_json(), headers=headers)

        json_returned = json.loads(response.content)
        if response.status_code != http.HTTPStatus.OK:
            raise AccountServiceError.from_json_response(json_returned, response.status_code)

        return UserSettingsResponse.from_json(json_returned)

    @classmethod
    def get(cls, headers: dict = None, project_id: str = None) -> UserSettings | None:
        url = f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/user_settings"
        if not project_id:
            response = requests.get(url, headers=headers)
        else:
            req = requests.models.PreparedRequest()
            req.prepare_url(url, UserSettings(project_id=project_id).to_json())
            response = requests.get(req.url, headers=headers)

        if response.status_code == http.HTTPStatus.NO_CONTENT:
            return None

        json_returned = json.loads(response.content)
        if response.status_code != http.HTTPStatus.OK:
            raise AccountServiceError.from_json_response(json_returned, response.status_code)

        return cls.from_json(json_returned)
