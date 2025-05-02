# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch

import cv2
import numpy

from resource_management.deployment_package_manager import DeploymentPackageManager

from iai_core.entities.project import Project
from iai_core.repos import ModelRepo


class TestDeploymentPackageManager:
    def test_prepare_geti_sdk_package(
        self,
        fxt_project,
        fxt_project_rest,
        fxt_optimized_model_1_with_exportable_code,
        fxt_optimized_model_2_with_exportable_code,
        fxt_model_identifiers,
    ) -> None:
        with (
            patch.object(
                ModelRepo,
                "get_by_id",
                side_effect=[
                    fxt_optimized_model_1_with_exportable_code,
                    fxt_optimized_model_2_with_exportable_code,
                ],
            ),
            patch.object(
                Project,
                "get_trainable_task_node_by_id",
                return_value=fxt_project.get_trainable_task_nodes()[0],
            ),
            patch.object(
                DeploymentPackageManager,
                "_get_random_image_from_project",
                return_value=cv2.cvtColor(numpy.zeros([10, 10, 3], dtype=numpy.uint8), cv2.COLOR_BGR2RGB),
            ),
            patch.object(
                ModelRepo,
                "get_latest_model_for_inference",
                side_effect=[
                    fxt_optimized_model_1_with_exportable_code,
                    fxt_optimized_model_2_with_exportable_code,
                ],
            ),
            patch.object(
                ModelRepo,
                "get_all_equivalent_model_ids",
                side_effect=[
                    [fxt_optimized_model_1_with_exportable_code.id_],
                    [fxt_optimized_model_2_with_exportable_code.id_],
                ],
            ),
        ):
            DeploymentPackageManager.prepare_geti_sdk_package(
                project=fxt_project,
                project_rest_view=fxt_project_rest,
                model_identifiers=fxt_model_identifiers,
            )
