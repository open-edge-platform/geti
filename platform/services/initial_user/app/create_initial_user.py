# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

import time

from geti_logger_tools.logger_config import initialize_logger
from geti_spicedb_tools import SpiceDB
from grpc import RpcError
from users_handler_client import UsersHandlerConnection

from account_service_client import AccountServiceConnection
from users_handler.exceptions import EmailAlreadyExists

from common import get_sub_from_jwt_token

logger = initialize_logger(__name__)


def main() -> None:
    """
    Main function that will:
        - create default organization and workspace
        - add initial user to account service and openldap
        - get 'sub' from manually created jwt token
        - update user's external_id in Account Service by 'sub' key.
    """
    acc_svc = AccountServiceConnection()
    for _ in range(15):
        try:
            organization_id = acc_svc.client.create_default_organization()
            workspace_id = acc_svc.client.create_default_workspace(organization_id=organization_id)
            break
        except RpcError as rpc_err:
            rpc_err_message = str(rpc_err)
            logger.warning(rpc_err)
            if "no healthy upstream" in rpc_err_message.lower() or "StatusCode.UNAVAILABLE" in rpc_err_message:
                time.sleep(60)
            else:
                raise rpc_err
    else:
        raise RuntimeError("Connection to account service has timed out - no healthy upstream.")
    uh_connection = UsersHandlerConnection()
    SpiceDB().link_organization_to_workspace_in_spicedb(workspace_id=workspace_id, organization_id=organization_id)
    user_id = acc_svc.client.create_initial_user(organization_id=organization_id)
    try:
        uh_connection.create_initial_user(uid=user_id, workspace_id=workspace_id, organization_id=organization_id)
    except EmailAlreadyExists:
        logger.info("User exists in ldap")
    sub = get_sub_from_jwt_token(uid=user_id)
    acc_svc.client.update_user_external_id(uid=user_id, organization_id=organization_id, external_id=sub)


if __name__ == "__main__":
    main()
