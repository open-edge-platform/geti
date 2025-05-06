# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from pydantic.main import BaseModel

from grpc_interfaces.account_service.pb.user_common_pb2 import UserData


class UserByIDResponse(BaseModel):
    id: str
    email: str
    status: str
    organizationId: str  # noqa: N815
    createdAt: str | None  # noqa: N815
    createdBy: str  # noqa: N815
    modifiedAt: str | None  # noqa: N815

    @classmethod
    def from_protobuf(cls, proto: UserData):
        return cls(
            id=proto.id,
            email=proto.email,
            status=proto.status,
            organizationId=proto.organization_id,
            createdAt=proto.created_at.ToJsonString() if str(proto.created_at) != "" else None,
            createdBy=proto.created_by,
            modifiedAt=proto.modified_at.ToJsonString() if str(proto.modified_at) != "" else None,
        )
