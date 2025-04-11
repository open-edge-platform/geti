# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from functools import cache
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
from mlflow.entities import Dataset, DatasetInput, Experiment, LifecycleStage, Metric, RunData, RunInfo, RunInputs
from pydantic import BaseModel as _BaseModel

from mlflow_geti_store.s3_object_storage_client import S3ObjectStorageClient
from mlflow_geti_store.utils import ARTIFACT_ROOT_URI_PREFIX, PYARROW_SCHEMA, TimeStampMapper

logger = logging.getLogger("mlflow")


class BaseModel(_BaseModel):
    class Config:
        arbitrary_types_allowed = True


class ProjectModel(BaseModel):
    project_id: str
    name: str
    creator_id: str
    description: str
    creation_date: datetime
    workspace_id: str
    organization_id: str

    @classmethod
    @cache
    def from_object_storage(cls, client: S3ObjectStorageClient) -> ProjectModel:
        relative_path = Path("project.json")
        response = None

        try:
            response = client.get_by_filename(relative_path)
            inputs = json.loads(response.data)
            msg = f"Received project.json={inputs}"
            logger.info(msg)

            return ProjectModel(
                project_id=inputs["id"],
                name=inputs["name"],
                creator_id=inputs["creator_id"],
                description=inputs["description"],
                creation_date=datetime.fromisoformat(inputs["creation_date"]),
                workspace_id=inputs["workspace_id"],
                organization_id=inputs["organization_id"],
            )
        finally:
            if response:
                response.close()
                response.release_conn()

    def to_mlflow(self) -> Experiment:
        suffix = os.path.join(
            "organizations",
            self.organization_id,
            "workspaces",
            self.workspace_id,
            "projects",
            self.project_id,
        )
        artifact_location = ARTIFACT_ROOT_URI_PREFIX + suffix

        return Experiment(
            experiment_id=self.project_id,
            name=self.name,
            artifact_location=artifact_location,
            lifecycle_stage=LifecycleStage.ACTIVE,
            creation_time=TimeStampMapper.forward(self.creation_date),
            last_update_time=None,
        )


class RunInfoModel(BaseModel):
    run_uuid: str
    job_name: str
    author: str
    status: str
    start_time: datetime
    end_time: datetime | None
    lifecycle_stage: str

    @classmethod
    def from_object_storage(cls, client: S3ObjectStorageClient) -> RunInfoModel:
        relative_path = Path("run_info.json")
        response = None

        try:
            response = client.get_by_filename(relative_path)
            inputs = json.loads(response.data)
            msg = f"Received run_info.json={inputs}"
            logger.info(msg)

            return RunInfoModel(
                run_uuid=inputs["run_uuid"],
                job_name=inputs["job_name"],
                author=inputs["author"],
                status=inputs["status"],
                start_time=datetime.fromisoformat(inputs["start_time"]),
                end_time=datetime.fromisoformat(inputs["end_time"]) if inputs["end_time"] else None,
                lifecycle_stage=inputs["lifecycle_stage"],
            )
        finally:
            if response:
                response.close()
                response.release_conn()

    def to_object_storage(self, client: S3ObjectStorageClient) -> None:
        relative_path = Path("run_info.json")
        to_json_dict = {
            "run_uuid": self.run_uuid,
            "job_name": self.job_name,
            "author": self.author,
            "status": self.status,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "lifecycle_stage": self.lifecycle_stage,
        }
        input_bytes = json.dumps(to_json_dict).encode("utf-8")
        client.save_file_from_bytes(
            relative_path=relative_path,
            input_bytes=input_bytes,
            overwrite=True,
        )

    def to_mlflow(self, project_model: ProjectModel) -> RunInfo:
        suffix = os.path.join(
            "organizations",
            project_model.organization_id,
            "workspaces",
            project_model.workspace_id,
            "projects",
            project_model.project_id,
            "jobs",
            self.run_uuid,
        )
        artifact_location = ARTIFACT_ROOT_URI_PREFIX + suffix

        run_name = f"{self.job_name}_{self.run_uuid}"

        if self.lifecycle_stage.lower() == "active":
            lifecycle_stage = LifecycleStage.ACTIVE
        elif self.lifecycle_stage.lower() == "deleted":
            lifecycle_stage = LifecycleStage.DELETED
        else:
            raise ValueError(f"Unrecognized lifecycle_stage value: {self.lifecycle_stage}")

        return RunInfo(
            run_uuid=self.run_uuid,
            experiment_id=project_model.project_id,
            user_id=self.author,
            # status should be a string.
            # See https://github.com/mlflow/mlflow/blob/6ca72469b289e77acc2f1201ca39237fc025c090/mlflow/entities/run_info.py#L151
            status=self.status,
            start_time=TimeStampMapper.forward(self.start_time),
            end_time=TimeStampMapper.forward(self.end_time) if self.end_time else None,
            lifecycle_stage=lifecycle_stage,
            artifact_uri=artifact_location,
            run_name=run_name,
        )


