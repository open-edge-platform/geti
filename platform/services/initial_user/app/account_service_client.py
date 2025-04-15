# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from geti_logger_tools.logger_config import initialize_logger
from grpc import RpcError
from grpc_interfaces.account_service.client import AccountServiceClient
from grpc_interfaces.account_service.pb.user_common_pb2 import UserData
from postgresql_client import PostgreSQLConnection
from users_handler_client import UsersHandlerConnection

from users_handler.exceptions import UserHandlerError

from common import base64_encode, get_sub_from_jwt_token

logger = initialize_logger(__name__)


class AccountServiceConnection:
    """
    Provides gRPC connection to Account Service.
    """

    def __init__(self) -> None:
        self.client = AccountServiceClient(metadata_getter=lambda: ())

    def handle_rpcerror(self, rpc_err: RpcError, email: str) -> None:
        if "StatusCode.ALREADY_EXISTS" in str(rpc_err):
            logger.warning(rpc_err)
            logger.warning(f"User with email {email} already exists. Skipping...")
        elif "StatusCode.INVALID_ARGUMENT" in str(rpc_err):
            logger.warning(rpc_err)
            logger.warning(f"User with email {email} is not accepted or invalid. Skipping...")
        else:
            raise rpc_err

    def migrate_accounts(
        self, uh_connection: UsersHandlerConnection, postgresql_connection: PostgreSQLConnection, organization_id: str
    ) -> None:
        users = uh_connection.get_accounts_for_migration()
        for index, user in enumerate(users):
            is_org_admin = index == 0
            if user["mail"] is None:
                raise ValueError("Cannot update user because of missing email.")
            logger.debug(f"Migrating user {user}")
            find_response = self.client.user_stub.find(UserData(email=user["mail"]))
            logger.debug(f"Received response from Account Service when searching for user: {find_response}")
            if find_response.total_matched_count >= 1:  # Check if user already exists in accsvc before migration
                logger.info("User already exist in account service.")
                continue

            split_name = user["name"].split(" ") if user["name"] else ""  # split name if ldap name contains space
            if len(split_name) == 1:
                first_name = split_name[0]
                second_name = split_name[0]
            else:
                first_name = split_name[0]
                second_name = " ".join(split_name[1:])

            user_data = UserData(
                first_name=first_name,
                second_name=second_name,
                email=user["mail"],
                country="POL",
                status="ACT",
                organization_id=organization_id,
            )
            try:
                migrated_user: UserData = self.client.user_stub.create(user_data)
                migrated_user.external_id = get_sub_from_jwt_token(uid=user["mail"])  # type: ignore[arg-type]
                modify_response = self.client.user_stub.modify(migrated_user)
                logger.info(
                    f"Updated external_id to {migrated_user.external_id} for user with id: {modify_response.id}"
                )
                try:  # Update UID of the migrated user in LDAP
                    if not uh_connection.users_handler.edit_user(
                        user["uid"],
                        new_uid=migrated_user.id,  # type: ignore[call-arg]
                    ):
                        logger.warning(f"Failed to update id of user {user['uid']} in LDAP")
                except UserHandlerError:
                    logger.warning(f"Failed to update id of user {user['uid']} in LDAP")
                self.update_user_id_spicedb(
                    postgresql_connection=postgresql_connection, user_mail=user["mail"], user_uid=migrated_user.id
                )
                self.add_organization_role_for_user(
                    uh_connection=uh_connection,
                    user_id=migrated_user.id,
                    organization_id=organization_id,
                    is_admin=is_org_admin,
                )
            except RpcError as rpc_err:
                self.handle_rpcerror(rpc_err, user["mail"])

    @staticmethod
    def update_user_id_spicedb(
        postgresql_connection: PostgreSQLConnection, user_mail: str | None, user_uid: str
    ) -> None:
        if not user_mail:
            raise ValueError("Cannot update user because of missing email.")
        encoded_mail = base64_encode(data=user_mail)
        encoded_uid = base64_encode(data=user_uid)
        list_of_ids = postgresql_connection.get_userset_object_ids()
        if encoded_uid in list_of_ids:
            logger.info("User already updated.")
            return
        postgresql_connection.update_userset_object_id(uid=encoded_uid, mail=encoded_mail)
        logger.info("User updated.")

    @staticmethod
    def add_organization_role_for_user(
        uh_connection: UsersHandlerConnection,
        user_id: str,
        organization_id: str,
        is_admin: bool = False,
    ) -> None:
        if is_admin:  # CVS-130037
            role = {"role": "ADMIN", "resource_id": organization_id, "resource_type": "organization"}
        else:
            role = {"role": "CONTRIBUTOR", "resource_id": organization_id, "resource_type": "organization"}
        encoded_uid = base64_encode(data=user_id)
        uh_connection.update_roles_in_spicedb(user_id=encoded_uid, role=role)
        logger.info("Added organization role for user.")
