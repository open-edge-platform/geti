# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from mlflow_geti_store.s3_object_storage_client import S3ObjectStorageClientSingleton


@pytest.fixture(scope="module", autouse=True)
def fxt_identifier(
    fxt_organization_id,
    fxt_workspace_id,
    fxt_project_id,
    fxt_job_id,
):
    with TemporaryDirectory() as root_dir:
        fpath = os.path.join(root_dir, "config.json")
        with open(fpath, "w") as fp:
            os.environ["IDENTIFIER_PATH"] = fpath
            json.dump(
                {
                    "organization_id": fxt_organization_id,
                    "workspace_id": fxt_workspace_id,
                    "project_id": fxt_project_id,
                    "job_id": fxt_job_id,
                },
                fp,
            )

        yield

        os.environ.pop("IDENTIFIER_PATH")


@pytest.fixture(scope="module", autouse=True)
def fxt_bucket(fxt_identifier):
    os.environ["S3_CREDENTIALS_PROVIDER"] = "local"
    os.environ["BUCKET_NAME_MLFLOWEXPERIMENTS"] = "mlflowexperiments"

    client = S3ObjectStorageClientSingleton.instance()

    if client.client.bucket_exists(client.bucket_name):
        client.clean_all_files()
        client.client.remove_bucket(client.bucket_name)

    client.client.make_bucket(client.bucket_name)

    yield client

    client.clean_all_files()
    client.client.remove_bucket(client.bucket_name)

    os.environ.pop("S3_CREDENTIALS_PROVIDER")
    os.environ.pop("BUCKET_NAME_MLFLOWEXPERIMENTS")


@pytest.fixture(autouse=True)
def fxt_root_dir(fxt_bucket, fxt_project_json, fxt_run_info_json):
    client = S3ObjectStorageClientSingleton.instance()
    client.save_file_from_local_disk(
        relative_path=Path("project.json"),
        local_file_path=fxt_project_json,
    )
    client.save_file_from_local_disk(
        relative_path=Path("run_info.json"),
        local_file_path=fxt_run_info_json,
    )
    yield
    client.delete_files(relative_path=Path("."), recursive=True)


@pytest.fixture(autouse=True)
def fxt_live_metrics_dir(fxt_bucket, fxt_live_metrics):
    client = S3ObjectStorageClientSingleton.instance()
    client.save_file_from_local_disk(
        relative_path=Path("live_metrics") / "metrics.arrow",
        local_file_path=fxt_live_metrics,
    )

    yield
    client.delete_files(relative_path=Path("live_metrics"), recursive=True)


@pytest.fixture(autouse=True)
def fxt_inputs_dir(fxt_bucket):
    client = S3ObjectStorageClientSingleton.instance()

    for idx in range(10):
        client.save_file_from_bytes(
            relative_path=Path("inputs") / f"datum-{idx}-of-10.arrow",
            input_bytes=b"data",
        )

    yield
    client.delete_files(relative_path=Path("inputs"), recursive=True)
