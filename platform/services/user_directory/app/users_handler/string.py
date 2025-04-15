"""String manipulation utilities."""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import secrets
import string

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
    return "".join(secrets.choice(pool) for pool in [
        string.ascii_uppercase,
        string.ascii_lowercase,
        string.digits,
        "".join(_CHARSET_LETTERS_DIGITS for _ in range(length - 3))
    ])
