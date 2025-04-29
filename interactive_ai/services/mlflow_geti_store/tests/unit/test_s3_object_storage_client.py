# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from minio import Minio
from minio.datatypes import Object
from mlflow_geti_store.s3_object_storage_client import S3ObjectStorageClientSingleton
from mlflow_geti_store.utils import Identifier

ENV_VARS = {
    "BUCKET_NAME_MLFLOWEXPERIMENTS": "mlflowexperiments",
    "S3_ACCESS_KEY": "dummy",
    "S3_SECRET_KEY": "dummy",
    "S3_PRESIGNED_URL_ACCESS_KEY": "dummy_access_key",
    "S3_PRESIGNED_URL_SECRET_KEY": "dummy_secret_key",
}


@patch.dict(os.environ, ENV_VARS)
class TestS3ObjectStorageClient:
    @pytest.fixture(autouse=True)
    def fxt_identifier(self, fxt_organization_id, fxt_workspace_id, fxt_project_id, fxt_job_id):
        with patch(
            "mlflow_geti_store.s3_object_storage_client.Identifier.from_config_file",
            return_value=Identifier(
                fxt_organization_id,
                fxt_workspace_id,
                fxt_project_id,
                fxt_job_id,
            ),
        ):
            yield

    @pytest.fixture()
    def fxt_mock_minio_client(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("S3_CREDENTIALS_PROVIDER", "local")

        mock_minio_client = MagicMock(spec=Minio)

        with patch("mlflow_geti_store.s3_object_storage_client.Minio", return_value=mock_minio_client):
            yield mock_minio_client

    def test_list_files(self, fxt_mock_minio_client):
        inst = S3ObjectStorageClientSingleton.instance(renew=True)

        call_count = 0

        def _mock_list_objects(bucket_name, prefix, recursive):
            nonlocal call_count
            if call_count == 0:
                retval = [Object(bucket_name, object_name=prefix + "/")]
            elif call_count == 1:
                file_list = [
                    Path("./inputs/.placeholder"),
                    Path("./inputs/config.json"),
                    Path("./inputs/datum-0-of-1.arrow"),
                    Path("./inputs/model.pth"),
                    Path("./project.json"),
                    Path("./run_info.json"),
                    Path("./outputs/models/.placeholder"),
                    Path("./outputs/configurations/.placeholder"),
                    Path("./outputs/exportable_codes/.placeholder"),
                    Path("./outputs/logs/otx-full.log"),
                    Path("./outputs/logs/.placeholder"),
                    Path("./outputs/logs/error.json"),
                    Path("./live_metrics/.placeholder"),
                    Path("./live_metrics/progress.json"),
                    Path("./metadata.json"),
                ]
                retval = [Object(bucket_name, object_name=str(Path(prefix) / Path(fpath))) for fpath in file_list]
            else:
                raise RuntimeError("# of calls should be less than 3")

            call_count += 1
            return retval

        fxt_mock_minio_client.list_objects.side_effect = _mock_list_objects
        objects = inst.list_files(relative_path=Path("."))

        expect_files = {"project.json", "run_info.json", "metadata.json"}
        expect_dirs = {"inputs", "outputs", "live_metrics"}
        expect_obj_names = {*expect_files, *expect_dirs}

        actual_obj_names = {Path(obj.object_name).name for obj in objects}
        assert actual_obj_names == expect_obj_names

        for obj in objects:
            # Check file or directory discrimination
            if obj.is_dir:
                assert Path(obj.object_name).name in expect_dirs
            else:
                assert Path(obj.object_name).name in expect_files
