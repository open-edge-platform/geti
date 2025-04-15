"""String manipulation utilities."""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import secrets
import string
import random

_CHARSET_LETTERS_DIGITS: str = string.ascii_letters + string.digits


def random_str(length: int) -> str:
    """
    Generates a random string consisting of letters and digits.

    Letters include both lowercase and uppercase characters.
    """
    return "".join(secrets.choice(_CHARSET_LETTERS_DIGITS) for _ in range(length))

def strong_password(length: int) -> str:
    """
    Generates a random string consisting of letters and digits ensuring that there is at least one of them.

    Letters include both lowercase and uppercase characters.
    """
    password = (
        random.choice(string.ascii_uppercase) +
        random.choice(string.ascii_lowercase) +
        random.choice(string.digits) +
        ''.join(secrets.choice(_CHARSET_LETTERS_DIGITS) for _ in range(length-3))
    )
    return password
