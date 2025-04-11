# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

import os
from unittest.mock import MagicMock, patch

import pytest
from sc_sdk.entities.model import TrainingFramework, TrainingFrameworkType

from jobs_common.k8s_helpers.trainer_image_info import TrainerImageInfo


@pytest.mark.JobsComponent
class TestTrainerImageInfo:
    @pytest.mark.parametrize(
        "training_framework, feature_flag_otx_version_selection, primary_image_full_name, sidecar_image_full_name",
        [
            (
                TrainingFramework(type=TrainingFrameworkType.OTX, version="2.1.0"),
                "false",
                "otx2_image",
                "mlflow_sidecar_image",
            ),
            (
                TrainingFramework(type=TrainingFrameworkType.OTX, version="1.6.0"),
                "false",
                "otx2_image",
                "mlflow_sidecar_image",
            ),
            (
                TrainingFramework(type=TrainingFrameworkType.OTX, version="2.1.0"),
                "true",
                "otx2_image",
                "mlflow_sidecar_image",
            ),
            (
                TrainingFramework(type=TrainingFrameworkType.OTX, version="1.6.0"),
                "true",
                "ote_image",
                "mlflow_sidecar_image",
            ),
        ],
    )
    @patch("jobs_common.k8s_helpers.trainer_image_info.get_config_map")
    def test_create(
        self,
        mock_get_config_map,
        training_framework,
        feature_flag_otx_version_selection,
        primary_image_full_name,
        sidecar_image_full_name,
    ):
        os.environ.update(
            {
                "FEATURE_FLAG_OTX_VERSION_SELECTION": feature_flag_otx_version_selection,
                "MLFLOW_SIDECAR_IMAGE_NAME": "mlflow_geti_store",
            }
        )
        configmap_data = {
            "registry_address": "registry",
            "tag": "develop",
            "mlflow_sidecar_image": "mlflow_sidecar_image",
            "ote_image": "ote_image",
            "otx2_image": "otx2_image",
        }
        mock_get_config_map.return_value = MagicMock()
        mock_get_config_map.return_value.data.get.side_effect = lambda key: configmap_data.get(key)

        trainer_image_info = TrainerImageInfo.create(training_framework)

        assert trainer_image_info.to_primary_image_full_name() == primary_image_full_name
        assert trainer_image_info.to_sidecar_image_full_name() == sidecar_image_full_name
