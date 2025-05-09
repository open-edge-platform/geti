# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements various methods to propagate a session
"""

import logging
from collections.abc import Iterable
from functools import wraps
from typing import Any

from geti_types import CTX_SESSION_VAR, Session

logger = logging.getLogger(__name__)


def setup_session_grpc(fn) -> Any:  # noqa: ANN001
    """
    Decorator to make a Session for gRPC communications, and store it in CTX_SESSION_VAR
    """
    from grpc import ServicerContext

    @wraps(fn)
    def wrapper(*args, **kwargs):
        for arg in args:
            if isinstance(arg, ServicerContext):
                session_dict = {}
                for item in arg.invocation_metadata():
                    if (
                        isinstance(item, tuple)
                        and len(item) > 1
                        and isinstance(item[0], str)
                        and isinstance(item[1], str)
                    ):
                        if item[0].startswith("extra."):  # 'extra' should be converted from dot notation to nested json
                            if "extra" not in session_dict:
                                session_dict["extra"] = {}
                            session_dict["extra"][item[0].removeprefix("extra.")] = item[1]
                        else:
                            session_dict[item[0]] = item[1]
                session = Session.from_json(session_dict)
                CTX_SESSION_VAR.set(session)
                break
        else:
            logger.error("Could not locate the 'context' argument in the gRPC method call")
        return fn(*args, **kwargs)

    return wrapper


def setup_session_kafka(fn) -> Any:  # noqa: ANN001
    """
    Decorator to make a Session for Kafka communications, and store it in CTX_SESSION_VAR
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        for arg in args:
            try:
                headers = arg.headers
            except AttributeError:
                continue
            if not isinstance(headers, Iterable):
                continue

            session_dict = {}
            for item in headers:
                if (
                    isinstance(item, tuple)
                    and len(item) > 1
                    and isinstance(item[0], str)
                    and isinstance(item[1], bytes)
                ):
                    if item[0].startswith("extra."):  # 'extra' should be converted from dot notation to nested json
                        if "extra" not in session_dict:
                            session_dict["extra"] = {}
                        session_dict["extra"][item[0].removeprefix("extra.")] = item[1].decode("utf-8")
                    else:
                        session_dict[item[0]] = item[1].decode("utf-8")
            session = Session.from_json(session_dict)
            CTX_SESSION_VAR.set(session)
            break
        else:
            logger.error("Could not locate the ConsumerRecord argument in the Kafka handler method call")
        return fn(*args, **kwargs)

    return wrapper
