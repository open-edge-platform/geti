# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import base64
import random
import string
import uuid


def gen_random_str(length=5) -> str:
    return "".join(random.choice(string.digits + string.ascii_letters) for _ in range(length))


def gen_random_b64() -> str:
    random_str = gen_random_str()
    random_str_encoded = random_str.encode()
    base64_bytes = base64.b64encode(random_str_encoded)
    base64_string = base64_bytes.decode()
    return base64_string


def gen_random_uuid() -> str:
    return str(uuid.uuid4())


def gen_random_email(length=15) -> str:
    fake_second_part_of_email_address = "@example.com"
    desired_len_of_first_part_of_email_address = length - len(fake_second_part_of_email_address)
    if desired_len_of_first_part_of_email_address <= 0:
        raise ValueError("first part of email address cannot be less than or equal to 0")
    return f"{gen_random_str(desired_len_of_first_part_of_email_address)}{fake_second_part_of_email_address}"
