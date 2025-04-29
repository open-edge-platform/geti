from geti_types import ID
from geti_types.session import (
    CTX_SESSION_VAR,
    RequestSource,
    Session,
    add_extra_to_current_session,
    make_session,
    session_context,
)

session = make_session(
    organization_id=ID("000000000000000000000001"),
    workspace_id=ID("63B183D00000000000000001"),
    source=RequestSource.BROWSER,
    extra={"ex-key-1": "ex-value-1"},
)


class TestSession:
    def test_session_tuple(self) -> None:
        session_as_tuple = session.as_tuple()
        assert session_as_tuple == (
            ("organization_id", "000000000000000000000001"),
            ("workspace_id", "63b183d00000000000000001"),
            ("source", "browser"),
            ("extra.ex-key-1", "ex-value-1"),
        )

    def test_session_json(self) -> None:
        session_as_json = session.as_json()
        assert session_as_json == {
            "organization_id": "000000000000000000000001",
            "workspace_id": "63b183d00000000000000001",
            "source": "browser",
            "extra": {"ex-key-1": "ex-value-1"},
        }

        session_from_json = Session.from_json(session_as_json)
        assert session_from_json == session

        session_from_json = Session.from_json(session_as_json)
        assert session_from_json == session

    def test_session_bytes(self) -> None:
        session_as_byte = session.as_list_bytes()
        assert session_as_byte == [
            ("organization_id", b"000000000000000000000001"),
            ("workspace_id", b"63b183d00000000000000001"),
            ("source", b"browser"),
            ("extra.ex-key-1", b"ex-value-1"),
        ]

    def test_add_extra_to_current_session(self) -> None:
        with session_context(session):
            add_extra_to_current_session(key="ex-key-2", value="ex-value-2")
            assert CTX_SESSION_VAR.get().extra == {"ex-key-1": "ex-value-1", "ex-key-2": "ex-value-2"}