class LatestMetricsModel(BaseModel):
    metrics: list[Metric]

    @classmethod
    def from_object_storage(cls, client: S3ObjectStorageClient) -> LatestMetricsModel:
        if not client.check_live_metrics_file_exists():
            return LatestMetricsModel(metrics=[])

        with (
            client.open_live_metrics_file() as fp,
            pa.ipc.open_file(source=fp, options=pa.ipc.IpcReadOptions(use_threads=False)) as reader,
        ):
            table = reader.read_all()
            latest = table.group_by("key", use_threads=False).aggregate(
                [
                    ("value", "last"),
                    ("timestamp", "last"),
                    ("step", "last"),
                ]
            )
            metrics = [
                Metric(
                    key=item["key"],
                    value=item["value_last"],
                    timestamp=TimeStampMapper.forward(item["timestamp_last"]),
                    step=item["step_last"],
                )
                for item in latest.to_pylist()
            ]

        return LatestMetricsModel(metrics=metrics)

    def to_mlflow(self) -> list[Metric]:
        return self.metrics


class MetricsHistoryModel(BaseModel):
    metrics: list[Metric]

    @classmethod
    def from_object_storage(
        cls, client: S3ObjectStorageClient, metric_key: str, offset: int, limit: int
    ) -> MetricsHistoryModel:
        if not client.check_live_metrics_file_exists():
            return MetricsHistoryModel(metrics=[])

        with (
            client.open_live_metrics_file() as fp,
            pa.ipc.open_file(source=fp, options=pa.ipc.IpcReadOptions(use_threads=False)) as reader,
        ):
            table = reader.read_all()
            expr = pc.field("key") == metric_key
            if limit <= 0:
                limit = len(table)
            history = (
                table.filter(expr).slice(offset=offset, length=limit).select(["key", "value", "timestamp", "step"])
            )
            metrics = [
                Metric(
                    key=item["key"],
                    value=item["value"],
                    timestamp=TimeStampMapper.forward(item["timestamp"]),
                    step=item["step"],
                )
                for item in history.to_pylist()
            ]

        return MetricsHistoryModel(metrics=metrics)

    def to_object_storage(self, client: S3ObjectStorageClient) -> None:
        # TODO (vinnamki): It's very ugly and has several other serious issues:
        # concurrency issues, excessive network I/O, etc.
        # Need further discussion about another approach.
        if client.check_live_metrics_file_exists():
            with (
                client.open_live_metrics_file() as fp,
                pa.ipc.open_file(source=fp, options=pa.ipc.IpcReadOptions(use_threads=False)) as reader,
            ):
                table = reader.read_all()
        else:
            table = None

        with (
            client.open_live_metrics_output_stream() as fp,
            pa.ipc.new_file(
                fp,
                schema=PYARROW_SCHEMA,
                options=pa.ipc.IpcWriteOptions(use_threads=False),
            ) as writer,
        ):
            to_append = pa.Table.from_pylist(
                [
                    {
                        "key": metric.key,
                        "value": metric.value,
                        "step": metric.step,
                        "timestamp": metric.timestamp,
                    }
                    for metric in self.metrics
                ],
                schema=PYARROW_SCHEMA,
            )

            to_write = pa.concat_tables(tables=[table, to_append]) if table else to_append

            writer.write_table(to_write)

    def to_mlflow(self) -> list[Metric]:
        return self.metrics


class ProgressModel(BaseModel):
    progress: float
    stage: str

    def to_object_storage(self, client: S3ObjectStorageClient) -> None:
        relative_path = Path("live_metrics", "progress.json")
        client.save_file_from_bytes(
            relative_path=relative_path,
            input_bytes=self.model_dump_json().encode(),
            overwrite=True,
        )


class RunDataModel(BaseModel):
    metrics: LatestMetricsModel

    @classmethod
    def from_object_storage(cls, client: S3ObjectStorageClient) -> RunDataModel:
        return RunDataModel(
            metrics=LatestMetricsModel.from_object_storage(client),
        )

    def to_mlflow(self) -> RunData:
        return RunData(
            metrics=self.metrics.to_mlflow(),
            params=None,
            tags=None,
        )


class RunInputsModel(BaseModel):
    filenames: list[str]
    presigned_urls: list[str]

    @classmethod
    def from_object_storage(cls, client: S3ObjectStorageClient) -> RunInputsModel:
        pattern = re.compile("datum-(\d+)-of-(\d+).arrow")

        filenames = []
        presigned_urls = []

        for obj in client.list_files(relative_path=Path("inputs"), recursive=True):
            if not obj.is_dir and pattern.findall(obj.object_name):
                filename = os.path.basename(obj.object_name)
                filenames += [filename]
                presigned_urls += [client.get_presigned_url(relative_path=Path("inputs") / filename)]

        return RunInputsModel(filenames=filenames, presigned_urls=presigned_urls)

    def to_mlflow(self) -> RunInputs:
        return RunInputs(
            dataset_inputs=[
                DatasetInput(
                    dataset=Dataset(
                        name=filename,
                        digest="",  # TODO(vinnamki): Receive checksum shard.checksum,
                        source_type="http",
                        source=presigned_url,
                    ),
                    # mlflow=2.8.0 has error if tags field is not empty
                )
                for filename, presigned_url in zip(self.filenames, self.presigned_urls)
            ]
        )
