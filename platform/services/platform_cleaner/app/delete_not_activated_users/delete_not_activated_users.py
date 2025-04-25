"""Module for deleting not activated user"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os
from datetime import datetime

from geti_logger_tools.logger_config import initialize_logger
from grpc_interfaces.account_service.client import AccountServiceClient
from grpc_interfaces.account_service.enums import OrganizationStatus, UserStatus
from grpc_interfaces.account_service.pb.organization_status_pb2 import OrganizationStatusRequest
from grpc_interfaces.account_service.pb.user_pb2 import FindUserRequest, UserIdRequest
from grpc_interfaces.account_service.pb.user_status_pb2 import UserStatusRequest

logger = initialize_logger(__name__)


def _days_difference_from_current_utc(timestamp_str: str) -> int:
    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ")
    current_time = datetime.utcnow()
    time_difference = current_time - timestamp
    return time_difference.days


class ActivatedUsers:
    """A class for managing activated users in the system."""

    def __init__(self):
        self.account_service_client = AccountServiceClient(metadata_getter=lambda: ())

    def _get_all_organizations(self):
        return self.account_service_client.get_all_organizations()

    def _get_registered_users(self, organization_id: str):
        find_user_request = FindUserRequest(organization_id=organization_id, status=UserStatus.REGISTERED)
        return self.account_service_client.get_organizations_users(find_user_request=find_user_request)

    def _get_activated_users(self, organization_id: str):
        find_user_request = FindUserRequest(organization_id=organization_id, status=UserStatus.ACTIVATED)
        return self.account_service_client.get_organizations_users(find_user_request=find_user_request)

    def _change_user_status(self, organization_id: str, user_id: str, status: str):
        user_status_request = UserStatusRequest(user_id=user_id, organization_id=organization_id, status=status)
        return self.account_service_client.change_user_status(user_status_request=user_status_request)

    def _change_organization_status(self, organization_id: str, status: str):
        organization_status_request = OrganizationStatusRequest(
            organization_id=organization_id, status=status, created_by="platform_cleaner"
        )
        return self.account_service_client.change_organization_status(organization_status_request)

    def _get_user_by_id(self, user_id: str, organization_id: str):
        user_request = UserIdRequest(user_id=user_id, organization_id=organization_id)
        return self.account_service_client.get_user_by_id(user_id_request=user_request)

    def delete_not_activated_users(self, days_until_deletion: int) -> None:
        """
        Deletes all non-activated users from all organizations if a user does not complete the registration
        within the number of days defined in the `days_until_deletion` variable.
        :param days_until_deletion: The number of days after which not activated users will be deleted.
        """
        try:
            organizations = self._get_all_organizations()
            logger.debug(f"{len(organizations)} organizations found. Organizations: {organizations}")
            for organization in organizations:
                registered_users = self._get_registered_users(organization_id=organization["id"])
                logger.debug(f"{len(registered_users)} registered users found. List of users: {registered_users}")

                activated_users = self._get_activated_users(organization_id=organization["id"])
                logger.debug(f"{len(activated_users)} activated users found. List of users: {activated_users}")

                platform_users_left = len(registered_users + activated_users)

                if registered_users:
                    for user in registered_users:
                        user_status = self._get_user_by_id(user["id"], user["organizationId"])
                        days_since_creation = _days_difference_from_current_utc(timestamp_str=user_status.createdAt)
                        if days_since_creation >= days_until_deletion:
                            self._change_user_status(
                                organization_id=organization["id"],
                                user_id=user["id"],
                                status=UserStatus.DELETED,
                            )
                            platform_users_left -= 1
                            logger.info("Deleted user %s in organization %s", user["id"], organization["id"])
                            logger.debug(f"Platform users left: {platform_users_left}")

                    if platform_users_left == 0:
                        logger.debug(
                            f"All platform users have been deleted. Deleting organization {organization['id']}"
                        )
                        self._change_organization_status(
                            organization_id=organization["id"], status=OrganizationStatus.DELETED
                        )
                        logger.info("Deleted organization %s", organization["id"])
        except Exception as e:
            logger.error("An error occurred during the deletion process: %s", str(e))


def delete_not_activated_users(days_until_deletion: int = 30) -> None:
    """
    Connects to AccountService and deletes inactive users after the number of days specified
    in the `days_until_deletion` variable.

    :param days_until_deletion: The number of days after which not activated users will be deleted.
    """
    active_users = ActivatedUsers()
    logger.info("Deleting not activated users process started.")
    active_users.delete_not_activated_users(days_until_deletion=days_until_deletion)


def main() -> None:
    """
    The main function of removing inactive users of the platform
    """
    try:
        not_activated_user_expiration_in_days = int(os.environ["NOT_ACTIVATED_USER_EXPIRATION_IN_DAYS"])
    except KeyError as err:
        raise OSError("Error: Missing required environment variable.") from err
    except ValueError as err:
        raise OSError("Error: Invalid value for environment variable.") from err

    delete_not_activated_users(days_until_deletion=not_activated_user_expiration_in_days)


if __name__ == "__main__":
    main()
