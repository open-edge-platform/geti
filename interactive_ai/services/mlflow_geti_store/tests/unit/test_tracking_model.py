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

import json
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pyarrow as pa
import pytest
from minio.datatypes import Object
from mlflow.entities import Experiment, LifecycleStage, Metric, RunInfo
from mlflow_geti_store.s3_object_storage_client import S3ObjectStorageClient
from mlflow_geti_store.tracking_model import (
    LatestMetricsModel,
    MetricsHistoryModel,
    ProgressModel,
    ProjectModel,
    RunDataModel,
    RunInfoModel,
    RunInputsModel,
)
from mlflow_geti_store.utils import ARTIFACT_ROOT_URI_PREFIX, TimeStampMapper


def assert_time_delta(a, b):
    delta = a - b if a > b else b - a
    assert delta < timedelta(seconds=0.01)


class TestTrackingModel:
    @patch("mlflow_geti_store.tracking_model.S3ObjectStorageClient", spec=S3ObjectStorageClient)
    def test_project_model(
        self,
        mock_client,
        fxt_project_json,
        fxt_project_id,
        fxt_organization_id,
        fxt_workspace_id,
        fxt_start_time,
    ):
        with open(fxt_project_json) as fp:
            mock_client.get_by_filename.return_value.data = fp.read()

        model = ProjectModel.from_object_storage(client=mock_client)

        assert model.project_id == fxt_project_id
        assert model.name == "project_name"
        assert model.creator_id == "project_creator"
        assert model.description == "project_description"
        assert model.creation_date == fxt_start_time
        assert model.workspace_id == fxt_workspace_id
        assert model.organization_id == fxt_organization_id

        experiment = model.to_mlflow()

        assert isinstance(experiment, Experiment)
        assert experiment.experiment_id == fxt_project_id
        assert experiment.name == "project_name"
        assert experiment.artifact_location.startswith(ARTIFACT_ROOT_URI_PREFIX)
        assert experiment.lifecycle_stage == LifecycleStage.ACTIVE
        assert_time_delta(TimeStampMapper.backward(experiment.creation_time), fxt_start_time)

    @patch("mlflow_geti_store.tracking_model.S3ObjectStorageClient", spec=S3ObjectStorageClient)
    def test_run_info_model(
        self,
        mock_client,
        fxt_project_json,
        fxt_run_info_json,
        fxt_job_id,
        fxt_organization_id,
        fxt_workspace_id,
        fxt_start_time,
    ):
        with open(fxt_project_json) as fp:
            mock_client.get_by_filename.return_value.data = fp.read()

        project_model = ProjectModel.from_object_storage(client=mock_client)

        with open(fxt_run_info_json) as fp:
            mock_client.get_by_filename.return_value.data = fp.read()

        model = RunInfoModel.from_object_storage(client=mock_client)

        assert model.run_uuid == fxt_job_id
        assert model.job_name == "job_name"
        assert model.author == "job_author"
        assert model.status == "SCHEDULED"
        assert model.start_time == fxt_start_time
        assert model.end_time is None
        assert model.lifecycle_stage == "ACTIVE"

        run_info = model.to_mlflow(project_model)

        assert isinstance(run_info, RunInfo)
        assert run_info.run_uuid == fxt_job_id
        assert run_info.run_id == fxt_job_id
        assert run_info.user_id == "job_author"
        assert run_info.run_name == f"job_name_{fxt_job_id}"
        assert run_info.status == "SCHEDULED"
        assert run_info.artifact_uri.startswith(ARTIFACT_ROOT_URI_PREFIX)
        assert_time_delta(TimeStampMapper.backward(run_info.start_time), fxt_start_time)

    @patch("mlflow_geti_store.tracking_model.S3ObjectStorageClient", spec=S3ObjectStorageClient)
    def test_latest_metrics_model(
        self,
        mock_client,
        fxt_live_metrics,
    ):
        with open(fxt_live_metrics, "rb") as fp:
            mock_client.open_live_metrics_file.return_value.__enter__.return_value = fp
            model = LatestMetricsModel.from_object_storage(mock_client)

        assert isinstance(model, LatestMetricsModel)

        mlflow_metrics = model.to_mlflow()

        assert {metric.key for metric in mlflow_metrics} == {"car", "cat", "dog"}
        assert all(metric.value == 1.0 for metric in mlflow_metrics)
        assert all(metric.timestamp == 9 for metric in mlflow_metrics)
        assert all(metric.step == 9 for metric in mlflow_metrics)

    @pytest.mark.parametrize("offset", [0, 5])
    @pytest.mark.parametrize("limit", [3, 10])
    @pytest.mark.parametrize("key", ["car", "cat", "dog"])
    @patch("mlflow_geti_store.tracking_model.S3ObjectStorageClient", spec=S3ObjectStorageClient)
    def test_metrics_history_model_from_object_storage(
        self,
        mock_client,
        fxt_live_metrics,
        offset,
        limit,
        key,
    ):
        with open(fxt_live_metrics, "rb") as fp:
            mock_client.open_live_metrics_file.return_value.__enter__.return_value = fp

            model = MetricsHistoryModel.from_object_storage(
                mock_client,
                metric_key=key,
                offset=offset,
                limit=limit,
            )

        assert isinstance(model, MetricsHistoryModel)

        mlflow_metrics = model.to_mlflow()

        if offset + limit < 10:
            assert len(mlflow_metrics) == limit
        else:
            assert len(mlflow_metrics) == 10 - offset

        assert all(metric.key == key for metric in mlflow_metrics)
        assert all(metric.value <= 10.0 - offset for metric in mlflow_metrics)
        assert all(metric.timestamp >= offset for metric in mlflow_metrics)
        assert all(metric.step >= offset for metric in mlflow_metrics)

    @patch("mlflow_geti_store.tracking_model.S3ObjectStorageClient", spec=S3ObjectStorageClient)
    def test_metrics_history_model_to_object_storage(
        self,
        mock_client,
        fxt_live_metrics,
        tmpdir,
    ):
        fpath_to_write = tmpdir / "tmp.arrow"

        with open(fxt_live_metrics, "rb") as fp_read, open(fpath_to_write, "wb") as fp_write:
            mock_client.open_live_metrics_file.return_value.__enter__.return_value = fp_read
            mock_client.open_live_metrics_output_stream.return_value.__enter__.return_value = fp_write

            model = MetricsHistoryModel(
                metrics=[
                    Metric(
                        key=key,
                        value=20 - idx,
                        timestamp=idx,
                        step=idx,
                    )
                    for key in ["car", "cat", "dog"]
                    for idx in range(10, 20)
                ]
            )
            model.to_object_storage(client=mock_client)

        with (
            open(fpath_to_write, "rb") as fp,
            pa.ipc.open_file(source=fp, options=pa.ipc.IpcReadOptions(use_threads=False)) as reader,
        ):
            table = reader.read_all()
            assert len(table) == 60  # 30 + 30

    @patch("mlflow_geti_store.tracking_model.S3ObjectStorageClient", spec=S3ObjectStorageClient)
    def test_progress_model(self, mock_client):
        model = ProgressModel(progress=1.0, stage="TRAINING")

        model.to_object_storage(client=mock_client)

        mock_client.save_file_from_bytes.assert_called_once()
        kwargs = mock_client.save_file_from_bytes.call_args.kwargs
        assert json.loads(kwargs.get("input_bytes")) == {"progress": 1.0, "stage": "TRAINING"}

    @patch("mlflow_geti_store.tracking_model.S3ObjectStorageClient", spec=S3ObjectStorageClient)
    def test_run_data_model(self, mock_client, fxt_live_metrics):
        with open(fxt_live_metrics, "rb") as fp:
            mock_client.open_live_metrics_file.return_value.__enter__.return_value = fp
            model = RunDataModel.from_object_storage(client=mock_client)

            mlflow_run_data = model.to_mlflow()
            mlflow_metrics = mlflow_run_data.metrics

            # Not supported, it should be empty
            assert mlflow_run_data.params == {}
            assert mlflow_run_data.tags == {}

            # Same as the latest metrics
            assert set(mlflow_metrics.keys()) == {"car", "cat", "dog"}
            assert all(value == 1.0 for value in mlflow_metrics.values())

    @patch("mlflow_geti_store.tracking_model.S3ObjectStorageClient", spec=S3ObjectStorageClient)
    def test_run_inputs_model(self, mock_client):
        def _create_mock(idx):
            mock = MagicMock(spec=Object)
            if idx < 10:
                mock.object_name = f"datum-{idx}-of-10.arrow"
            else:
                mock.object_name = f"not-datum-arrow-file-{idx}.txt"
            mock.is_dir = False
            return mock

        # 10 Arrow files and 5 non-Arrow files
        mock_client.list_files.return_value = [_create_mock(idx) for idx in range(15)]
        mock_client.get_presigned_url.return_value = "http://dummy_url"

        model = RunInputsModel.from_object_storage(client=mock_client)

        run_inputs = model.to_mlflow()

        assert len(run_inputs.dataset_inputs) == 10
        assert all(input.dataset.source == "http://dummy_url" for input in run_inputs.dataset_inputs)
