# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
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
from http import HTTPStatus

from geti_types import CTX_SESSION_VAR


class TestModelRESTEndpoint:
    def test_supported_algorithms_endpoint_single_task(self, fxt_director_app, fxt_db_project_service) -> None:
        # Default templates are patched because these are unavailable on the testing environment
        session = CTX_SESSION_VAR.get()
        project = fxt_db_project_service.create_annotated_detection_project()
        workspace_id = project.workspace_id
        project_id = project.id_
        endpoint = (
            f"/api/v1/organizations/{str(session.organization_id)}"
            f"/workspaces/{workspace_id}"
            f"/projects/{project_id}"
            f"/supported_algorithms"
        )

        supported_algorithms = [
            {
                "name": "mock_detection",
                "task_type": "detection",
                "model_size": 0,
                "model_template_id": "detection",
                "gigaflops": 0,
                "summary": "",
                "supports_auto_hpo": False,
                "default_algorithm": True,
                "performance_category": "other",
                "lifecycle_stage": "active",
            }
        ]

        result = fxt_director_app.get(endpoint)

        assert result.status_code == HTTPStatus.OK
        data = result.json()
        for item in data["supported_algorithms"]:
            assert item in supported_algorithms

    def test_supported_algorithms_endpoint_task_chain(self, fxt_director_app, fxt_db_project_service) -> None:
        # Default templates are patched because these are unavailable on the testing environment
        session = CTX_SESSION_VAR.get()
        project = fxt_db_project_service.create_annotated_detection_classification_project()
        workspace_id = project.workspace_id
        project_id = project.id_
        endpoint = (
            f"/api/v1/organizations/{str(session.organization_id)}"
            f"/workspaces/{workspace_id}"
            f"/projects/{project_id}"
            f"/supported_algorithms"
        )
        supported_algorithms = [
            {
                "name": "mock_detection",
                "task_type": "detection",
                "model_size": 0,
                "model_template_id": "detection",
                "gigaflops": 0,
                "summary": "",
                "supports_auto_hpo": False,
                "default_algorithm": True,
                "performance_category": "other",
                "lifecycle_stage": "active",
            },
            {
                "name": "mock_classification",
                "task_type": "classification",
                "model_size": 0,
                "model_template_id": "classification",
                "gigaflops": 0,
                "summary": "",
                "supports_auto_hpo": False,
                "default_algorithm": True,
                "performance_category": "other",
                "lifecycle_stage": "active",
            },
        ]

        result = fxt_director_app.get(endpoint)

        assert result.status_code == HTTPStatus.OK
        data = result.json()
        for item in data["supported_algorithms"]:
            assert item in supported_algorithms
