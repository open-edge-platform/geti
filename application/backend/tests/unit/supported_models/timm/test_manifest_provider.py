# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from types import MappingProxyType
from unittest.mock import Mock, patch

import huggingface_hub
import pytest

from app.models.model_manifest import ModelManifestDeprecationStatus, WeightsSource
from app.models.task import TaskType
from app.supported_models.timm import catalog, manifest_provider
from app.supported_models.timm.manifest_provider import (
    _DEFAULT_LICENSE,
    TimmManifestProvider,
    _license_of,
    id_to_model_name,
    model_name_to_id,
)

_FAKE_ENTRY = {
    "model_name": "resnet18.a1_in1k",
    "family": "resnet",
    "version": "resnet18",
    "pretrained": "a1_in1k",
    "input_size": [3, 224, 224],
    "default_lr": 0.01,
    "default_weight_decay": 0.001,
    "imagenet_top1_accuracy": 70.0,
    "trainable_parameters": 11.7,
    "gigaflops": 1.8,
}
_FAKE_SNAPSHOT = MappingProxyType({_FAKE_ENTRY["model_name"]: _FAKE_ENTRY})


@pytest.fixture(autouse=True)
def _fake_snapshot():
    """Replace the cached snapshot with a small, deterministic fixture."""
    catalog._snapshot.cache_clear()
    with patch.object(manifest_provider, "_snapshot", return_value=_FAKE_SNAPSHOT):
        yield


class TestModelIdConversion:
    def test_model_name_to_id_adds_prefix(self) -> None:
        assert model_name_to_id("resnet18.a1_in1k") == "image-classification-timm-resnet18.a1_in1k"

    def test_id_to_model_name_strips_prefix(self) -> None:
        assert id_to_model_name("image-classification-timm-resnet18.a1_in1k") == "resnet18.a1_in1k"

    def test_round_trip(self) -> None:
        model_name = "vit_base_patch16_224.augreg_in21k_ft_in1k"
        assert id_to_model_name(model_name_to_id(model_name)) == model_name

    def test_id_to_model_name_without_prefix_is_unchanged(self) -> None:
        assert id_to_model_name("not-a-timm-id") == "not-a-timm-id"


class TestTimmManifestProvider:
    def test_recognizes_timm_prefixed_id(self) -> None:
        assert TimmManifestProvider.is_timm_id("image-classification-timm-resnet18.a1_in1k") is True

    def test_rejects_non_timm_id(self) -> None:
        assert TimmManifestProvider.is_timm_id("image-classification-yolo-v8") is False

    def test_build_manifest_maps_snapshot_fields(self) -> None:
        fake_info = Mock(card_data=Mock(license="apache-2.0"))
        with patch.object(huggingface_hub, "model_info", return_value=fake_info):
            manifest = TimmManifestProvider.build_manifest("resnet18.a1_in1k")

        assert manifest.id == model_name_to_id("resnet18.a1_in1k")
        assert manifest.name == "timm/resnet18.a1_in1k"
        assert manifest.license == "apache-2.0"
        assert manifest.family == "resnet"
        assert manifest.version == "resnet18"
        assert manifest.pretrained == "a1_in1k"
        assert manifest.task == TaskType.CLASSIFICATION
        assert manifest.weights_source == WeightsSource.TIMM_MANAGED
        assert manifest.pretrained_weights is None
        assert manifest.support_status == ModelManifestDeprecationStatus.ACTIVE
        assert manifest.stats.gigaflops == 1.8
        assert manifest.stats.trainable_parameters == 11.7
        assert manifest.stats.benchmark_metrics.imagenet_top1_accuracy == 70.0
        assert manifest.hyperparameters.training.input_size_width == 224
        assert manifest.hyperparameters.training.input_size_height == 224
        assert manifest.hyperparameters.training.learning_rate == 0.01
        assert manifest.hyperparameters.training.weight_decay == 0.001

    def test_build_manifest_missing_model_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            TimmManifestProvider.build_manifest("unknown-model")

    def test_get_preprocessing_maps_snapshot_fields(self) -> None:
        preprocessing = TimmManifestProvider.get_preprocessing("resnet18.a1_in1k")

        assert preprocessing == {
            "input_size": (224, 224),
        }

    def test_returns_hub_license_when_present(self) -> None:
        fake_info = Mock(card_data=Mock(license="mit"))
        with patch.object(huggingface_hub, "model_info", return_value=fake_info):
            assert _license_of("resnet18.a1_in1k") == "mit"

    def test_defaults_when_no_card_data(self) -> None:
        fake_info = Mock(card_data=None)
        with patch.object(huggingface_hub, "model_info", return_value=fake_info):
            assert _license_of("resnet18.a1_in1k") == _DEFAULT_LICENSE

    def test_defaults_when_license_field_empty(self) -> None:
        fake_info = Mock(card_data=Mock(license=None))
        with patch.object(huggingface_hub, "model_info", return_value=fake_info):
            assert _license_of("resnet18.a1_in1k") == _DEFAULT_LICENSE

    def test_defaults_when_hub_lookup_fails(self) -> None:
        with patch.object(
            huggingface_hub,
            "model_info",
            side_effect=huggingface_hub.errors.HfHubHTTPError("not found", response=Mock(status_code=404)),
        ):
            assert _license_of("resnet18.a1_in1k") == _DEFAULT_LICENSE
