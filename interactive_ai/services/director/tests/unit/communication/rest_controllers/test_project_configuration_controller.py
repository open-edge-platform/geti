# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from testfixtures import compare

from communication.controllers.project_configuration_controller import ProjectConfigurationRESTController
from storage.repos.project_configuration_repo import ProjectConfigurationRepo

from geti_fastapi_tools.exceptions import ProjectNotFoundException
from geti_types import ID, ProjectIdentifier


@pytest.fixture
def project_configuration_controller():
    return ProjectConfigurationRESTController()


class TestProjectConfigurationRESTController:
    def test_get_configuration(
        self,
        request,
        fxt_project_identifier,
        project_configuration_controller,
        fxt_project_configuration,
        fxt_project_configuration_rest_view,
    ) -> None:
        # Arrange
        repo = ProjectConfigurationRepo(fxt_project_identifier)
        request.addfinalizer(lambda: repo.delete_all())
        repo.save(fxt_project_configuration)

        # Act
        result = project_configuration_controller.get_configuration(project_identifier=fxt_project_identifier)

        # Convert to dict to compare with expected output
        compare(result, fxt_project_configuration_rest_view, ignore_eq=True)

    def test_get_configuration_not_found(self, project_configuration_controller) -> None:
        project_id = ID("dummy_project_id")
        workspace_id = ID("dummy_workspace_id")
        project_identifier = ProjectIdentifier(workspace_id=workspace_id, project_id=project_id)

        with pytest.raises(ProjectNotFoundException):
            project_configuration_controller.get_configuration(project_identifier=project_identifier)
