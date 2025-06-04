# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.
"""
A module containing helper methods used in password handling
"""

import base64
import os
import random
import secrets
import string
from binascii import b2a_base64

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ALLOWED_SPECIAL_CHARACTERS = "()*+,-.:;<=>[]^_"


def generate_password() -> str:
    """
    Generate password. Security guide: 10 characters minimum, at least one capital letter,
    at least one numeral, and at least one special character
    """
    lower = random.sample(string.ascii_lowercase, 4)
    upper = random.sample(string.ascii_uppercase, 4)
    numeral = random.sample(string.digits, 4)
    symbols = random.sample(ALLOWED_SPECIAL_CHARACTERS, 4)
    password = [*lower, *upper, *numeral, *symbols]
    random.shuffle(password)
    return "".join(password)


def ab64_encode(data: bytes) -> str:
    """
    Calculate adjusted base64 of a string
    """
    return b2a_base64(data).decode("ascii").rstrip("=\n").replace("+", ".")


def hash_ldap_password(password: str) -> str:
    """
    Hash the password as it does OpenLDAP so to be able to pass only the digest.
    """
    salt = secrets.token_bytes(16)
    iterations = 25000
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA512(),
        length=64,
        salt=salt,
        iterations=iterations,
    )
    key = kdf.derive(password.encode("ascii"))
    return "{}{}${}${}".format("{PBKDF2-SHA512}", iterations, ab64_encode(salt), ab64_encode(key))


def generate_cookie_secret(secret_length: int = 32) -> str:
    """
    Generate a random authorization cookie secret.
    :param secret_length: length of the secret
    :return: cookie secret in base64
    """
    return base64.urlsafe_b64encode(os.urandom(secret_length)).decode()
