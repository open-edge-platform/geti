import abc
import base64
import functools
import json
import logging
import os
import threading
import time
from collections.abc import Callable
from os import environ
from typing import Any

import authzed.api.v1 as authzed
from authzed.api.v1 import (
    CheckPermissionRequest,
    Client,
    Consistency,
    DeleteRelationshipsRequest,
    DeleteRelationshipsResponse,
    LookupResourcesRequest,
    ObjectReference,
    ReadRelationshipsRequest,
    ReadRelationshipsResponse,
    RelationshipFilter,
    SubjectFilter,
    SubjectReference,
    WriteRelationshipsResponse,
    ZedToken,
)
from grpc import (  # type: ignore # grpc types are not available in mypy
    RpcError,
    StatusCode,
    access_token_call_credentials,
    composite_channel_credentials,
    ssl_channel_credentials,
)
from grpcutil import insecure_bearer_token_credentials

from geti_spicedb_tools import Permissions, Relations, RoleMutationOperations, SpiceDBResourceTypes, SpiceDBUserRoles

logger = logging.getLogger(__name__)


class Singleton(abc.ABCMeta):
    """
    Metaclass to create singleton classes.
    """

    def __new__(cls, clsname, bases, dct):  # noqa: ANN001
        def __deepcopy__(self, memo_dict=None):  # noqa: ANN001
            # Since the classes are singleton per-project, we can return the same object.
            if memo_dict is None:
                memo_dict = {}
            memo_dict[id(self)] = self
            return self

        def __copy__(self):  # noqa: ANN001
            # Since the classes are singleton per-project, we can return the same object.
            return self

        newclass = super().__new__(cls, clsname, bases, dct)
        setattr(newclass, __deepcopy__.__name__, __deepcopy__)
        setattr(newclass, __copy__.__name__, __copy__)
        return newclass

    def __init__(cls, clsname, bases, dct) -> None:  # noqa: ANN001
        super().__init__(clsname, bases, dct)
        cls._lock = threading.Lock()
        cls._instance: Singleton | None = None

    def __call__(cls, *args, **kwargs) -> Any:
        if cls._instance is None:  # double-checked locking
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


