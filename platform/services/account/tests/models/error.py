# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from models.meta import CamelJsonizable


class AccountServiceErrorResponse(CamelJsonizable):
    def __init__(self, code, message, details):
        self.code = code
        self.message = message
        self.details = details


class AccountServiceError(Exception):
    def __init__(self, error_response: AccountServiceErrorResponse, http_status_code: int):
        self.error = error_response
        self.message = error_response.message
        self.status_code = http_status_code
        super().__init__(self.message)

    @classmethod
    def from_json_response(cls, json_response: dict, http_status_code: int):
        return cls(AccountServiceErrorResponse.from_json(json_response), http_status_code)
