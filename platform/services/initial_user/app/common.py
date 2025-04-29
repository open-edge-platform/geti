# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import base64
from binascii import a2b_base64

from users_handler.subject_pb2 import IDTokenSubject


def get_sub_from_jwt_token(uid: str) -> str:
    """
    Generate the JWT subject string (sub) based on a given user ID (uid).

    :param uid: The user ID used to construct the IDTokenSubject object.

    :return: A base64 encoded serialized JWT subject string.
    """
    id_token_subject = IDTokenSubject()
    id_token_subject.user_id = f"cn={uid},dc=example,dc=org"
    id_token_subject.conn_id = "regular_users"

    sub: str = base64.b64encode(id_token_subject.SerializeToString()).decode(encoding="utf8").rstrip("=")
    return sub


def base64_encode(data: str) -> str:
    """Encode data as base64 with padding removed"""
    return base64.encodebytes(data.encode("utf-8")).decode("utf-8").replace("=", "").replace("\n", "")


def ab64_decode(data: str) -> str:
    """Decode data as base64 with padding removed"""
    data = data.replace(".", "+")
    return a2b_base64(data + "=" * (-len(data) % 4)).decode("utf-8")