def retry_grpc_call_on_unavailable_response(
    func: Callable,
    retries: int = 2,
    initial_delay: float = 0.5,
    backoff_multiplier: int = 2,
) -> Callable:
    """
    Simple decorator for gRPC call retry with exponential backoff when UNAVAILABLE status code is received.
    In theory, most retries should be performed in the background by gRPC channel according
    to retry policy, but in practice these automatic retries may not be triggered in some corner cases (e.g. GOAWAY
    response returned due to max connection age or connection count being exceeded).
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        delay = initial_delay
        for _ in range(retries):
            try:
                return func(*args, **kwargs)
            except RpcError as rpc_error:
                logger.info(f"Received {rpc_error}, retrying call in {delay} seconds")
                if rpc_error.code() == StatusCode.UNAVAILABLE:
                    time.sleep(delay)
                    delay *= backoff_multiplier
                    continue
                raise
        raise RuntimeError(f"gRPC call {func}({args}, {kwargs}) failed after {retries} retries.")

    return wrapper


class SpiceDB(metaclass=Singleton):
    """
    SpiceDB client wrapper for high level interactions with DB
    """

    def __init__(self) -> None:
        spicedb_address = environ.get("SPICEDB_ADDRESS", "localhost:50051")
        spicedb_token = environ.get("SPICEDB_TOKEN", "")
        spicedb_credentials = environ.get("SPICEDB_CREDENTIALS", "token")
        spicedb_ssl_certificates_dir = environ.get("SPICEDB_SSL_CERTIFICATES_DIR", "")

        credentials = self._get_credentials(spicedb_credentials, spicedb_token, spicedb_ssl_certificates_dir)
        grpc_channel_config: str = json.dumps(
            {
                "methodConfig": [
                    {
                        "name": [{"service": "authzed.api.v1.PermissionsService"}],
                        "retryPolicy": {
                            "maxAttempts": 5,
                            "initialBackoff": "1s",
                            "maxBackoff": "3s",
                            "backoffMultiplier": 2,
                            "retryableStatusCodes": [
                                "UNAVAILABLE",
                                "INTERNAL",
                                "UNKNOWN",
                            ],
                        },
                    }
                ]
            }
        )
        self._client = Client(
            spicedb_address,
            credentials,
            options=[("grpc.service_config", grpc_channel_config)],
        )

    def _get_credentials(self, spicedb_credentials: str, spicedb_token: str, certificates_dir: str) -> Any:
        if spicedb_credentials == "token_and_ca":
            return composite_channel_credentials(
                self._get_root_certificate_credentials(certificates_dir),
                access_token_call_credentials(spicedb_token),
            )
        if spicedb_credentials == "token_and_ssl":
            return composite_channel_credentials(
                self._get_ssl_channel_credentials(certificates_dir),
                access_token_call_credentials(spicedb_token),
            )
        return insecure_bearer_token_credentials(spicedb_token)

    def _get_root_certificate_credentials(self, certificates_dir: str) -> Any:
        with open(os.path.join(certificates_dir, "ca.crt"), mode="rb") as ca_file:
            ca = ca_file.read()
            return ssl_channel_credentials(root_certificates=ca)

    def _get_ssl_channel_credentials(self, certificates_dir: str) -> Any:
        with open(os.path.join(certificates_dir, "ca.crt"), mode="rb") as ca_file:
            ca = ca_file.read()
        with open(os.path.join(certificates_dir, "tls.key"), mode="rb") as key_file:
            key = key_file.read()
        with open(os.path.join(certificates_dir, "tls.crt"), mode="rb") as cert_file:
            cert = cert_file.read()
            return ssl_channel_credentials(root_certificates=ca, private_key=key, certificate_chain=cert)

    @retry_grpc_call_on_unavailable_response
    def _lookup_resources(self, resource_object_type: str, permission: str, subject: SubjectReference):
        return self._client.LookupResources(
            LookupResourcesRequest(
                resource_object_type=resource_object_type,
                permission=permission,
                subject=subject,
                consistency=Consistency(fully_consistent=True),
            )
        )

    def get_user_workspaces(self, user_id: str, permission: Permissions) -> tuple[str, ...]:
        """
        Gets user workspaces list available with certain permission

        :param user_id: User ID
        :param permission: permission to check (i.e. can_manage, can_contribute)
        :return list of workspaces
        """
        resp = self._lookup_resources(
            SpiceDBResourceTypes.WORKSPACE.value,
            permission.value,
            SubjectReference(
                object=ObjectReference(
                    object_type=SpiceDBResourceTypes.USER.value, object_id=SpiceDB.convert_user_id(user_id)
                )
            ),
        )
        return tuple(str(r.resource_object_id) for r in resp)

    def get_user_jobs(self, user_id: str, permission: Permissions) -> tuple[str, ...]:
        """
        Gets user jobs list available with certain permission

        :param user_id: User ID
        :param permission: permission to check (i.e. view_job)
        :return list of jobs
        """
        resp = self._lookup_resources(
            SpiceDBResourceTypes.JOB.value,
            permission.value,
            SubjectReference(
                object=ObjectReference(
                    object_type=SpiceDBResourceTypes.USER.value, object_id=SpiceDB.convert_user_id(user_id)
                )
            ),
        )
        return tuple(str(r.resource_object_id) for r in resp)

    def get_user_projects(self, user_id: str, permission: Permissions) -> tuple[str, ...]:
        """
        Gets user projects list available with certain permission

        :param user_id: User ID
        :param permission: permission to check (i.e. can_manage, can_contribute)
        :return list of projects
        """
        resp = self._lookup_resources(
            SpiceDBResourceTypes.PROJECT.value,
            permission.value,
            SubjectReference(
                object=ObjectReference(
                    object_type=SpiceDBResourceTypes.USER.value, object_id=SpiceDB.convert_user_id(user_id)
                )
            ),
        )
        if not resp:
            raise Exception
        return tuple(str(r.resource_object_id) for r in resp if r.resource_object_id)

    @retry_grpc_call_on_unavailable_response
    def get_user_roles(self, resource_type: str, user_id: str, resource_id: str | None = None) -> list[tuple[str, str]]:
        logger.info(f"Getting user {user_id} roles on {resource_type}/{resource_id if resource_id is not None else ''}")
        if resource_id:
            relationship_filter = RelationshipFilter(
                resource_type=resource_type,
                optional_resource_id=resource_id,
                optional_subject_filter=authzed.SubjectFilter(
                    subject_type=SpiceDBResourceTypes.USER.value, optional_subject_id=user_id
                ),
            )
        else:
            relationship_filter = RelationshipFilter(
                resource_type=resource_type,
                optional_subject_filter=authzed.SubjectFilter(
                    subject_type=SpiceDBResourceTypes.USER.value, optional_subject_id=user_id
                ),
            )
        resp: ReadRelationshipsResponse = self._client.ReadRelationships(
            ReadRelationshipsRequest(
                consistency=authzed.Consistency(fully_consistent=True),
                relationship_filter=relationship_filter,
            )
        )

        user_roles = []
        for item in list(resp):
            logger.debug(f"Response relation: {item.relationship.relation}")
            user_roles.append(
                (
                    item.relationship.resource.object_id,
                    SpiceDBUserRoles.role_from_relation(resource_type, item.relationship.relation),
                )
            )
        return user_roles

    @retry_grpc_call_on_unavailable_response
    def _check_permission(self, resource: ObjectReference, subject: SubjectReference, permission: str):
        return self._client.CheckPermission(
            CheckPermissionRequest(
                resource=resource,
                permission=permission,
                subject=subject,
                consistency=Consistency(fully_consistent=True),
            )
        )

    @retry_grpc_call_on_unavailable_response
    def check_permission(
        self,
        subject_type: str,
        subject_id: str,
        resource_type: str,
        resource_id: str,
        permission: str,
    ) -> bool:
        """
        Check permission on given resource_type/resource_id for subject_type/subject_id.
        Returns True if User has the permission, returns False otherwise.
        """
        logger.info(f"Checking {subject_type}/{subject_id} {permission} permission on {resource_type}/{resource_id}")
        if subject_type == SpiceDBResourceTypes.USER.value:
            subject_id = self.convert_user_id(subject_id)

        subject = authzed.SubjectReference(
            object=authzed.ObjectReference(
                object_type=subject_type,
                object_id=subject_id,
            )
        )

        resource = authzed.ObjectReference(object_type=resource_type, object_id=resource_id)

        resp = self._client.CheckPermission(
            authzed.CheckPermissionRequest(
                consistency=authzed.Consistency(fully_consistent=True),
                resource=resource,
                permission=permission,
                subject=subject,
            ),
        )
        return resp.permissionship == authzed.CheckPermissionResponse.PERMISSIONSHIP_HAS_PERMISSION

    def link_organization_to_workspace_in_spicedb(self, workspace_id: str, organization_id: str) -> None:
        """
        Connect given organization to workspace with parent_organization relation.
        """
        self.write_relationship(
            resource=authzed.ObjectReference(object_type="workspace", object_id=workspace_id),
            subject=authzed.SubjectReference(
                object=authzed.ObjectReference(
                    object_type="organization",
                    object_id=organization_id,
                )
            ),
            relation="parent_organization",  # type: ignore
            operation=authzed.RelationshipUpdate.Operation.OPERATION_TOUCH,
        )

    @retry_grpc_call_on_unavailable_response
    def write_relationship(
        self,
        relation: Relations,
        subject: authzed.SubjectReference,
        resource: authzed.ObjectReference,
        operation: authzed.RelationshipUpdate.Operation,
    ) -> WriteRelationshipsResponse:
        """
        Write relationship into spice db
        """
        logger.debug(f"Creating {relation} relationship for {subject} in {resource}.")
        resp: authzed.WriteRelationshipsResponse = self._client.WriteRelationships(
            authzed.WriteRelationshipsRequest(
                updates=[
                    authzed.RelationshipUpdate(
                        operation=operation,
                        relationship=authzed.Relationship(
                            resource=resource,
                            relation=relation,
                            subject=subject,
                        ),
                    ),
                ]
            )
        )
        logger.debug(f"WriteRelationship response: {resp}")
        return resp

    def change_user_relation(
        self,
        resource_type: str,
        resource_id: str,
        relations: list[Relations],
        user_id: str,
        operation: RoleMutationOperations,
        object_type: str = "user",
    ) -> None:
        """
        Change relations for target user
        """
        if operation == RoleMutationOperations.CREATE:
            relation_operation = authzed.RelationshipUpdate.Operation.OPERATION_CREATE
        elif operation == RoleMutationOperations.DELETE:
            relation_operation = authzed.RelationshipUpdate.Operation.OPERATION_DELETE
        elif operation == RoleMutationOperations.TOUCH:
            relation_operation = authzed.RelationshipUpdate.Operation.OPERATION_TOUCH
        else:
            raise ValueError(f"Unknown operation: {repr(operation)}.")

        user_subject = authzed.SubjectReference(
            object=authzed.ObjectReference(object_type=object_type, object_id=user_id)
        )
        resource = authzed.ObjectReference(object_type=resource_type, object_id=resource_id)
        for relation in relations:
            self.write_relationship(relation, user_subject, resource, relation_operation)

    def add_workspace_user(self, workspace_id: str, user_id: str, relation: Relations) -> ZedToken:
        """
        Adds a workspace user with a certain role (relation)

        :param workspace_id: Workspace ID
        :param user_id: User ID
        :param relation: User relation (Admin, Contributor)
        :return ZedToken
        """
        return self.write_relationship(
            relation=relation.value,
            subject=SubjectReference(
                object=ObjectReference(
                    object_type=SpiceDBResourceTypes.USER.value,
                    object_id=SpiceDB.convert_user_id(user_id),
                )
            ),
            resource=ObjectReference(object_type=SpiceDBResourceTypes.WORKSPACE.value, object_id=workspace_id),
            operation=authzed.RelationshipUpdate.Operation.OPERATION_CREATE,
        ).written_at

    def add_project_user(self, project_id: str, user_id: str, relation: Relations) -> ZedToken:
        """
        Adds a project user with a certain role (relation)

        :param project_id: Project ID
        :param user_id: User ID
        :param relation: User relation (Manager, Contributor)
        :return ZedToken
        """
        return self.write_relationship(
            relation=relation.value,
            subject=SubjectReference(
                object=ObjectReference(
                    object_type=SpiceDBResourceTypes.USER.value,
                    object_id=SpiceDB.convert_user_id(user_id),
                )
            ),
            resource=ObjectReference(object_type=SpiceDBResourceTypes.PROJECT.value, object_id=project_id),
            operation=authzed.RelationshipUpdate.Operation.OPERATION_CREATE,
        ).written_at

    def add_project_space(self, project_id: str, workspace_id: str) -> ZedToken:
        """
        Adds a project user with a certain role (relation)

        :param project_id: Project ID
        :param workspace_id: User ID
        :return ZedToken
        """
        return self.write_relationship(
            relation=Relations.PARENT_WORKSPACE.value,
            subject=SubjectReference(
                object=ObjectReference(
                    object_type=SpiceDBResourceTypes.WORKSPACE.value,
                    object_id=workspace_id,
                )
            ),
            resource=ObjectReference(object_type=SpiceDBResourceTypes.PROJECT.value, object_id=project_id),
            operation=authzed.RelationshipUpdate.Operation.OPERATION_CREATE,
        ).written_at

    def create_workspace(self, workspace_id: str, creator: str) -> ZedToken:
        """
        Creates a workspace with an admin user

        :param workspace_id: Workspace ID
        :param creator: Creator user
        :return ZedToken
        """
        return self.add_workspace_user(workspace_id, creator, Relations.WORKSPACE_ADMIN)

    def create_project(self, workspace_id: str, project_id: str, creator: str) -> ZedToken:
        """
        Creates a project within a workspace with a manager user

        :param workspace_id: Workspace ID
        :param project_id: Project ID
        :param creator: Creator user
        :return ZedToken
        """
        self.write_relationship(
            relation=Relations.PARENT_WORKSPACE.value,
            subject=SubjectReference(
                object=ObjectReference(object_type=SpiceDBResourceTypes.WORKSPACE.value, object_id=workspace_id)
            ),
            resource=ObjectReference(object_type=SpiceDBResourceTypes.PROJECT.value, object_id=project_id),
            operation=authzed.RelationshipUpdate.Operation.OPERATION_CREATE,
        )
        return self.write_relationship(
            relation=Relations.PROJECT_MANAGER.value,
            subject=SubjectReference(
                object=ObjectReference(
                    object_type=SpiceDBResourceTypes.USER.value,
                    object_id=SpiceDB.convert_user_id(creator),
                )
            ),
            resource=ObjectReference(object_type=SpiceDBResourceTypes.PROJECT.value, object_id=project_id),
            operation=authzed.RelationshipUpdate.Operation.OPERATION_CREATE,
        ).written_at

    def create_job(self, job_id: str, parent_entity_type: str, parent_entity_id: str) -> ZedToken:
        """
        Creates a job

        :param job_id: Job ID
        :param parent_entity_type: parent entity type, either "workspace" or "project"
        :param parent_entity_id: parent entity ID
        :return ZedToken
        """
        return self.write_relationship(
            operation=authzed.RelationshipUpdate.Operation.OPERATION_CREATE,
            resource=ObjectReference(object_type=SpiceDBResourceTypes.JOB.value, object_id=job_id),
            relation=Relations.PARENT_ENTITY.value,
            subject=SubjectReference(
                object=ObjectReference(
                    object_type=parent_entity_type,
                    object_id=parent_entity_id,
                ),
            ),
        ).written_at

    @retry_grpc_call_on_unavailable_response
    def delete_relations(self, user_id: str, object_type: str) -> None:
        """
        Atomically bulk deletes all relationships matching the provided filter.
        If no relationships match, none will be deleted and the operation will succeed.
        """
        for resource_type in SpiceDBResourceTypes:
            logger.debug(f"Deleting relationship for {user_id}, {object_type} and {resource_type}.")
            resp: authzed.DeleteRelationshipsResponse = self._client.DeleteRelationships(
                authzed.DeleteRelationshipsRequest(
                    relationship_filter=authzed.RelationshipFilter(
                        resource_type=resource_type,
                        optional_subject_filter=authzed.SubjectFilter(
                            subject_type=object_type, optional_subject_id=user_id
                        ),
                    )
                )
            )
            logger.debug(f"DeleteRelationships response for the {resource_type}: {resp}")

    def delete_job(self, job_id: str) -> ZedToken:
        """
        Deletes a job

        :param job_id: Job ID
        :return ZedToken
        """
        return self.delete_relation(resource_object_type=SpiceDBResourceTypes.JOB.value, resource_id=job_id).deleted_at

    def delete_project(self, project_id: str) -> ZedToken:
        """
        Deletes project and removes all related project relations

        :param project_id: Project ID
        :return ZedToken
        """
        return self.delete_relation(SpiceDBResourceTypes.PROJECT.value, project_id).deleted_at

    def delete_workspace(self, workspace_id: str) -> ZedToken:
        """
        Deletes workspace and removes all related workspace relations

        :param workspace_id: Project ID
        :return ZedToken
        """
        return self.delete_relation(SpiceDBResourceTypes.WORKSPACE.value, workspace_id).deleted_at

    def delete_user(self, user_id: str) -> ZedToken:
        """
        Deletes user from workspaces and projects

        :param user_id: User ID
        :return ZedToken
        """
        self.delete_subject(
            SpiceDBResourceTypes.WORKSPACE, SpiceDBResourceTypes.USER.value, self.convert_user_id(user_id)
        )
        return self.delete_subject(
            SpiceDBResourceTypes.PROJECT, SpiceDBResourceTypes.USER.value, self.convert_user_id(user_id)
        ).deleted_at

    def delete_project_user(self, project_id: str, user_id: str, relation: Relations) -> ZedToken:
        """
        Deletes a project user with a certain role (relation)

        :param project_id: Project ID
        :param user_id: User ID
        :param relation: User relation (Manager, Contributor)
        :return ZedToken
        """
        return self.write_relationship(
            operation=authzed.RelationshipUpdate.Operation.OPERATION_DELETE,
            resource=ObjectReference(object_type=SpiceDBResourceTypes.PROJECT.value, object_id=project_id),
            relation=relation.value,
            subject=SubjectReference(
                object=ObjectReference(
                    object_type=SpiceDBResourceTypes.USER.value, object_id=self.convert_user_id(user_id)
                )
            ),
        ).written_at

    def delete_workspace_user(self, workspace_id: str, user_id: str, relation: Relations) -> ZedToken:
        """
        Deletes a workspace user with a certain role (relation)

        :param workspace_id: workspace ID
        :param user_id: User ID
        :param relation: User relation (Manager, Contributor)
        :return ZedToken
        """
        return self.write_relationship(
            operation=authzed.RelationshipUpdate.Operation.OPERATION_DELETE,
            resource=ObjectReference(object_type=SpiceDBResourceTypes.WORKSPACE.value, object_id=workspace_id),
            relation=relation.value,
            subject=SubjectReference(
                object=ObjectReference(
                    object_type=SpiceDBResourceTypes.USER.value, object_id=self.convert_user_id(user_id)
                )
            ),
        ).written_at

    @retry_grpc_call_on_unavailable_response
    def delete_relation(self, resource_object_type: str, resource_id: str) -> DeleteRelationshipsResponse:
        return self._client.DeleteRelationships(
            DeleteRelationshipsRequest(
                relationship_filter=RelationshipFilter(
                    resource_type=resource_object_type, optional_resource_id=resource_id
                )
            )
        )

    @retry_grpc_call_on_unavailable_response
    def delete_subject(
        self, resource_object_type: str, subject_type: str, subject_id: str
    ) -> DeleteRelationshipsResponse:
        return self._client.DeleteRelationships(
            DeleteRelationshipsRequest(
                relationship_filter=RelationshipFilter(
                    resource_type=resource_object_type,
                    optional_subject_filter=SubjectFilter(subject_type=subject_type, optional_subject_id=subject_id),
                )
            )
        )

    @staticmethod
    def convert_user_id(user_id: str) -> str:
        return base64.b64encode(bytes(user_id, "utf-8")).decode("utf-8").replace("=", "")
