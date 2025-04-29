from uuid import UUID

from bson import ObjectId

from geti_types import ID


class TestID:
    def test_id(self) -> None:
        oid = ObjectId()
        uuid = UUID("12345678123456781234567812345678")
        str_id = "foo"

        id_empty = ID()
        id_oid = ID(oid)
        id_uuid = ID(uuid)
        id_str = ID(str_id)

        assert str(id_empty) == ""
        assert str(id_oid) == str(oid)
        assert str(id_uuid) == str(uuid)
        assert str(id_str) == str(str_id)
