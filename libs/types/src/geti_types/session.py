import logging
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from enum import Enum
from typing import cast

from geti_types import ID

DEFAULT_ORGANIZATION_ID = ID("000000000000000000000001")
DEFAULT_WORKSPACE_ID = ID("63B183D00000000000000001")
EXTRA = "extra"


class RequestSource(str, Enum):
    """
    Source of the request

    UNKNOWN: the origin of the request is unknown.
    BROWSER: the request originates from a browser (auth header)
    API_KEY: the request was sent with an API key (e.g. Geti SDK)
    INTERNAL: the source cannot be identified in a specific request from outside (user),
         but it is rather an internal system event (e.g. a job)
    """

    UNKNOWN = "unknown"
    BROWSER = "browser"
    API_KEY = "api_key"
    INTERNAL = "internal"


@dataclass
class Session:
    """
    Session context associated with incoming requests from a user.

    :var organization_id: Identifier of the organization associated with the user
    :var workspace_id: Identifier of the workspace
    :var source: Origin of the request
    :var extra: Additional information that to optionally embed in the session, as key-value pairs.
        This unstructured field can be used to carry arbitrary use case-specific info together with the session.
    """

    organization_id: ID
    workspace_id: ID
    source: RequestSource = RequestSource.UNKNOWN
    extra: dict[str, str] = field(default_factory=dict)

    def as_tuple(self) -> tuple[tuple[str, str], ...]:
        """
        Method to provide a Session as a Tuple representation

        :return: The session as a tuple, mapping the variables to its value in a (key, value) pair
        """
        extra_tuples = tuple((f"{EXTRA}.{extra_key}", extra_value) for extra_key, extra_value in self.extra.items())
        return (
            ("organization_id", str(self.organization_id)),
            ("workspace_id", str(self.workspace_id)),
            ("source", self.source.value),
            *extra_tuples,
        )

    def as_json(self) -> dict[str, str | dict[str, str]]:
        extra_dict = {EXTRA: self.extra} if self.extra else {}  # serialize extras only if non-empty
        return {
            "organization_id": str(self.organization_id),
            "workspace_id": str(self.workspace_id),
            "source": self.source.value,
            **extra_dict,
        }

    @staticmethod
    def from_json(session_dict: dict[str, str | dict[str, str]]) -> "Session":
        try:
            source = RequestSource[cast("str", session_dict.get("source", "unknown")).upper()]
        except KeyError:
            source = RequestSource.UNKNOWN
        extra = cast("dict[str, str]", session_dict.get(EXTRA, {}))
        return Session(
            organization_id=ID(cast("str", session_dict["organization_id"])),
            workspace_id=ID(cast("str", session_dict["workspace_id"])),
            source=source,
            extra=extra,
        )

    def as_list_bytes(self) -> list:
        """
        Method to provide a Session as a List of tuples representation

        :return: The session as a List, mapping the variables to its value (in bytes) in a (key, value) pair
        """
        extra_bytes = tuple(
            (f"{EXTRA}.{extra_key}", extra_value.encode()) for extra_key, extra_value in self.extra.items()
        )
        return [
            ("organization_id", str(self.organization_id).encode()),
            ("workspace_id", str(self.workspace_id).encode()),
            ("source", self.source.value.encode()),
            *extra_bytes,
        ]

    @property
    def source_str(self) -> str:
        return self.source.value


def make_session(
    organization_id: ID = DEFAULT_ORGANIZATION_ID,
    workspace_id: ID | None = DEFAULT_WORKSPACE_ID,
    source: RequestSource = RequestSource.UNKNOWN,
    extra: dict[str, str] | None = None,
) -> Session:
    """
    Create a Session object.

    :param organization_id: ID of the organization
    :param workspace_id: ID of the workspace
    :param source: Origin of the request (browser vs SDK)
    :param extra: Additional information that to optionally embed in the session, as key-value pairs.
        This unstructured field can be used to carry arbitrary use case-specific info together with the session.

    :return: Session object
    """
    return Session(
        organization_id=organization_id,
        workspace_id=workspace_id if workspace_id is not None else DEFAULT_WORKSPACE_ID,
        source=source,
        extra=extra if extra else {},
    )


CTX_SESSION_VAR: ContextVar[Session] = ContextVar("ctx_session_var")


@contextmanager
def session_context(session: Session):  # noqa: ANN201
    """
    Allows to use a session together with "with statement" context managers.
    On context entering initializes a context variable with a session and resets it on exit.
    :param session: Session object
    """
    token = CTX_SESSION_VAR.set(session)
    try:
        yield session
    finally:
        CTX_SESSION_VAR.reset(token)


def add_extra_to_current_session(key: str, value: str) -> None:
    """
    Insert a (key,value) pair into the current session 'extra'.

    :param key: The key to add
    :param value: The value to add
    """
    try:
        session = CTX_SESSION_VAR.get()
    except LookupError:
        raise RuntimeError("Cannot embed extra into session before it is initialized")
    session.extra[key] = value
    CTX_SESSION_VAR.set(session)


SESSION_LOGGING_FORMAT_HEADER = "[organization_id=%(organization_id)s workspace_id=%(workspace_id)s]"


def enhance_log_records_with_session_info() -> None:
    """Embed session information (organization_id, workspace_id) into the log records"""
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        try:
            session = CTX_SESSION_VAR.get()
            organization_id = session.organization_id
            workspace_id = session.workspace_id
        except LookupError:
            # Some system components that execute independently from requests may run without a session
            organization_id = workspace_id = "N/A"
        record.organization_id = organization_id
        record.workspace_id = workspace_id
        return record

    logging.setLogRecordFactory(record_factory)
