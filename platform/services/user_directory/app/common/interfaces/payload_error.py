# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Common Interface to handle Errors"""


class ResponseException(Exception):
    """Common Exception class parse error codes into UI readable way"""

    def __init__(self, code, item=None, msg=None) -> None:  # noqa: ANN001
        super().__init__()
        self.error_code = code
        self.item = item
        self.msg = msg

    def __str__(self) -> str:
        return "::".join(filter(None, (self.error_code, self.item, self.msg)))
