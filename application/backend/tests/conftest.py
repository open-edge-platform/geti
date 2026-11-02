# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Callable
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np
import pytest
import tifffile

from app.core.jobs.models import Job, JobParams, JobType
from app.models import (
    ModelRevision,
    MqttSinkConfig,
    OutputFormat,
    Pipeline,
    PipelineStatus,
    SinkType,
    SourceType,
    TrainingInfo,
    TrainingStatus,
    USBCameraSourceConfig,
)
from app.models.sink import MqttConfig
from app.models.source import USBCameraConfig


@pytest.fixture
def fxt_usb_camera_source() -> USBCameraSourceConfig:
    """Sample source configuration data."""
    return USBCameraSourceConfig(
        id=uuid4(),
        source_type=SourceType.USB_CAMERA,
        name="Test Source",
        config_data=USBCameraConfig(device_id=1, codec=None),
    )


@pytest.fixture
def fxt_mqtt_sink() -> MqttSinkConfig:
    """Sample sink configuration data."""
    return MqttSinkConfig(
        id=uuid4(),
        sink_type=SinkType.MQTT,
        name="Test Sink",
        rate_limit=0.1,
        output_formats=[OutputFormat.IMAGE_WITH_PREDICTIONS],
        config_data=MqttConfig(
            broker_host="localhost",
            broker_port=1883,
            topic="topic",
            auth_required=False,
        ),
    )


@pytest.fixture
def fxt_model() -> ModelRevision:
    """Sample model data."""
    return ModelRevision(
        id=uuid4(),
        name="YOLOX-X (abc123)",
        architecture="object-detection-yolox-x",
        training_info=TrainingInfo(status=TrainingStatus.NOT_STARTED, label_schema_revision={}, configuration={}),  # type: ignore
    )  # type: ignore


@pytest.fixture
def fxt_default_pipeline() -> Pipeline:
    """Sample default pipeline data."""
    return Pipeline(
        project_id=uuid4(),
        source=None,
        sink=None,
        model_revision=None,
        status=PipelineStatus.IDLE,
    )


@pytest.fixture
def fxt_running_pipeline(fxt_usb_camera_source, fxt_mqtt_sink, fxt_model) -> Pipeline:
    """Sample default pipeline data."""
    return Pipeline(
        project_id=uuid4(),
        source_id=fxt_usb_camera_source.id,
        sink_id=fxt_mqtt_sink.id,
        model_id=fxt_model.id,
        status=PipelineStatus.RUNNING,
    )


@pytest.fixture
def fxt_job() -> Callable[[JobType, JobParams], Job]:
    def _factory(job_type: JobType | None = JobType.TRAIN, params: JobParams | None = None) -> Job:
        return Job(job_type=job_type, params=JobParams() if params is None else params)

    return _factory


def ome_pixel_value(t: int, c: int, z: int) -> int:
    """Constant value of the (t, c, z) plane in OME-TIFF images written by `fxt_ome_tiff_factory`."""
    return 100 * t + 10 * c + z + 1


@pytest.fixture
def fxt_ome_tiff_factory(tmp_path: Path) -> Callable[..., Path]:
    """
    Returns a callable writing a synthetic OME-TIFF image (axes TCZYX) and returning its path.

    Every (t, c, z) plane is filled with `ome_pixel_value(t, c, z)`, so that plane selection can be asserted.
    """

    def _write(
        name: str = "image.ome.tiff",
        size_t: int = 1,
        size_c: int = 3,
        size_z: int = 1,
        height: int = 32,
        width: int = 48,
        dtype: type = np.uint16,
        channels: dict[str, list[Any]] | None = None,
        significant_bits: int | None = None,
        pyramid_levels: int = 1,
        bigtiff: bool = False,
    ) -> Path:
        data = np.zeros((size_t, size_c, size_z, height, width), dtype=dtype)
        for t in range(size_t):
            for c in range(size_c):
                for z in range(size_z):
                    data[t, c, z] = ome_pixel_value(t, c, z)
        metadata: dict[str, Any] = {"axes": "TCZYX"}
        if channels is not None:
            metadata["Channel"] = channels
        if significant_bits is not None:
            metadata["SignificantBits"] = significant_bits
        path = tmp_path / name
        tile = (16, 16) if pyramid_levels > 1 else None
        with tifffile.TiffWriter(path, bigtiff=bigtiff, ome=True) as writer:
            writer.write(data, subifds=pyramid_levels - 1, metadata=metadata, photometric="minisblack", tile=tile)
            for level in range(1, pyramid_levels):
                factor = 2**level
                writer.write(data[..., ::factor, ::factor], subfiletype=1, photometric="minisblack", tile=tile)
        return path

    return _write
