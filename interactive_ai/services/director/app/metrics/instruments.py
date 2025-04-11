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

"""Resources and utilities to collect metrics in Geti using OpenTelemetry"""

import logging
from dataclasses import dataclass
from enum import Enum, auto

from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter  # type: ignore[attr-defined]
from opentelemetry.sdk.metrics import MeterProvider  # type: ignore[attr-defined]
from opentelemetry.sdk.metrics.export import (  # type: ignore[attr-defined]
    ConsoleMetricExporter,
    InMemoryMetricReader,
    MetricReader,
    PeriodicExportingMetricReader,
)

from geti_telemetry_tools import DEBUG_METRICS, OTLP_METRICS_RECEIVER, TEST_METRICS
from geti_telemetry_tools.metrics.instruments import BaseInstrumentAttributes
from geti_telemetry_tools.metrics.instruments import MetricName as MetricNameBase

logger = logging.getLogger(__name__)


class MetricName:
    """
    Names and namespaces of the instruments used to collect Geti metrics.
    Namespaces that are used to group affine metrics have the suffix 'BASENAME'.
    """

    MODEL_TRAINING_DURATION = f"{MetricNameBase.MODEL_BASENAME}.training_duration"
    MODEL_TRAINING_JOB_DURATION = f"{MetricNameBase.MODEL_BASENAME}.training_job_duration"


metric_readers: list[MetricReader] = []
in_memory_metric_reader: InMemoryMetricReader | None = None
periodic_metric_reader: PeriodicExportingMetricReader | None = None

# Set up the metric readers based on configuration
if DEBUG_METRICS:  # Enable console exporter
    console_metric_exporter = ConsoleMetricExporter()
    metric_readers.append(PeriodicExportingMetricReader(console_metric_exporter))
    logger.info("Telemetry console metric exporter enabled")
elif TEST_METRICS:  # Enable InMemoryMetricReader
    in_memory_metric_reader = InMemoryMetricReader()
    metric_readers.append(in_memory_metric_reader)
    logger.info("Telemetry in-memory metric reader enabled (for testing purposes)")
if OTLP_METRICS_RECEIVER:  # Enable OTLP exporter
    try:
        otlp_metric_exporter = OTLPMetricExporter(endpoint=OTLP_METRICS_RECEIVER, insecure=True)
        periodic_metric_reader = PeriodicExportingMetricReader(
            exporter=otlp_metric_exporter, export_interval_millis=600000
        )
        metric_readers.append(periodic_metric_reader)
        logger.info("Telemetry OTLP metric exporter enabled. Endpoint: `%s`", OTLP_METRICS_RECEIVER)
    except Exception:
        # Log exception and do not initialize the exporter
        logger.exception(
            "Failed to initialize OTLP metrics exporter to endpoint `%s`.",
            OTLP_METRICS_RECEIVER,
        )
if not DEBUG_METRICS and not OTLP_METRICS_RECEIVER:
    logger.warning("Missing config for exporting telemetry metrics: they will not be exported.")


meter_provider = MeterProvider(
    metric_readers=metric_readers,
)
meter = meter_provider.get_meter("geti.training_job.metrics")

training_duration_counter = meter.create_counter(
    name=MetricName.MODEL_TRAINING_DURATION, unit="seconds", description="Time used for training the model"
)


class TrainingDurationCounterJobStatus(Enum):
    SUCCEEDED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class ModelTrainingDurationAttributes(BaseInstrumentAttributes):
    """
    Attributes for the training duration counters

      - job_id: id of the training job
      - model_architecture: model template id of the models
      - task_type: task type of the model, e.g. CLASSIFICATION
      - job_status: status of the job, e.g. SUCCEEDED, FAILED, or CANCELLED.
      - organization_id: ID of the organization
      - training_job_duration: duration in seconds of the entire training job
      - dataset_size: number of items in the dataset, including all subsets
    """

    job_id: str
    model_architecture: str
    task_type: str
    job_status: str
    organization_id: str
    training_job_duration: float
    dataset_size: int
