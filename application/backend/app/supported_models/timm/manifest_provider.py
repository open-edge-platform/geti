# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import huggingface_hub
from loguru import logger

from app.models import TaskType
from app.models.model_manifest import (
    BenchmarkMetrics,
    Capabilities,
    ModelManifest,
    ModelManifestDeprecationStatus,
    ModelStats,
    WeightsSource,
)
from app.models.training_configuration import AlgoLevelParameters, AlgoLevelTrainingParameters
from app.supported_models.timm.catalog import _snapshot

_DEFAULT_LICENSE = "apache-2.0"
_ID_PREFIX = "image-classification-timm-"


def model_name_to_id(model_name: str) -> str:
    """Convert a bare timm model name to its manifest ID."""
    return _ID_PREFIX + model_name


def id_to_model_name(manifest_id: str) -> str:
    """Convert a manifest ID back to its bare timm model name."""
    return manifest_id.removeprefix(_ID_PREFIX)


def _license_of(model_name: str) -> str:
    """Return the Hugging Face Hub license for *model_name*, defaulting to Apache-2.0."""
    try:
        info = huggingface_hub.model_info(f"timm/{model_name}")
    except huggingface_hub.errors.HfHubHTTPError:
        logger.warning("No model card found on the Hub for %s; defaulting license to {}", model_name, _DEFAULT_LICENSE)
        return _DEFAULT_LICENSE

    if info.card_data is None or not info.card_data.license:
        logger.debug("No license in model card for {}; defaulting to {}", model_name, _DEFAULT_LICENSE)
        return _DEFAULT_LICENSE

    return info.card_data.license


class TimmManifestProvider:
    """Builds ModelManifest objects for timm backbones from the snapshot."""

    @staticmethod
    def is_timm_id(manifest_id: str) -> bool:
        return manifest_id.startswith(_ID_PREFIX)

    @classmethod
    def build_manifest(cls, model_name: str) -> ModelManifest:
        e = _snapshot()[model_name]
        _, h, w = e["input_size"]
        return ModelManifest(
            id=model_name_to_id(model_name),
            name=f"timm/{model_name}",
            license=_license_of(model_name),
            family=e["family"],
            version=e["version"],
            pretrained=e["pretrained"],
            task=TaskType.CLASSIFICATION,
            description=f"timm backbone '{model_name}'.",
            pretrained_weights=None,
            weights_source=WeightsSource.TIMM_MANAGED,
            support_status=ModelManifestDeprecationStatus.ACTIVE,
            capabilities=Capabilities(xai=False, tiling=False),
            stats=ModelStats(
                gigaflops=e.get("gigaflops", 0.0),
                trainable_parameters=e.get("trainable_parameters", 0.0),
                benchmark_metrics=BenchmarkMetrics(
                    imagenet_top1_accuracy=e.get("imagenet_top1_accuracy"),
                ),
            ),
            # ---- Dynamic hyperparameters keyed on the chosen architecture ----
            hyperparameters=AlgoLevelParameters(
                training=AlgoLevelTrainingParameters(
                    learning_rate=e["default_lr"],
                    weight_decay=e["default_weight_decay"],
                    input_size_width=w,
                    input_size_height=h,
                    allowed_values_input_size=[w, h],
                    # everything else (epochs, batch, scheduler, early stopping,
                    # augmentation) inherits classification/base.yaml defaults.
                ),
            ),
        )

    @classmethod
    def get_preprocessing(cls, model_name: str) -> dict:
        e = _snapshot()[model_name]
        _, height, width = e["input_size"]
        return {
            "input_size": (height, width),
        }
