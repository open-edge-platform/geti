# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module defines a command to prepare MLFlow Experiment directory in the S3 bucket."""

import io
import json
import logging
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import numpy as np
import pyarrow as pa
from geti_telemetry_tools import unified_tracing
from geti_types import ProjectIdentifier
from iai_core.adapters.binary_interpreters import RAWBinaryInterpreter
from iai_core.adapters.model_adapter import DataSource
from iai_core.configuration.elements.configurable_parameters import ConfigurableParameters
from iai_core.configuration.helper import create
from iai_core.entities.label_schema import LabelSchema
from iai_core.entities.metrics import CurveMetric, LineChartInfo, MetricsGroup, Performance, ScoreMetric
from iai_core.entities.model import Model, ModelFormat, ModelOptimizationType, ModelStatus
from iai_core.repos.model_repo import ModelRepo
from iai_core.repos.project_repo import ProjectRepo
from pandas import DataFrame

# NOTE: workaround for CVS-156400 -> the following imports are needed for the workaround
from jobs_common.tasks.utils.progress import report_progress
from jobs_common.tasks.utils.secrets import JobMetadata
from jobs_common_extras.evaluation.utils.helpers import is_model_legacy_otx_version
from jobs_common_extras.mlflow.adapters.definitions import (
    BASE_FRAMEWORK_KEY,
    CONFIG_JSON_KEY,
    ONNX_KEY,
    OPENVINO_BIN_KEY,
    OPENVINO_XML_KEY,
    ClsSubTaskType,
    MLFlowLifecycleStage,
    MLFlowRunStatus,
)
from jobs_common_extras.mlflow.adapters.metrics_mapper import PerformanceDeserializer
from jobs_common_extras.mlflow.repos.binary_repo import MLFlowExperimentBinaryRepo

logger = logging.getLogger(__name__)


__all__ = ["GetiOTXInterfaceAdapter", "MLFlowLifecycleStage", "MLFlowRunStatus"]

UNAVAILABLE_PERFORMANCE_WARNING = (
    "Performance metrics are not available for the trained model due to an internal error; please contact support."
)


def _check_bytes_type(data: bytes | np.ndarray) -> bytes:
    if not isinstance(data, bytes):
        raise TypeError
    return data


