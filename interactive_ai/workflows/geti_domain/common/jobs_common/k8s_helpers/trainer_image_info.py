# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
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
    render_gid: int = 0  # Should be non-zero value when training with Intel GPUs

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

        render_gid = 0

        msg = "Cannot get `{0}` field from config map `{1}/{2}`"

        # This information is from `impt-configuration` config map in the namespace `impt`
        if (mlflow_sidecar_image := configmap.data.get("mlflow_sidecar_image")) is None:
            raise ValueError(msg.format("mlflow_sidecar_image", namespace, name))
        if (ote_image := configmap.data.get("ote_image")) is None:
            raise ValueError(msg.format("ote_image", namespace, name))
        if (otx2_image := configmap.data.get("otx2_image")) is None:
            raise ValueError(msg.format("otx2_image", namespace, name))
        if configmap.data.get("render_gid"):
            render_gid = int(configmap.data["render_gid"])
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
        return cls(train_image_name=image_name, sidecar_image_name=mlflow_sidecar_image, render_gid=render_gid)

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
