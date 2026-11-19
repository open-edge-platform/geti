# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Callable
from pathlib import Path
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
from app.models.media_storage import MediaStorage
from app.models.sink import MqttConfig
from app.models.source import USBCameraConfig


@pytest.fixture
def companion_storage(tmp_path: Path, request: pytest.FixtureRequest) -> MediaStorage:
    """Create a small multi-file OME-TIFF channel set shared by reader and ingest tests."""
    root = tmp_path / "storage"
    root.mkdir()
    channel_count = getattr(request, "param", 2)
    identifiers = [f"00000000-0000-0000-0000-{index + 1:012d}" for index in range(channel_count)]
    references = "".join(
        f'<TiffData IFD="0" FirstC="{index}" FirstZ="0" FirstT="0" PlaneCount="1">'
        f'<UUID FileName="part{index}.ome.tiff">urn:uuid:{identifier}</UUID></TiffData>'
        for index, identifier in enumerate(identifiers)
    )
    channels = "".join(f'<Channel ID="Channel:0:{index}" SamplesPerPixel="1"/>' for index in range(channel_count))
    for index, identifier in enumerate(identifiers):
        xml = (
            f'<OME xmlns="http://www.openmicroscopy.org/Schemas/OME/2016-06" UUID="urn:uuid:{identifier}">'
            '<Image ID="Image:0"><Pixels ID="Pixels:0" DimensionOrder="XYCZT" Type="uint16" '
            f'SizeX="5" SizeY="4" SizeC="{channel_count}" SizeZ="1" SizeT="1">'
            f"{channels}{references}</Pixels></Image></OME>"
        )
        tifffile.imwrite(
            root / f"part{index}.ome.tiff", np.full((4, 5), index, dtype=np.uint16), description=xml, metadata=None
        )
    return MediaStorage(root=root, entrypoint=Path("part0.ome.tiff"))


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
