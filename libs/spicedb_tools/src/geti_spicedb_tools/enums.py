"""Module enums"""

from enum import Enum, IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


class UserRoles(IntEnum):
    """Available roles from v1.0.
    Still used in migration scripts"""

    ADMIN = 0


class SpiceDBResourceTypes(str, Enum):
    """Available resources for use in SpiceDB"""

    PROJECT = "project"
    WORKSPACE = "workspace"
    ORGANIZATION = "organization"
    SERVICE_ACCOUNT = "service_account"
    USER = "user"
    JOB = "job"


class AccessResourceTypes(str, Enum):
    """Available resources for SpiceDB relations"""

    PROJECT = SpiceDBResourceTypes.PROJECT.value
    WORKSPACE = SpiceDBResourceTypes.WORKSPACE.value
    ORGANIZATION = SpiceDBResourceTypes.ORGANIZATION.value


class RoleMutationOperations(str, Enum):
    """Represents mutation operations that can be performed on user roles."""

    CREATE = "CREATE"
    DELETE = "DELETE"
    TOUCH = "TOUCH"


class Permissions(str, Enum):
    VIEW_JOB = "view_job"
    CAN_MANAGE = "can_manage"
    CAN_CONTRIBUTE = "can_contribute"
    VIEW_PROJECT = "view_project"
    EDIT_PROJECT = "edit_project"
    DELETE_PROJECT = "delete_project"
    MANAGE_USER_ACCESS = "manage_user_access"
    VIEW_WORKSPACE = "view_workspace"
    VIEW_ALL_WORKSPACE_JOBS = "view_all_workspace_jobs"
    EDIT_WORKSPACE = "edit_workspace"
    DELETE_WORKSPACE = "delete_workspace"
    CREATE_NEW_PROJECT = "create_new_project"


class Relations(str, Enum):
    """Represents a relation between resources."""

    SERVICE_ACCOUNTS = "service_accounts"
    PROJECT_MANAGER = "project_manager"
    PROJECT_CONTRIBUTOR = "project_contributor"
    WORKSPACE_ADMIN = "workspace_admin"
    WORKSPACE_CONTRIBUTOR = "workspace_contributor"
    ORGANIZATION_ADMIN = "organization_admin"
    ORGANIZATION_CONTRIBUTOR = "organization_contributor"
    GLOBAL_ADMIN = "admin"
    PARENT_WORKSPACE = "parent_workspace"
    VIEW_JOB = "view_job"
    PARENT_ENTITY = "parent_entity"


class SpiceDBResourceUserRoles(str, Enum):
    """Available resources user roles for use in SpiceDB"""

    ADMIN = "admin"
    CONTRIBUTOR = "contributor"


class SpiceDBUserRoles(Enum):
    """Maps user role to SpiceDB relations, for a specific resource type.

    The resource type is considered to be a SpiceDB resource,
    e.g. "project" or "workspace".
    """

    PROJECT = {
        SpiceDBResourceUserRoles.ADMIN.value: Relations.PROJECT_MANAGER,
        SpiceDBResourceUserRoles.CONTRIBUTOR.value: Relations.PROJECT_CONTRIBUTOR,
    }
    WORKSPACE = {
        SpiceDBResourceUserRoles.ADMIN.value: Relations.WORKSPACE_ADMIN,
        SpiceDBResourceUserRoles.CONTRIBUTOR.value: Relations.WORKSPACE_CONTRIBUTOR,
    }
    ORGANIZATION = {
        SpiceDBResourceUserRoles.ADMIN.value: Relations.ORGANIZATION_ADMIN,
        SpiceDBResourceUserRoles.CONTRIBUTOR.value: Relations.ORGANIZATION_CONTRIBUTOR,
    }

    @classmethod
    def role_from_relation(cls, resource_type: str, relation: str) -> str:
        """
        Returns user role corresponding to the provided SpiceDB relation,
        for the specified resource type.
        """
        try:
            app_role_to_relation: Mapping[str, str] = cls[resource_type.upper()].value

            for app_role, spicedb_relation in app_role_to_relation.items():
                if spicedb_relation == relation:
                    return app_role

            raise ValueError(
                f"No user role match for relation {repr(relation)} and resource type {repr(resource_type)}"
            )

        except KeyError as err:
            raise KeyError(f"Unknown resource type: {repr(resource_type)}") from err
