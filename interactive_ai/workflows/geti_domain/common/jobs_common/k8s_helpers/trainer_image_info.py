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
"""
Defines train image info
"""

import asyncio
import logging
import os
from dataclasses import dataclass

from dataclasses_json import dataclass_json
from kubernetes_asyncio import client, config
from kubernetes_asyncio.config import ConfigException
from packaging.version import parse as parse_version
from sc_sdk.entities.model import TrainingFramework, TrainingFrameworkType

from jobs_common.features.feature_flag_provider import FeatureFlag, FeatureFlagProvider

logger = logging.getLogger(__name__)


async def get_config_map(namespace: str, name: str = "impt-configuration") -> client.V1ConfigMap:
    """
    Gets config map
    :param namespace: config map namespace
    :param name: config map name
    :return: config map
    """
    try:
        try:
            await config.load_kube_config()
        except (FileNotFoundError, TypeError, ConfigException):
            config.load_incluster_config()

        core_api = client.CoreV1Api(client.ApiClient())
        return await core_api.read_namespaced_config_map(namespace=namespace, name=name)

    except Exception:
        logger.exception(f"Failed to get config map {name} from {namespace} namespace")
        raise


@dataclass_json
@dataclass
class TrainerImageInfo:
    """Trainer image information."""

    train_image_name: str
    sidecar_image_name: str

    @classmethod
    def create(cls, training_framework: TrainingFramework) -> "TrainerImageInfo":
        """Create trainer image information from the given training framework.

        :param training_framework: Dataclass to choose the trainer image
        """

        if training_framework.type != TrainingFrameworkType.OTX:
            raise ValueError(f"{training_framework.type} type is not supported yet.")

        namespace = os.getenv("IMPT_NAMESPACE", "impt")
        name = os.getenv("IMPT_CONFIGURATION", "impt-configuration")

        configmap = asyncio.run(get_config_map(namespace=namespace, name=name))

        msg = "Cannot get `{0}` field from config map `{1}/{2}`"

        # This information is from `impt-configuration` config map in the namespace `impt`
        if (mlflow_sidecar_image := configmap.data.get("mlflow_sidecar_image")) is None:
            raise ValueError(msg.format("mlflow_sidecar_image", namespace, name))
        if (ote_image := configmap.data.get("ote_image")) is None:
            raise ValueError(msg.format("ote_image", namespace, name))
        if (otx2_image := configmap.data.get("otx2_image")) is None:
            raise ValueError(msg.format("otx2_image", namespace, name))

        if FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_OTX_VERSION_SELECTION):
            if parse_version(training_framework.version) < parse_version("2.0.0"):
                image_name = ote_image
            else:
                image_name = otx2_image
        else:
            image_name = otx2_image

        logger.info(
            f"Trainer image has been selected {image_name}, where a model has trainer "
            f"identification for {training_framework.version}."
        )
        return cls(train_image_name=image_name, sidecar_image_name=mlflow_sidecar_image)

    def to_primary_image_full_name(self) -> str:
        """Get primary image full name.

        For example, it would be "dev-registry.toolbox.com/impp/ote:2.2.0".
        """
        return self.train_image_name

    def to_sidecar_image_full_name(self) -> str:
        """Get sidecar image full name.

        For example, it would be "dev-registry.toolbox.com/impp/mlflow-geti-store:2.2.0".
        """
        return self.sidecar_image_name
