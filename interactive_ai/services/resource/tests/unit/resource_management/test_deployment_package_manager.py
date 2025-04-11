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

import cv2
import numpy

from resource_management.deployment_package_manager import DeploymentPackageManager

from sc_sdk.entities.project import Project
from sc_sdk.repos import ModelRepo


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
