"""
Utils to validate inputs
"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import base64
import re

FORBIDDEN_STRINGS = ["../", "<--", "-->", "..\\"]
FORBIDDEN_WORDS = ["exec", "drop", "truncate", "cmd", "insert", "delete"]
MAX_INPUT_LENGTH = 200


def is_base64(encoded_string: str):  # noqa: ANN201
    """
    Check if string is in base64 format
    :param encoded_string: any string
    :return: True if input has valid base64 format
    """
    try:
        check = base64.b64encode(base64.b64decode(encoded_string)).decode()
        return check == encoded_string
    except:  # noqa: E722
        return False


def convert_from_base_64(message: str) -> str:
    """
    :param message: Coded string
    :return: Decoded
    """
    base64_bytes = message.encode("ascii")
    message_bytes = base64.b64decode(base64_bytes)
    return message_bytes.decode("ascii")


def validate_user_input(user_input: dict) -> None:  # noqa: C901
    """
    Generic anti-attack user input validation.
    Input is a dictionary with the following possible keys: (name, mail, password, user_id)
    """
    for key, _ in user_input.items():
        if user_input[key] is None:
            continue
        if key == "password":
            if is_base64(user_input[key]):
                user_input[key] = convert_from_base_64(user_input[key])
                if not 8 <= len(user_input[key]) <= MAX_INPUT_LENGTH:
                    raise ValueError(
                        f"Password must consist of 8 - {MAX_INPUT_LENGTH} characters,, at least one capital letter, "
                        "lower letter, digit or symbol"
                    )
            else:
                raise ValueError("Wrong password format")
        elif len(user_input[key]) > MAX_INPUT_LENGTH:
            raise ValueError("Input is too long")

        input_lower = user_input[key].lower()
        input_words = input_lower.split()
        for word in FORBIDDEN_WORDS:
            if word in input_words:
                raise ValueError("Not allowed string")
        for forbidden_string in FORBIDDEN_STRINGS:
            if forbidden_string in input_lower:
                raise ValueError("Not allowed string")


def validate_resource_id(resource_id: str | None) -> None:
    """
    Validates resource id format.
    """
    if resource_id:
        regex = re.compile(r"(^(([a-zA-Z0-9_][a-zA-Z0-9/_|-]{0,127})|\\*)$)")
        if not re.fullmatch(regex, resource_id):
            raise ValueError("Invalid resource id")
