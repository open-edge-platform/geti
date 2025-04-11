from unittest.mock import call, patch

import pytest
from authzed.api.v1 import (
    CheckPermissionRequest,
    CheckPermissionResponse,
    Consistency,
    DeleteRelationshipsRequest,
    DeleteRelationshipsResponse,
    LookupResourcesRequest,
    LookupResourcesResponse,
    ObjectReference,
    Relationship,
    RelationshipFilter,
    RelationshipUpdate,
    SubjectFilter,
    SubjectReference,
    WriteRelationshipsRequest,
    WriteRelationshipsResponse,
    ZedToken,
)

from geti_spicedb_tools import Permissions, Relations, SpiceDB, SpiceDBResourceTypes


class TestSpiceDB:
    @patch("authzed.api.v1.Client")
    def test_create_workspace(self, mocked_client):
        # Arrange
        spicedb = SpiceDB()
        spicedb._client = mocked_client
        with patch.object(
            spicedb, "add_workspace_user", wraps=spicedb.add_workspace_user
        ) as wrapped_add_workspace_user:
            # Act
            spicedb.create_workspace("test_workspace", "test_user")

            # Assert
            wrapped_add_workspace_user.assert_called_with("test_workspace", "test_user", Relations.WORKSPACE_ADMIN)

    @patch("authzed.api.v1.Client")
    @pytest.mark.parametrize("user_relation", Relations)
    def test_add_workspace_user(self, mocked_client, user_relation: Relations):
        # Arrange
        spicedb = SpiceDB()
        spicedb._client = mocked_client
        mocked_client.WriteRelationships.return_value = WriteRelationshipsResponse(
            written_at=ZedToken(token="test_token")
        )

        # Act
        response = spicedb.add_workspace_user("test_workspace", "test_user", user_relation)

        # Assert
        assert response.token == "test_token", "Expected valid response token"
        expected_arguments = WriteRelationshipsRequest(
            updates=[
                RelationshipUpdate(
                    operation=1,
                    relationship=Relationship(
                        resource=ObjectReference(object_type="workspace", object_id="test_workspace"),
                        relation=user_relation.value,
                        subject=SubjectReference(object=ObjectReference(object_type="user", object_id="dGVzdF91c2Vy")),
                    ),
                ),
            ]
        )
        mocked_client.WriteRelationships.assert_called_once_with(expected_arguments)

    @patch("authzed.api.v1.Client")
    @pytest.mark.parametrize("user_relation", Relations)
    def test_delete_workspace_user(self, mocked_client, user_relation: Relations):
        # Arrange
        spicedb = SpiceDB()
        spicedb._client = mocked_client
        mocked_client.WriteRelationships.return_value = WriteRelationshipsResponse(
            written_at=ZedToken(token="test_token")
        )

        # Act
        response = spicedb.delete_workspace_user("test_workspace", "test_user", user_relation)
        assert response.token == "test_token", "Expected valid response token"

        # Assert
        expected_arguments = WriteRelationshipsRequest(
            updates=[
                RelationshipUpdate(
                    operation=3,
                    relationship=Relationship(
                        resource=ObjectReference(object_type="workspace", object_id="test_workspace"),
                        relation=user_relation.value,
                        subject=SubjectReference(object=ObjectReference(object_type="user", object_id="dGVzdF91c2Vy")),
                    ),
                ),
            ]
        )
        mocked_client.WriteRelationships.assert_called_once_with(expected_arguments)

    @patch("authzed.api.v1.Client")
    @pytest.mark.parametrize("permission", Permissions)
    @pytest.mark.parametrize(
        "permissionship,expected_response",
        [
            (1, False),
            (2, True),
        ],
    )
    @pytest.mark.skip("CVS-164150")
    def test_check_user_workspace_permission(
        self,
        mocked_client,
        permission: Permissions,
        permissionship: int,
        expected_response: bool,
    ):
        # Arrange
        spicedb = SpiceDB()
        spicedb._client = mocked_client
        mocked_client.CheckPermissions.return_value = CheckPermissionResponse(
            checked_at=ZedToken(token="test_token"), permissionship=permissionship
        )

        # Act
        response = spicedb.check_permission(
            SpiceDBResourceTypes.USER.value,
            "test_user",
            SpiceDBResourceTypes.WORKSPACE.value,
            "test_workspace",
            permission,
        )

        # Assert
        assert response is expected_response, "Expected valid response token"
        expected_arguments = CheckPermissionRequest(
            resource=ObjectReference(object_type="workspace", object_id="test_workspace"),
            permission=permission.value,
            subject=SubjectReference(object=ObjectReference(object_type="user", object_id="dGVzdF91c2Vy")),
            consistency=Consistency(fully_consistent=True),
        )
        mocked_client.CheckPermissions.assert_called_once_with(expected_arguments)

    @patch("authzed.api.v1.Client")
    @pytest.mark.parametrize("permission", Permissions)
    def test_get_user_workspaces(self, mocked_client, permission: Permissions):
        # Arrange
        spicedb = SpiceDB()
        spicedb._client = mocked_client
        mocked_client.LookupResources.return_value = [
            LookupResourcesResponse(resource_object_id="test_workspace_1"),
            LookupResourcesResponse(resource_object_id="test_workspace_2"),
        ]

        # Act
        response = spicedb.get_user_workspaces("test_user", permission)

        # Assert
        assert response == (
            "test_workspace_1",
            "test_workspace_2",
        ), "Expected valid workspaces"
        expected_arguments = LookupResourcesRequest(
            resource_object_type="workspace",
            permission=permission.value,
            subject=SubjectReference(object=ObjectReference(object_type="user", object_id="dGVzdF91c2Vy")),
            consistency=Consistency(fully_consistent=True),
        )
        mocked_client.LookupResources.assert_called_once_with(expected_arguments)

    @patch("authzed.api.v1.Client")
    def test_delete_workspace(self, mocked_client):
        # Arrange
        spicedb = SpiceDB()
        spicedb._client = mocked_client
        mocked_client.DeleteRelationships.return_value = DeleteRelationshipsResponse(
            deleted_at=ZedToken(token="test_token")
        )

        # Act
        response = spicedb.delete_workspace("test_workspace")

        # Assert
        assert response.token == "test_token", "Expected valid response token"
        expected_arguments = DeleteRelationshipsRequest(
            relationship_filter=RelationshipFilter(resource_type="workspace", optional_resource_id="test_workspace")
        )
        mocked_client.DeleteRelationships.assert_called_once_with(expected_arguments)

    @patch("authzed.api.v1.Client")
    def test_create_project(self, mocked_client):
        # Arrange
        spicedb = SpiceDB()
        spicedb._client = mocked_client
        mocked_client.WriteRelationships.return_value = WriteRelationshipsResponse(
            written_at=ZedToken(token="test_token")
        )

        # Act
        response = spicedb.create_project("test_workspace", "test_project", "test_user")

        # Assert
        assert response.token == "test_token", "Expected valid response token"
        expected_arguments_user = WriteRelationshipsRequest(
            updates=[
                RelationshipUpdate(
                    operation=1,
                    relationship=Relationship(
                        resource=ObjectReference(object_type="project", object_id="test_project"),
                        relation="project_manager",
                        subject=SubjectReference(object=ObjectReference(object_type="user", object_id="dGVzdF91c2Vy")),
                    ),
                ),
            ]
        )
        expected_arguments_workspace = WriteRelationshipsRequest(
            updates=[
                RelationshipUpdate(
                    operation=1,
                    relationship=Relationship(
                        resource=ObjectReference(object_type="project", object_id="test_project"),
                        relation="parent_workspace",
                        subject=SubjectReference(
                            object=ObjectReference(object_type="workspace", object_id="test_workspace")
                        ),
                    ),
                )
            ]
        )
        mocked_client.WriteRelationships.assert_has_calls(
            [call(expected_arguments_workspace), call(expected_arguments_user)]
        )

    @patch("authzed.api.v1.Client")
    def test_add_project_space(self, mocked_client):
        # Arrange
        spicedb = SpiceDB()
        spicedb._client = mocked_client
        mocked_client.WriteRelationships.return_value = WriteRelationshipsResponse(
            written_at=ZedToken(token="test_token")
        )

        # Act
        response = spicedb.add_project_space("test_project", "test_workspace")

        # Assert
        assert response.token == "test_token", "Expected valid response token"
        expected_arguments = WriteRelationshipsRequest(
            updates=[
                RelationshipUpdate(
                    operation=1,
                    relationship=Relationship(
                        resource=ObjectReference(object_type="project", object_id="test_project"),
                        relation="parent_workspace",
                        subject=SubjectReference(
                            object=ObjectReference(object_type="workspace", object_id="test_workspace")
                        ),
                    ),
                ),
            ]
        )
        mocked_client.WriteRelationships.assert_called_once_with(expected_arguments)

    @patch("authzed.api.v1.Client")
    @pytest.mark.parametrize("user_relation", Relations)
    def test_add_project_user(self, mocked_client, user_relation: Relations):
        # Arrange
        spicedb = SpiceDB()
        spicedb._client = mocked_client
        mocked_client.WriteRelationships.return_value = WriteRelationshipsResponse(
            written_at=ZedToken(token="test_token")
        )

        # Act
        response = spicedb.add_project_user("test_project", "test_user", user_relation)

        # Assert
        assert response.token == "test_token", "Expected valid response token"
        expected_arguments = WriteRelationshipsRequest(
            updates=[
                RelationshipUpdate(
                    operation=1,
                    relationship=Relationship(
                        resource=ObjectReference(object_type="project", object_id="test_project"),
                        relation=user_relation.value,
                        subject=SubjectReference(object=ObjectReference(object_type="user", object_id="dGVzdF91c2Vy")),
                    ),
                ),
            ]
        )
        mocked_client.WriteRelationships.assert_called_once_with(expected_arguments)

    @patch("authzed.api.v1.Client")
    @pytest.mark.parametrize("user_relation", Relations)
    def test_delete_project_user(self, mocked_client, user_relation: Relations):
        # Arrange
        spicedb = SpiceDB()
        spicedb._client = mocked_client
        mocked_client.WriteRelationships.return_value = WriteRelationshipsResponse(
            written_at=ZedToken(token="test_token")
        )

        # Act
        response = spicedb.delete_project_user("test_project", "test_user", user_relation)
        assert response.token == "test_token", "Expected valid response token"

        # Assert
        expected_arguments = WriteRelationshipsRequest(
            updates=[
                RelationshipUpdate(
                    operation=3,
                    relationship=Relationship(
                        resource=ObjectReference(object_type="project", object_id="test_project"),
                        relation=user_relation.value,
                        subject=SubjectReference(object=ObjectReference(object_type="user", object_id="dGVzdF91c2Vy")),
                    ),
                ),
            ]
        )
        mocked_client.WriteRelationships.assert_called_once_with(expected_arguments)

    @patch("authzed.api.v1.Client")
    @pytest.mark.parametrize("permission", Permissions)
    @pytest.mark.parametrize(
        "permissionship,expected_response",
        [
            (1, False),
            (2, True),
        ],
    )
    @pytest.mark.skip("CVS-164150")
    def test_check_user_project_permission(
        self,
        mocked_client,
        permission: Permissions,
        permissionship,
        expected_response: bool,
    ):
        # Arrange
        spicedb = SpiceDB()
        spicedb._client = mocked_client
        mocked_client.CheckPermissions.return_value = CheckPermissionResponse(
            checked_at=ZedToken(token="test_token"), permissionship=permissionship
        )

        # Act
        response = spicedb.check_permission(
            SpiceDBResourceTypes.USER.value, "test_user", SpiceDBResourceTypes.PROJECT.value, "test_project", permission
        )

        # Assert
        assert response is expected_response, "Expected valid response token"
        expected_arguments = CheckPermissionRequest(
            resource=ObjectReference(object_type="project", object_id="test_project"),
            permission=permission.value,
            subject=SubjectReference(object=ObjectReference(object_type="user", object_id="dGVzdF91c2Vy")),
            consistency=Consistency(fully_consistent=True),
        )
        mocked_client.CheckPermissions.assert_called_once_with(expected_arguments)

    @patch("authzed.api.v1.Client")
    @pytest.mark.parametrize("permission", Permissions)
    def test_get_user_projects(self, mocked_client, permission: Permissions):
        # Arrange
        spicedb = SpiceDB()
        spicedb._client = mocked_client
        mocked_client.LookupResources.return_value = [
            LookupResourcesResponse(resource_object_id="test_project_1"),
            LookupResourcesResponse(resource_object_id="test_project_2"),
        ]

        # Act
        response = spicedb.get_user_projects("test_user", permission)

        # Assert
        assert response == (
            "test_project_1",
            "test_project_2",
        ), "Expected valid projects"
        expected_arguments = LookupResourcesRequest(
            resource_object_type="project",
            permission=permission.value,
            subject=SubjectReference(object=ObjectReference(object_type="user", object_id="dGVzdF91c2Vy")),
            consistency=Consistency(fully_consistent=True),
        )
        mocked_client.LookupResources.assert_called_once_with(expected_arguments)

    @patch("authzed.api.v1.Client")
    def test_delete_project(self, mocked_client):
        # Arrange
        spicedb = SpiceDB()
        spicedb._client = mocked_client
        mocked_client.DeleteRelationships.return_value = DeleteRelationshipsResponse(
            deleted_at=ZedToken(token="test_token")
        )

        # Act
        response = spicedb.delete_project("test_project")

        # Assert
        assert response.token == "test_token", "Expected valid response token"
        mocked_client.DeleteRelationships.assert_has_calls(
            [
                call(
                    DeleteRelationshipsRequest(
                        relationship_filter=RelationshipFilter(
                            resource_type="project", optional_resource_id="test_project"
                        )
                    )
                ),
            ]
        )

    @patch("authzed.api.v1.Client")
    def test_delete_user(self, mocked_client):
        # Arrange
        spicedb = SpiceDB()
        spicedb._client = mocked_client
        mocked_client.DeleteRelationships.return_value = DeleteRelationshipsResponse(
            deleted_at=ZedToken(token="test_token")
        )

        # Act
        response = spicedb.delete_user("test_user")

        # Assert
        assert response.token == "test_token", "Expected valid response token"
        mocked_client.DeleteRelationships.assert_has_calls(
            [
                call(
                    DeleteRelationshipsRequest(
                        relationship_filter=RelationshipFilter(
                            resource_type="workspace",
                            optional_subject_filter=SubjectFilter(
                                subject_type="user", optional_subject_id="dGVzdF91c2Vy"
                            ),
                        )
                    )
                ),
                call(
                    DeleteRelationshipsRequest(
                        relationship_filter=RelationshipFilter(
                            resource_type="project",
                            optional_subject_filter=SubjectFilter(
                                subject_type="user", optional_subject_id="dGVzdF91c2Vy"
                            ),
                        )
                    )
                ),
            ]
        )

    @patch("authzed.api.v1.Client")
    def test_create_workspace_job(self, mocked_client):
        # Arrange
        spicedb = SpiceDB()
        spicedb._client = mocked_client
        mocked_client.WriteRelationships.return_value = WriteRelationshipsResponse(
            written_at=ZedToken(token="test_token")
        )

        # Act
        response = spicedb.create_job("test_job", SpiceDBResourceTypes.WORKSPACE.value, "test_workspace")

        # Assert
        assert response.token == "test_token", "Expected valid response token"
        expected_arguments = WriteRelationshipsRequest(
            updates=[
                RelationshipUpdate(
                    operation=1,
                    relationship=Relationship(
                        resource=ObjectReference(object_type="job", object_id="test_job"),
                        relation="parent_entity",
                        subject=SubjectReference(
                            object=ObjectReference(object_type="workspace", object_id="test_workspace")
                        ),
                    ),
                ),
            ]
        )
        mocked_client.WriteRelationships.assert_called_with(expected_arguments)

    @patch("authzed.api.v1.Client")
    def test_create_project_job(self, mocked_client):
        # Arrange
        spicedb = SpiceDB()
        spicedb._client = mocked_client
        mocked_client.WriteRelationships.return_value = WriteRelationshipsResponse(
            written_at=ZedToken(token="test_token")
        )

        # Act
        response = spicedb.create_job("test_job", SpiceDBResourceTypes.PROJECT.value, "test_project")

        # Assert
        assert response.token == "test_token", "Expected valid response token"
        expected_arguments = WriteRelationshipsRequest(
            updates=[
                RelationshipUpdate(
                    operation=1,
                    relationship=Relationship(
                        resource=ObjectReference(object_type="job", object_id="test_job"),
                        relation="parent_entity",
                        subject=SubjectReference(
                            object=ObjectReference(object_type="project", object_id="test_project")
                        ),
                    ),
                ),
            ]
        )
        mocked_client.WriteRelationships.assert_called_with(expected_arguments)

    @patch("authzed.api.v1.Client")
    def test_delete_job(self, mocked_client):
        # Arrange
        spicedb = SpiceDB()
        spicedb._client = mocked_client
        mocked_client.DeleteRelationships.return_value = DeleteRelationshipsResponse(
            deleted_at=ZedToken(token="test_token")
        )

        # Act
        response = spicedb.delete_job("test_job")

        # Assert
        assert response.token == "test_token", "Expected valid response token"
        expected_arguments = DeleteRelationshipsRequest(
            relationship_filter=RelationshipFilter(resource_type="job", optional_resource_id="test_job")
        )
        mocked_client.DeleteRelationships.assert_called_once_with(expected_arguments)

    @patch("authzed.api.v1.Client")
    @pytest.mark.parametrize("permission", Permissions)
    def test_get_user_jobs(self, mocked_client, permission: Permissions):
        # Arrange
        spicedb = SpiceDB()
        spicedb._client = mocked_client
        mocked_client.LookupResources.return_value = [
            LookupResourcesResponse(resource_object_id="test_job_1"),
            LookupResourcesResponse(resource_object_id="test_job_2"),
        ]

        # Act
        response = spicedb.get_user_jobs("test_user", permission)

        # Assert
        assert response == (
            "test_job_1",
            "test_job_2",
        ), "Expected valid jobs"
        expected_arguments = LookupResourcesRequest(
            resource_object_type="job",
            permission=permission.value,
            subject=SubjectReference(object=ObjectReference(object_type="user", object_id="dGVzdF91c2Vy")),
            consistency=Consistency(fully_consistent=True),
        )
        mocked_client.LookupResources.assert_called_once_with(expected_arguments)
