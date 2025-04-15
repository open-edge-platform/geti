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

import time

from geti_logger_tools.logger_config import initialize_logger
from geti_spicedb_tools import SpiceDB
from grpc import RpcError
from postgresql_client import PostgreSQLConnection
from users_handler_client import UsersHandlerConnection

from account_service_client import AccountServiceConnection

logger = initialize_logger(__name__)


def main() -> None:
    """
    Main function that will:
        - create default organization and workspace
        - migrate existing ldap users to newly created account service
        - replace user id in spicedb with new id from account service
        - update workspace id in spicedb
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

    uh_connection = UsersHandlerConnection()  # has to be initiated for link_organization_to_workspace_in_spicedb
    SpiceDB().link_organization_to_workspace_in_spicedb(workspace_id=workspace_id, organization_id=organization_id)
    psql_connection = PostgreSQLConnection()
    try:  # https://www.psycopg.org/docs/usage.html#with-statement
        acc_svc.migrate_accounts(
            uh_connection=uh_connection, postgresql_connection=psql_connection, organization_id=organization_id
        )
        psql_connection.update_workspace_object_id(workspace_id=workspace_id)
    finally:
        psql_connection.close()


if __name__ == "__main__":
    main()
