# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

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
