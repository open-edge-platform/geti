# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from app.message import Message

VALID_MESSAGE = {
    "subject": "Hello World!",
    "to": "recipient@example.com",
    "from_address": "sender@example.com",
    "from_name": "John Doe",
    "html_content": "Welcome to the real world.",
}


def test_valid_message():
    message = Message(VALID_MESSAGE)

    assert "Hello World!" == message.subject
    assert "recipient@example.com" == message.to
    assert "sender@example.com" == message.from_address
    assert "John Doe" == message.from_name
    assert "Welcome to the real world." == message.html_content


def test_invalid_message():
    for key in VALID_MESSAGE.keys():
        invalid_message = dict(VALID_MESSAGE)
        del invalid_message[key]

        with pytest.raises(ValueError) as err_info:
            Message(invalid_message)

        assert key in err_info.__str__()
