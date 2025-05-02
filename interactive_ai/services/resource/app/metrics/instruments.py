# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Resources and utilities to collect metrics in Geti using OpenTelemetry"""

import logging
from dataclasses import dataclass

from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter  # type: ignore[attr-defined]
from opentelemetry.metrics import CallbackOptions, Observation  # type: ignore[attr-defined]
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
from geti_telemetry_tools.metrics.utils import if_elected_publisher_for_metric
from iai_core_py.repos.leader_election_repo import LeaderElectionRepo
from iai_core_py.repos.metrics_reporting_model_storage_repo import MetricsReportingModelStorageRepo
from iai_core_py.repos.metrics_reporting_project_repo import MetricsReportingProjectRepo

logger = logging.getLogger(__name__)


class MetricName:
    """
    Names and namespaces of the instruments used to collect Geti metrics.
    Namespaces that are used to group affine metrics have the suffix 'BASENAME'.
    """

    PROJECT_TOTAL_GAUGE = f"{MetricNameBase.PROJECTS_BASENAME}.total_gauge"

    MODEL_TOTAL_GAUGE = f"{MetricNameBase.MODEL_BASENAME}.total_gauge"
    MODELS_PER_TASK_TYPE = f"{MODEL_TOTAL_GAUGE}.task_type"
    MODELS_PER_ARCH = f"{MODEL_TOTAL_GAUGE}.architecture"


metric_readers: list[MetricReader] = []
in_memory_metric_reader: InMemoryMetricReader | None = None

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
            exporter=otlp_metric_exporter,
            export_interval_millis=3600000,  # once an hour
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
meter = meter_provider.get_meter("geti.resource_microservice.metrics")


@if_elected_publisher_for_metric(
    metric_name=MetricName.PROJECT_TOTAL_GAUGE, validity_in_seconds=3540, election_manager_cls=LeaderElectionRepo
)
def total_projects_per_type(options: CallbackOptions) -> list[Observation]:  # noqa: ARG001
    """
    Report the total number of projects per project type
    """

    metrics_reporting_project_repo = MetricsReportingProjectRepo()
    project_metrics = metrics_reporting_project_repo.get_total_number_of_projects_per_project_type()
    logger.info("Reporting total projects per project type: %s", project_metrics)

    return [
        Observation(
            value=project_metrics[project_type],
            attributes=ProjectsTotalGaugeAttributes(project_type=project_type).to_dict(),
        )
        for project_type in project_metrics
    ]


projects_total_per_type_gauge = meter.create_observable_gauge(
    name=MetricName.PROJECT_TOTAL_GAUGE,
    description="Number of existing projects",
    unit="projects",
    callbacks=[total_projects_per_type],
)


@if_elected_publisher_for_metric(
    metric_name=MetricName.MODELS_PER_ARCH, validity_in_seconds=3540, election_manager_cls=LeaderElectionRepo
)
def total_models_per_arch_callback(options: CallbackOptions) -> list[Observation]:  # noqa: ARG001
    """
    Report the total number of models per architecture
    """

    metrics_reporting_model_storage_repo = MetricsReportingModelStorageRepo()
    model_metrics = metrics_reporting_model_storage_repo.get_total_number_of_models_per_arch()
    logger.info("Reporting total models per architecture metrics now: %s", model_metrics)

    return [
        Observation(
            value=model_metrics[model_architecture],
            attributes=ModelPerArchTotalGaugeAttributes(model_architecture=model_architecture).to_dict(),
        )
        for model_architecture in model_metrics
    ]


models_total_per_arch_gauge = meter.create_observable_gauge(
    name=MetricName.MODELS_PER_ARCH,
    description="Number of models per architecture",
    unit="models",
    callbacks=[total_models_per_arch_callback],
)


@if_elected_publisher_for_metric(
    metric_name=MetricName.MODELS_PER_TASK_TYPE, validity_in_seconds=3540, election_manager_cls=LeaderElectionRepo
)
def total_models_per_task_type_callback(options: CallbackOptions) -> list[Observation]:  # noqa: ARG001
    """
    Report the total number of models per task type
    """

    metrics_reporting_model_storage_repo = MetricsReportingModelStorageRepo()
    model_metrics = metrics_reporting_model_storage_repo.get_total_number_of_models_per_task_type()
    logger.info("Reporting total models per task type metrics now: %s", model_metrics)

    return [
        Observation(
            value=model_metrics[task_type],
            attributes=ModelPerTypeTotalGaugeAttributes(task_type=task_type).to_dict(),
        )
        for task_type in model_metrics
    ]


models_total_per_task_type_gauge = meter.create_observable_gauge(
    name=MetricName.MODELS_PER_TASK_TYPE,
    description="Number of models per task type",
    unit="models",
    callbacks=[total_models_per_task_type_callback],
)


@dataclass
class ProjectsTotalGaugeAttributes(BaseInstrumentAttributes):
    """
    Attributes for the projects total gauge

      - project_type: Project type of the total number of projects
    """

    project_type: str


@dataclass
class ModelPerArchTotalGaugeAttributes(BaseInstrumentAttributes):
    """
    Attributes for the total models per architecture total gauge

      - model_architecture: model template id of the models
    """

    model_architecture: str


@dataclass
class ModelPerTypeTotalGaugeAttributes(BaseInstrumentAttributes):
    """
    Attributes for the total models per task type total gauge

      - task_type: task type of the models
    """

    task_type: str


def initialize_metrics() -> None:
    """
    Ensure the metrics module is loaded and async gauges are initialized.
    """
