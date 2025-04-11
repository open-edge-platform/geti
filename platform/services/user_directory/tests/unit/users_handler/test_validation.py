# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

from users_handler.validation import MAX_INPUT_LENGTH, is_base64, validate_resource_id, validate_user_input


def test_validate_resource_id_invalid():
    invalid_resource_id = "fake-id-!@#$%"
    with pytest.raises(ValueError) as exc:
        validate_resource_id(invalid_resource_id)
    assert str(exc.value) == "Invalid resource id"


def test_validate_resource_id_valid():
    valid_resource_id = "fake-id123456789"
    validate_resource_id(valid_resource_id)


def test_is_base64_true():
    encoded_string = "YmFzZTY0LWVuY29kZWQgc3RyaW5n"
    result = is_base64(encoded_string)
    assert result


def test_is_base64_false():
    encoded_string = "NotBase64"
    result = is_base64(encoded_string)
    assert not result


def test_validate_user_input_ok():
    user_input = {"uid": "test@test.com", "password": "UXdlcjEyM0A="}
    validate_user_input(user_input)


def test_validate_user_input_short_password():
    user_input = {"uid": "test@test.com", "password": "c2hvcnQ="}
    with pytest.raises(ValueError) as exc:
        validate_user_input(user_input)
    assert (
        str(exc.value) == f"Password must consists of 8 - {MAX_INPUT_LENGTH} characters, at least one capital letter, "
        "lower letter, digit or symbol"
    )


def test_validate_user_input_wrong_password_format():
    user_input = {"uid": "test@test.com", "password": "Not_encoded_p@55word"}
    with pytest.raises(ValueError) as exc:
        validate_user_input(user_input)
    assert str(exc.value) == "Wrong password format"


def test_validate_user_input_too_long():
    user_input = {
        "uid": "test@test.com",
        "password": "UXdlcjEyM0A=",
        "name": "input_is_too_long_123456789!@#$%^&*_input_is_too_long_123456789!@#$%^&*_input_is_too_long_123456789"
        "!@#$%^&*_input_is_too_long_123456789!@#$%^&*_input_is_too_long_123456789!@#$%^&*_input_is_too_long_"
        "123456789!@#$%^&*",
    }
    with pytest.raises(ValueError) as exc:
        validate_user_input(user_input)
    assert str(exc.value) == "Input is too long"


def test_validate_user_input_forbidden_str():
    user_input = {"uid": "test@test.com", "password": "UXdlcjEyM0A=", "name": "../forbidden-string"}
    with pytest.raises(ValueError) as exc:
        validate_user_input(user_input)
    assert str(exc.value) == "Not allowed string"


def test_validate_user_input_forbidden_word():
    user_input = {"uid": "test@test.com", "password": "UXdlcjEyM0A=", "name": "DROP TABLE USERS"}
    with pytest.raises(ValueError) as exc:
        validate_user_input(user_input)
    assert str(exc.value) == "Not allowed string"
