# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.
from unittest.mock import patch

import pytest

from service.project_service import ProjectService

from sc_sdk.repos import AnnotationSceneRepo, ProjectRepo


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
