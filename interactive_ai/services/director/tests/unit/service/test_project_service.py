# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch

import pytest

from service.project_service import ProjectService

from iai_core.repos import AnnotationSceneRepo, ProjectRepo


@pytest.fixture
def patched_repo():
    with patch.object(AnnotationSceneRepo, "__init__", return_value=None):
        yield

    AnnotationSceneRepo._instances = {}


class TestProjectService:
    @pytest.mark.parametrize("job_type", ["train", "optimize_pot", "test"])
    def test_unlock_project(self, job_type, fxt_ote_id):
        # Arrange

        project_id = fxt_ote_id(2)

        # Act
        with patch.object(ProjectRepo, "mark_unlocked") as mock_unlock:
            ProjectService.unlock(job_type=job_type, project_id=project_id)

        mock_unlock.assert_called_once_with(owner=job_type, project_id=project_id)
