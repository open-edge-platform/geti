# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Resources and utilities to collect metrics in Geti using OpenTelemetry"""

import abc
import logging
from dataclasses import asdict, dataclass
from typing import final

from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter  # type: ignore[attr-defined]
from opentelemetry.metrics import set_meter_provider  # type: ignore[attr-defined]
from opentelemetry.sdk.metrics import MeterProvider  # type: ignore[attr-defined]
from opentelemetry.sdk.metrics.export import (  # type: ignore[attr-defined]
    ConsoleMetricExporter,
    InMemoryMetricReader,
    MetricExporter,
    MetricReader,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.metrics.view import ExplicitBucketHistogramAggregation, View  # type: ignore[attr-defined]

from geti_telemetry_tools import DEBUG_METRICS, OTLP_METRICS_RECEIVER, TEST_METRICS

__all__ = [
    "EmptyInstrumentAttributes",
    "MetricName",
    "ModelExportsCounterAttributes",
    "images_resolution_histogram",
    "in_memory_metric_reader",
    "model_exports_counter",
    "videos_frames_histogram",
    "videos_resolution_histogram",
]

logger = logging.getLogger(__name__)


class MetricName:
    """
    Names and namespaces of the instruments used to collect Geti metrics.
    Namespaces that are used to group affine metrics have the suffix 'BASENAME'.
    """

    # geti
    GETI_BASENAME = "geti"
    # geti.<domain>
    APPLICATION_BASENAME = f"{GETI_BASENAME}.application"
    DOCUMENTATION_BASENAME = f"{GETI_BASENAME}.documentation"
    PLATFORM_BASENAME = f"{GETI_BASENAME}.platform"
    USERS_BASENAME = f"{GETI_BASENAME}.users"
    # geti.application.<base-entity>
    MEDIA_BASENAME = f"{APPLICATION_BASENAME}.media"
    MODEL_BASENAME = f"{APPLICATION_BASENAME}.models"
    PROJECTS_BASENAME = f"{APPLICATION_BASENAME}.projects"
    # geti.application.media.<property>
    MEDIA_SIZE_BASENAME = f"{MEDIA_BASENAME}.size"
    # geti.application.media.size.<media-type>
    IMAGES_SIZE_BASENAME = f"{MEDIA_SIZE_BASENAME}.images"
    VIDEOS_SIZE_BASENAME = f"{MEDIA_SIZE_BASENAME}.videos"
    # geti.application.media.size.images.<dimension>
    IMAGES_RESOLUTION = f"{IMAGES_SIZE_BASENAME}.resolution"
    # geti.application.media.size.videos.<dimension>
    VIDEOS_RESOLUTION = f"{VIDEOS_SIZE_BASENAME}.resolution"
    VIDEOS_FRAMES = f"{VIDEOS_SIZE_BASENAME}.frames"
    # geti.application.models.<workflow>
    MODEL_EXPORTS_BASENAME = f"{MODEL_BASENAME}.exports"
    # geti.application.models.exports.<property>
    MODEL_EXPORTS_COUNT = f"{MODEL_EXPORTS_BASENAME}.count"


metric_readers: list[MetricReader] = []
in_memory_metric_reader: InMemoryMetricReader | None = None

metric_exporter: MetricExporter
# Set up the metric readers based on configuration
if DEBUG_METRICS:  # Enable console exporter
    metric_exporter = ConsoleMetricExporter()
    metric_readers.append(PeriodicExportingMetricReader(metric_exporter))
    logger.info("Telemetry console metric exporter enabled")
elif TEST_METRICS:  # Enable InMemoryMetricReader
    in_memory_metric_reader = InMemoryMetricReader()
    metric_readers.append(in_memory_metric_reader)
    logger.info("Telemetry in-memory metric reader enabled (for testing purposes)")
if OTLP_METRICS_RECEIVER:  # Enable OTLP exporter
    try:
        metric_exporter = OTLPMetricExporter(endpoint=OTLP_METRICS_RECEIVER, insecure=True)
        metric_readers.append(PeriodicExportingMetricReader(metric_exporter))
        logger.info("Telemetry OTLP metric exporter enabled. Endpoint: `%s`", OTLP_METRICS_RECEIVER)
    except Exception:
        # Log exception and do not initialize the exporter
        logger.exception(
            "Failed to initialize OTLP metrics exporter to endpoint `%s`.",
            OTLP_METRICS_RECEIVER,
        )
if not DEBUG_METRICS and not OTLP_METRICS_RECEIVER:
    logger.warning("Missing config for exporting telemetry metrics: they will not be exported.")


images_resolution_view = View(
    instrument_name=MetricName.IMAGES_RESOLUTION,
    aggregation=ExplicitBucketHistogramAggregation(boundaries=(1, 10, 50)),
)

# buckets are designed so to have 360p, 480p, 720p, 1080p, 2160p roughly in their middle
videos_resolution_view = View(
    instrument_name=MetricName.VIDEOS_RESOLUTION,
    aggregation=ExplicitBucketHistogramAggregation(boundaries=(0.25, 0.6, 1.5, 5)),
)

videos_frames_view = View(
    instrument_name=MetricName.VIDEOS_FRAMES,
    aggregation=ExplicitBucketHistogramAggregation(boundaries=(1000, 10_000, 100_000)),
)

meter_provider = MeterProvider(
    metric_readers=metric_readers, views=[images_resolution_view, videos_resolution_view, videos_frames_view]
)
set_meter_provider(meter_provider)
meter = meter_provider.get_meter("geti.telemetry")

images_resolution_histogram = meter.create_histogram(
    name=MetricName.IMAGES_RESOLUTION,
    description="Resolution of the uploaded images",
    unit="MP",
)

videos_frames_histogram = meter.create_histogram(
    name=MetricName.VIDEOS_FRAMES,
    description="Number of frames of the uploaded videos",
    unit="1",
)

videos_resolution_histogram = meter.create_histogram(
    name=MetricName.VIDEOS_RESOLUTION,
    description="Resolution of the uploaded videos",
    unit="MP",
)

model_exports_counter = meter.create_counter(
    name=MetricName.MODEL_EXPORTS_COUNT,
    description="Number of exported models",
    unit="1",
)


@dataclass
class BaseInstrumentAttributes(metaclass=abc.ABCMeta):
    """Base class for instrument attributes"""

    def to_dict(self) -> dict[str, str | float]:
        """
        Get a dict representation of the attributes.

        In practice, this method is typically used to get the dictionary
        of attributes to pass to the instrument 'add/record' method.
        Concrete implementations of this class may choose either a 1:1
        representation of the dataclass attributes (no override) or a
        custom one (by overriding this method).
        """

        return asdict(self)


@final
@dataclass
class EmptyInstrumentAttributes(BaseInstrumentAttributes):
    """Placeholder for instruments that do not specify attributes"""

    def to_dict(self) -> dict[str, str | float]:
        return {}


@dataclass
class ModelExportsCounterAttributes(BaseInstrumentAttributes):
    """
    Attributes for the model exports counter

      - workspace_id: ID of the workspace containing the project
      - project_id: ID of the project containing the exported model
      - model_architecture: Type of model (e.g. SSD)
      - training_version: Training revision of the exported model
      - format: Format of the exported model (e.g. OPENVINO)
      - precision: Precision of the exported model (e.g. FP32)
    """

    model_architecture: str
    format: str
    precision: str