class GetiOTXInterfaceAdapter:
    def __init__(
        self,
        project_identifier: ProjectIdentifier,
        job_metadata: JobMetadata,
    ):
        super().__init__()
        self.project_repo = ProjectRepo()
        self.binary_repo = MLFlowExperimentBinaryRepo(project_identifier)
        self.project_identifier = project_identifier
        self.job_metadata = job_metadata

    @property
    def dst_path_prefix(self) -> str:
        """String path prefix for all files.

        :return: `jobs/<job-id>`
        """
        return os.path.join("jobs", str(self.job_metadata.id))

    @unified_tracing
    def push_placeholders(self) -> None:
        """Push empty placeholder files to create the directory structure in a S3 file system.

        This function will create the following directory structure under
        `mlflowexperiments/organizations/<org-id>/workspaces/<ws-id>/projects/<proj-id>/jobs/<job-id>`

        - <root>/inputs
        - <root>/live_metrics
        - <root>/outputs/models
        - <root>/outputs/exportable_codes
        - <root>/outputs/configurations
        - <root>/outputs/logs
        """

        with TemporaryDirectory() as root:
            for dir in ["inputs", "live_metrics"]:
                prefix = os.path.join(root, self.dst_path_prefix, dir)
                os.makedirs(prefix)
                with open(os.path.join(prefix, ".placeholder"), "w") as fp:
                    fp.write("")

            for dir in ["models", "exportable_codes", "configurations", "logs"]:
                prefix = os.path.join(root, self.dst_path_prefix, "outputs", dir)
                os.makedirs(prefix)
                with open(os.path.join(prefix, ".placeholder"), "w") as fp:
                    fp.write("")

            # NOTE: This is a workaround to construct
            # jobs/<job-id>/... directory structure in the S3 bucket.
            # It is because iai-core binary repo `save()` function only allows a filename, not a filepath.
            self.binary_repo.save_group(source_directory=root)

    @unified_tracing
    def push_metadata(self) -> None:
        """Push empty metadata files to the root directory.

        It will create the following metadata files: metadata.json, project.json, run_info.json.
        """

        with TemporaryDirectory() as root:
            prefix = os.path.join(root, self.dst_path_prefix)
            os.makedirs(prefix)

            with open(os.path.join(prefix, "metadata.json"), "w") as fp:
                json.dump(obj=self._create_metadata_json(), fp=fp)

            with open(os.path.join(prefix, "project.json"), "w") as fp:
                json.dump(obj=self._create_project_json(), fp=fp)

            with open(os.path.join(prefix, "run_info.json"), "w") as fp:
                json.dump(obj=self._create_run_info_json(), fp=fp)

            prefix_live_metrics = os.path.join(prefix, "live_metrics")
            os.makedirs(prefix_live_metrics)
            with open(os.path.join(prefix_live_metrics, "progress.json"), "w") as fp:
                json.dump(obj=self._create_progress_json(), fp=fp)

            # NOTE: This is a workaround to construct
            # jobs/<job-id>/... directory structure in the S3 bucket.
            # It is because iai-core binary repo `save()` function only allows a filename, not a filepath.
            self.binary_repo.save_group(source_directory=root)

    @unified_tracing
    def push_input_model(self, model: Model) -> None:
        """Push the model artifacts to the inputs directory.

        :param model: Model to use as a checkpoint to reload weights for training.
            If the model has no trained weights, no binary file is uploaded,
            then the model will be trained from scratch.
        """
        model_keys = [BASE_FRAMEWORK_KEY]
        model_alias = {
            BASE_FRAMEWORK_KEY: "model.pth",
        }
        if model.optimization_type == ModelOptimizationType.MO:
            model_keys = [OPENVINO_XML_KEY, OPENVINO_BIN_KEY]
            if is_model_legacy_otx_version(model):
                model_keys.extend(
                    [
                        "confidence_threshold",
                        "tile_classifier.xml",
                        "tile_classifier.bin",
                    ]
                )

        if not model.has_trained_weights() or model_keys[0] not in model.model_adapters:
            logger.warning(
                "Model with ID '%s' has no trained model weights binary file.",
                model.id_,
            )
            return

        model_repo = ModelRepo(model.model_storage_identifier)

        for model_key in model_keys:
            model_adapter = model.model_adapters.get(model_key)
            if not model_adapter:
                logger.info("Model adapter with key '%s' is not found. Ignoring.", model_key)
                continue

            data_source = model_adapter.data_source
            if not isinstance(data_source, DataSource):
                raise TypeError(
                    "Model with ID '%s' should have DataSource for the given model adapter key %s. But it has %s",
                    model.id_,
                    model_key,
                    str(type(model_adapter)),
                )

            self.binary_repo.copy_from(
                model_binary_repo=model_repo.binary_repo,
                src_filename=data_source.binary_filename,
                dst_filepath=os.path.join(
                    self.dst_path_prefix,
                    "inputs",
                    model_alias.get(model_key, model_key),
                ),
            )

    @unified_tracing
    def push_input_dataset(self, shard_file_local_path: Path) -> None:
        """Push the dataset shard file to the inputs directory.

        :param shard_file_local_path: Local disk path of shard file
        """
        with TemporaryDirectory() as root:
            prefix = os.path.join(root, self.dst_path_prefix, "inputs")
            os.makedirs(prefix)

            local_dst = os.path.join(prefix, shard_file_local_path.name)
            os.symlink(src=shard_file_local_path, dst=local_dst)

            # NOTE: This is a workaround to construct
            # jobs/<job-id>/... directory structure in the S3 bucket.
            # It is because iai-core binary repo `save()` function only allows a filename, not a filepath.
            self.binary_repo.save_group(source_directory=root)

    @unified_tracing
    def push_input_configuration(
        self,
        model_template_id: str,
        hyper_parameters: dict[str, Any],
        export_parameters: dict[str, str] | list[dict[str, str]],
        optimization_type: ModelOptimizationType = ModelOptimizationType.NONE,
        label_schema: LabelSchema | None = None,
    ) -> None:
        """Push the configuration file to the inputs directory.

        :param model_template_id: ID of model template for this job (obtained from CRD)
        :param hyper_parameters: Hyperparameters for this job (obtained from CRD)
        :param export_parameters: Exportparameters for this job (obtained from CRD)
        :param optimization_type: Model optimization type enum. It is only used for the model optimize job.
        :param sub_task: Sub task type used to distinguish classification tasks.
            If `None`, do not add this value to the configuration file.
        """
        config_dict: dict[str, Any] = {}

        config_dict["job_type"] = self.job_metadata.type
        config_dict["model_template_id"] = model_template_id
        config_dict["hyperparameters"] = hyper_parameters
        config_dict["export_parameters"] = export_parameters
        config_dict["optimization_type"] = optimization_type.name

        if label_schema:
            config_dict["sub_task_type"] = ClsSubTaskType.create_from_label_schema(label_schema=label_schema).value

        with TemporaryDirectory() as root:
            prefix = os.path.join(root, self.dst_path_prefix, "inputs")
            os.makedirs(prefix)

            with open(os.path.join(prefix, "config.json"), "w") as fp:
                json.dump(obj=config_dict, fp=fp)

            # NOTE: This is a workaround to construct
            # jobs/<job-id>/... directory structure in the S3 bucket.
            # It is because iai-core binary repo `save()` function only allows a filename, not a filepath.
            self.binary_repo.save_group(source_directory=root)

    @unified_tracing
    def update_output_models(self, models_to_update: list[Model]) -> None:
        """Update output model binary data from the outputs directory.

        If succeeds, it updates the given models' model adapters with
        the output model binary data pulled from the outputs directory.
        In addition, it updates the model status as `ModelStatus.SUCCESS` as well.

        :param models_to_update: Models to update output model binary data.
            This function will inplace their data.
        """
        for model in models_to_update:
            precision = next(iter(model.precision)).name.lower()
            xai_suffix = "xai" if model.has_xai_head else "non-xai"

            if model.model_format == ModelFormat.BASE_FRAMEWORK:
                self._update_base_model(model, precision, xai_suffix)

            elif model.model_format == ModelFormat.OPENVINO:
                self._update_ov_model(model, precision, xai_suffix)

            elif model.model_format == ModelFormat.ONNX:
                self._update_onnx_model(model, precision, xai_suffix)

    @unified_tracing
    def update_output_model_for_optimize(
        self,
        model: Model,
    ) -> None:
        """Pull output model binary data from the outputs directory.

        This is dedicated for "optimize" only.
        It is inevitable because "optimize" workflow has really dirty branching.

        :param model: it should have OpenVINO IR with INT8 precision
        """
        # Update model_to_optimize
        self._update_ov_model(
            model=model,
            precision="int8-pot",
            xai_suffix="non-xai",
        )

    @unified_tracing
    def _update_model(self, model: Model, key: str, filepath: str, is_exportable_code: bool = False) -> None:
        try:
            model_repo = ModelRepo(model.model_storage_identifier)
            binary_filename = self.binary_repo.copy_to(model_binary_repo=model_repo.binary_repo, src_filepath=filepath)
            data_source = DataSource(repository=model_repo.binary_repo, binary_filename=binary_filename)

            if is_exportable_code:
                model.exportable_code = data_source  # type: ignore[assignment]
            else:
                model.set_data(
                    key=key,
                    data=data_source,
                    skip_deletion=False,
                )
            # TODO move out of the loop
            logger.info(
                "Model with ID '%s' update its weights %s with binary file %s: Model status after the update: %s.",
                model.id_,
                key,
                filepath,
                model.model_status.name,
            )
            # NOTE: If one of consecutive _update_model() calls goes into ModelStatus.FAILED,
            # that model cannot be `ModelStatus.SUCCESS` although another _update_model() call is succeeded.
            if model.model_status != ModelStatus.FAILED:
                model.model_status = ModelStatus.SUCCESS
        except Exception:
            logger.exception(
                f"Failed to pull the trained weights binary for model with ID '{model.id_}' from the MLFlow experiment"
            )
            model.model_status = ModelStatus.FAILED
            raise  # TODO handle

    @unified_tracing
    def _update_onnx_model(self, model: Model, precision: str, xai_suffix: str) -> None:
        model_prefix = os.path.join(self.dst_path_prefix, "outputs", "models")

        self._update_model(
            model=model,
            key=ONNX_KEY,
            filepath=os.path.join(model_prefix, f"model_{precision}_{xai_suffix}.onnx"),
        )

    @unified_tracing
    def _update_ov_model(self, model: Model, precision: str, xai_suffix: str):
        model_prefix = os.path.join(self.dst_path_prefix, "outputs", "models")
        exportable_code_prefix = os.path.join(self.dst_path_prefix, "outputs", "exportable_codes")

        # Update OpenVINO XML
        self._update_model(
            model=model,
            key=OPENVINO_XML_KEY,
            filepath=os.path.join(model_prefix, f"model_{precision}_{xai_suffix}.xml"),
        )
        # Update OpenVINO BIN
        self._update_model(
            model=model,
            key=OPENVINO_BIN_KEY,
            filepath=os.path.join(model_prefix, f"model_{precision}_{xai_suffix}.bin"),
        )
        # Update Exportable code
        self._update_model(
            model=model,
            key="",
            filepath=os.path.join(
                exportable_code_prefix,
                f"exportable-code_{precision}_{xai_suffix}.whl",
            ),
            is_exportable_code=True,
        )

        # Update detection model only artifacts
        self._update_detection_model(model=model, precision=precision, xai_suffix=xai_suffix)

    @unified_tracing
    def _update_detection_model(self, model: Model, precision: str, xai_suffix: str):
        """Update model artifacts required only for detection models."""

        model_prefix = os.path.join(self.dst_path_prefix, "outputs", "models")
        # NOTE: Below is only for detection task models & tiling
        config_prefix = os.path.join(self.dst_path_prefix, "outputs", "configurations")
        config_fname = os.path.join(
            config_prefix,
            f"config_{precision}_{xai_suffix}.json",
        )

        if self.binary_repo.exists(filename=config_fname):
            self._update_model(
                model=model,
                key=CONFIG_JSON_KEY,
                filepath=config_fname,
            )

        tile_classifier_fnames = [
            os.path.join(model_prefix, f"tile-classifier_{precision}_{xai_suffix}.xml"),
            os.path.join(model_prefix, f"tile-classifier_{precision}_{xai_suffix}.bin"),
        ]
        tile_classifier_keys = [
            "tile_classifier.xml",
            "tile_classifier.bin",
        ]
        for tile_classifier_fname, tile_classifier_key in zip(tile_classifier_fnames, tile_classifier_keys):
            if not self.binary_repo.exists(filename=tile_classifier_fname):
                continue

            self._update_model(
                model=model,
                key=tile_classifier_key,
                filepath=tile_classifier_fname,
            )

    @unified_tracing
    def _update_base_model(self, model: Model, precision: str, xai_suffix: str) -> None:
        model_prefix = os.path.join(self.dst_path_prefix, "outputs", "models")

        self._update_model(
            model=model,
            key=BASE_FRAMEWORK_KEY,
            filepath=os.path.join(model_prefix, f"model_{precision}_{xai_suffix}.pth"),
        )

    @unified_tracing
    def pull_output_configuration(self) -> ConfigurableParameters:
        data = _check_bytes_type(
            self.binary_repo.get_by_filename(
                filename=os.path.join(
                    self.dst_path_prefix,
                    "outputs",
                    "configurations",
                    "optimized-config.json",
                ),
                binary_interpreter=RAWBinaryInterpreter(),
            )
        )
        return create(input_config=json.loads(data))

    @unified_tracing
    def pull_metrics(self) -> Performance | None:
        """Pull training performance metrics from the MLFlow output artifacts.

        :return: Performance object, or None if it cannot be loaded.
        """

        # Metrics can be found either in outputs/models/performance.pickle or live_metrics/metrics.arrow
        model_prefix = os.path.join(self.dst_path_prefix, "outputs", "models")
        performance_filepath = os.path.join(model_prefix, "performance-json.bin")
        live_metrics_prefix = os.path.join(self.dst_path_prefix, "live_metrics")
        metrics_filepath = os.path.join(live_metrics_prefix, "metrics.arrow")

        performance: Performance | None = None
        if self.binary_repo.exists(performance_filepath):
            logger.info("Reading performance metrics from %s", performance_filepath)
            try:
                data = self.binary_repo.get_by_filename(
                    filename=performance_filepath,
                    binary_interpreter=RAWBinaryInterpreter(),
                )
                performance = PerformanceDeserializer.backward(json.loads(data.decode()))
            except Exception:
                logger.exception(f"Failed to extract performance metrics from {performance_filepath}")
        elif self.binary_repo.exists(metrics_filepath):
            logger.info("Reading performance metrics from %s", metrics_filepath)
            try:
                obj = self.binary_repo.storage_client.client.get_object(  # type: ignore
                    bucket_name=self.binary_repo.storage_client.bucket_name,  # type: ignore
                    object_name=os.path.join(
                        self.binary_repo.storage_client.object_name_base,
                        metrics_filepath,
                    ),  # type: ignore
                )
                table = pa.ipc.RecordBatchFileReader(io.BytesIO(obj.data)).read_all()
                data_frame = table.to_pandas()
                performance = self._create_performance_from_arrow(data_frame)
            except Exception:
                logger.exception(f"Failed to extract performance metrics from {metrics_filepath}")
        else:
            logger.error(
                "Cannot find any file to extract performance metrics; both `%s` and `%s` are missing.",
                performance_filepath,
                metrics_filepath,
            )

        if performance is None:
            report_progress(warning=UNAVAILABLE_PERFORMANCE_WARNING)

        return performance

    def pull_progress(self) -> float | None:
        """Pull progress from the JSON file.

        :return: If succeed, return a tuple of training stage and progress
            Otherwise, return `None`.
        """
        try:
            filename = os.path.join(self.dst_path_prefix, "live_metrics", "progress.json")
            data = _check_bytes_type(
                self.binary_repo.get_by_filename(
                    filename=filename,
                    binary_interpreter=RAWBinaryInterpreter(),
                )
            )
            progress_dict = json.loads(data)
            return float(progress_dict["progress"])

        except Exception as e:
            logger.warning(
                "Failed to pull progress. This can be caused by various problems "
                "such as no JSON file or data race. error='%s'",
                e,
            )
            return None

    def _create_metadata_json(self) -> dict[str, str | None]:
        return {
            "job_id": str(self.job_metadata.id),
            "job_type": self.job_metadata.type,
            "start_time": self.job_metadata.start_time.isoformat(),
            "end_time": None,
        }

    def _create_project_json(self) -> dict[str, str]:
        project = self.project_repo.get_by_id(id_=self.project_identifier.project_id)
        return {
            "id": str(project.id_),
            "name": project.name,
            "creator_id": project.creator_id,
            "description": project.description,
            "creation_date": project.creation_date.isoformat(),
            "workspace_id": project.workspace_id,
            "organization_id": self.binary_repo.organization_id,
        }

    def _create_run_info_json(self) -> dict[str, str | None]:
        return {
            "run_uuid": str(self.job_metadata.id),
            "job_name": self.job_metadata.name,
            "author": str(self.job_metadata.author),
            "status": MLFlowRunStatus.SCHEDULED,
            "start_time": self.job_metadata.start_time.isoformat(),
            "end_time": None,
            "lifecycle_stage": MLFlowLifecycleStage.ACTIVE,
        }

    def _create_progress_json(self) -> dict[str, str | float]:
        return {
            "progress": 0.0,
        }

    def _create_performance_from_arrow(self, data_frame: DataFrame) -> Performance:
        grouped = data_frame.groupby("key")

        dashboard_metrics = []
        for name, group in grouped:
            ys = group["value"].tolist()
            xs = [float(x) for x in range(1, len(ys) + 1)]
            metric = CurveMetric(name=name, ys=ys, xs=xs)

            info = LineChartInfo(name=name, x_axis_label="Timestamp", y_axis_label=name)

            dashboard_metrics.append(MetricsGroup(metrics=[metric], visualization_info=info))
        return Performance(
            score=ScoreMetric(name="Model accuracy", value=0.5),
            dashboard_metrics=dashboard_metrics,
        )

    @unified_tracing
    def clean(self) -> None:
        """Remove all files under this directory.
        `mlflowexperiments/organizations/<org-id>/workspaces/<ws-id>/projects/<proj-id>/jobs/<job-id>`
        """
        self.binary_repo.delete_all_under_job_dir(job_id=self.job_metadata.id)
