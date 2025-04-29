# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

logger = logging.getLogger(__name__)


class Message:
    def __init__(self, msg: dict) -> None:
        self.subject = msg.get("subject", "")
        self.to = msg.get("to", "")
        self.from_address = msg.get("from_address", "")
        self.from_name = msg.get("from_name", "")
        self.content = msg.get("content", "")
        self.html_content = msg.get("html_content", "")

        self.validate()

    def __repr__(self) -> str:
        return self.as_dict().__str__()

    def __eq__(self, other: object):
        if not isinstance(other, Message):
            return False
        return self.as_dict() == other.as_dict()

    def as_dict(self) -> dict:
        return self.__dict__

    def validate(self):  # noqa: ANN201
        """
        Check if message looks valid.
        """
        all_ok = True

        for key in ["subject", "to", "from_address", "from_name"]:
            if not self.__getattribute__(key):
                all_ok = False
                logger.debug(f"Empty {key} in message {self=}")

        if not self.content + self.html_content:
            all_ok = False
            logger.debug(f"Empty content and html_content in message {self=}")

        if not all_ok:
            raise ValueError(f"Invalid data provided to Message: {self=}")
