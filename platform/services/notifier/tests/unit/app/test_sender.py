# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from unittest.mock import MagicMock, patch

import pytest
from app.message import Message
from app.sender import create_email_message, is_valid_email, send_message

MESSAGE = Message(
    {
        "subject": "Hello World!",
        "to": "recipient@example.com",
        "from_address": "sender@example.com",
        "from_name": "John Doe",
        "html_content": "Welcome to the real world.",
    }
)

HOST = "mocked smtp host"
PORT = 1234
LOGIN = "mocked smtp login"
PASSWORD = "mocked smtp password"


@patch("app.sender.send")
async def test_send_message_start_tls(send_mock: MagicMock, mocker):
    mocker.patch("app.sender.SMTP_HOST", HOST)
    mocker.patch("app.sender.SMTP_PORT", PORT)
    mocker.patch("app.sender.SMTP_LOGIN", LOGIN)
    mocker.patch("app.sender.SMTP_PASSWORD", PASSWORD)
    mocker.patch("app.sender.USE_START_TLS", True)
    mocker.patch("app.sender.VERIFY_HTTPS", True)

    await send_message(MESSAGE)

    send_mock.assert_called_once()
    assert_send_args(send_mock=send_mock, start_tls=True, use_tls=False, validate_certs=True)


@patch("app.sender.send")
async def test_send_message_tls(send_mock: MagicMock, mocker):
    mocker.patch("app.sender.SMTP_HOST", HOST)
    mocker.patch("app.sender.SMTP_PORT", PORT)
    mocker.patch("app.sender.SMTP_LOGIN", LOGIN)
    mocker.patch("app.sender.SMTP_PASSWORD", PASSWORD)
    mocker.patch("app.sender.USE_START_TLS", False)
    mocker.patch("app.sender.VERIFY_HTTPS", False)

    await send_message(MESSAGE)

    send_mock.assert_called_once()
    assert_send_args(send_mock=send_mock, start_tls=False, use_tls=True, validate_certs=False)


def assert_send_args(send_mock: MagicMock, start_tls: bool, use_tls: bool, validate_certs: bool):
    send_kwargs = send_mock.call_args[1]

    sent_message = send_kwargs.get("message")
    assert isinstance(sent_message, MIMEMultipart)
    assert sent_message.get("to") == "recipient@example.com"
    assert sent_message.get("from") == "John Doe <sender@example.com>"
    assert sent_message.get("subject") == "Hello World!"

    assert send_kwargs.get("hostname") is HOST
    assert send_kwargs.get("port") is PORT
    assert send_kwargs.get("username") is LOGIN
    assert send_kwargs.get("password") is PASSWORD
    assert send_kwargs.get("start_tls") is start_tls
    assert send_kwargs.get("use_tls") is use_tls
    assert send_kwargs.get("validate_certs") is validate_certs


@pytest.mark.parametrize(
    "email_address, is_valid",
    (
        pytest.param("user@example.com", True, id="positive scenario"),
        pytest.param("example.com", False, id="negative scenario"),
    ),
)
def test_is_email_valid(email_address, is_valid):
    if is_valid:
        assert is_valid_email(email_address)
    else:
        with pytest.raises(ValueError):
            is_valid_email(email_address)


def test_create_email_message():
    msg = Message(
        msg={
            "subject": "Hello World!",
            "to": "address@example.com",
            "from_address": "address@example.com",
            "from_name": "John Doe",
            "content": "Welcome to the real world.",
            "html_content": "<h1>Welcome to the real world.</h1>",
        }
    )
    expected_result = MIMEMultipart()
    expected_result["From"] = f"{msg.from_name} <{msg.from_address}>"
    expected_result["Subject"] = msg.subject
    expected_result["To"] = msg.to
    expected_result.attach(MIMEText(msg.content, "plain", "utf-8"))
    expected_result.attach(MIMEText(msg.html_content, "html", "utf-8"))
    result = create_email_message(message=msg)

    assert result["From"] == expected_result["From"]
    assert result["Subject"] == expected_result["Subject"]
    assert result["To"] == expected_result["To"]
    assert str(result.get_payload()[0]) == str(expected_result.get_payload()[0])
    assert str(result.get_payload()[1]) == str(expected_result.get_payload()[1])


@pytest.mark.parametrize(
    "message",
    (
        pytest.param(
            {
                "subject": "Hello World!",
                "to": "address@example.com",
                "from_address": "example.com",
                "from_name": "John Doe",
                "html_content": "Welcome to the real world.",
            },
            id="Wrong 'from_address' email address",
        ),
        pytest.param(
            {
                "subject": "Hello World!",
                "to": "example.com",
                "from_address": "address@example.com",
                "from_name": "John Doe",
                "html_content": "Welcome to the real world.",
            },
            id="Wrong 'to' email address",
        ),
    ),
)
def test_create_email_message_invalid_email_address(message):
    msg = Message(msg=message)
    with pytest.raises(ValueError):
        create_email_message(message=msg)
