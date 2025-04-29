# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import os.path
import shutil
from contextlib import nullcontext
from functools import partial
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from geti_types import ID
from migration.utils.connection import MinioStorageClient
from sc_sdk.versioning import DataVersion

from job.entities.exceptions import ImportProjectUnsupportedVersionException, SignatureVerificationFailed
from job.repos.base.storage_repo import StorageRepo
from job.usecases import ProjectImportUseCase

EXTERNAL_KEY_FF = "FEATURE_FLAG_ALLOW_EXTERNAL_KEY_PROJECT_IMPORT"
CERT_MANAGER_PRIVKEY_ENV_NAME = "SIGNING_IE_PRIVKEY"
TEST_DATA_DIR = os.path.join("tests", "test_data")
TEST_PROJECT_ARCHIVES_DIR = os.path.join(TEST_DATA_DIR, "project_archives")
TEST_SAAS_PRIV_KEY_PATH = os.path.join(TEST_DATA_DIR, "test-saas-privkey.pem")
TEST_ONPREM_PRIV_KEY_PATH = os.path.join(TEST_DATA_DIR, "test-onprem-privkey.pem")


def do_nothing(*args, **kwargs):
    pass


def read_privkey(filepath: str):
    with open(filepath) as f:
        return f.read()


def copy_zip_to_local_path(file_id: ID, local_zip_path: str, source_zip_path: str) -> None:
    """Copy zip from source_zip_path to local_zip_path"""
    shutil.copy(source_zip_path, local_zip_path)


def setup_envs(target_env: str) -> None:
    if target_env == "saas":
        os.environ[EXTERNAL_KEY_FF] = "false"
        os.environ[CERT_MANAGER_PRIVKEY_ENV_NAME] = read_privkey(TEST_SAAS_PRIV_KEY_PATH)
    else:
        os.environ[EXTERNAL_KEY_FF] = "true"
        os.environ[CERT_MANAGER_PRIVKEY_ENV_NAME] = read_privkey(TEST_ONPREM_PRIV_KEY_PATH)


@pytest.fixture
def fxt_mock_progress_callback():
    yield MagicMock()


@pytest.fixture
def fxt_mocked_minio_storage_client():
    mock_minio_client = MagicMock()
    with (
        patch.object(MinioStorageClient, "get_storage_client", return_value=mock_minio_client),
    ):
        yield


@pytest.mark.ProjectIEMsComponent
class TestProjectImport:
    @pytest.mark.parametrize(
        "filename, target_env",
        [
            ("2_6-saas-classification-empty.zip", "on-prem"),
            ("2_6-saas-classification-empty.zip", "saas"),
            ("2_6-onprem-detection-empty.zip", "on-prem"),
        ],
        ids=[
            "Projects exported from SaaS can be imported to on-prem",
            "Projects exported from SaaS can be imported to SaaS",
            "Projects exported from on-prem can be imported to on-prem",
        ],
    )
    def test_import_zip(
        self,
        filename,
        target_env,
        fxt_mock_progress_callback,
        fxt_ote_id,
        fxt_session_ctx,
        fxt_mocked_minio_storage_client,
    ) -> None:
        # Arrange
        setup_envs(target_env)

        file_id = fxt_ote_id(0)
        creator_id = ID(str(uuid4()))
        filepath = os.path.join(TEST_PROJECT_ARCHIVES_DIR, filename)
        with (
            patch.object(
                ProjectImportUseCase,
                "_download_import_zip",
                new=partial(copy_zip_to_local_path, source_zip_path=filepath),
            ),
            patch.object(StorageRepo, "__init__", new=do_nothing),
            patch("job.usecases.project_import_usecase.publish_metadata_update") as mock_metadata_update,
        ):
            ProjectImportUseCase().import_zip(
                file_id=file_id, creator_id=creator_id, progress_callback=fxt_mock_progress_callback
            )

        mock_metadata_update.assert_called_once()

    @pytest.mark.parametrize(
        "filename, source_data_version, target_data_version",
        [
            ("2_0-saas-anomaly_detection-small-unknown-upgraded_from_1_8.zip", "1.0", None),
            ("2_6-saas-classification-empty.zip", "19.0", "19.0"),
            ("2_6-saas-classification-empty.zip", "19.0", "18.0"),
        ],
        ids=[
            "Projects exported from Geti with data version 1.0 can be imported to latest Geti version",
            "Projects exported from Geti with data version 19.0 can be imported to same Geti version",
            "Projects exported from Geti with data version 19.0 CANNOT be imported to Geti with lower version",
        ],
    )
    def test_import_zip_data_version(
        self,
        filename,
        source_data_version,
        target_data_version,
        fxt_mock_progress_callback,
        fxt_ote_id,
        fxt_session_ctx,
        fxt_mocked_minio_storage_client,
    ) -> None:
        # Arrange
        setup_envs("on-prem")

        target_version = DataVersion(target_data_version) if target_data_version else DataVersion.get_current()
        is_data_version_supported = target_data_version is None or int(source_data_version.split(".")[0]) <= int(
            target_data_version.split(".")[0]
        )

        file_id = fxt_ote_id(0)
        creator_id = ID(str(uuid4()))
        filepath = os.path.join(TEST_PROJECT_ARCHIVES_DIR, filename)
        with (
            patch.object(
                ProjectImportUseCase,
                "_download_import_zip",
                new=partial(copy_zip_to_local_path, source_zip_path=filepath),
            ),
            patch.object(StorageRepo, "__init__", new=do_nothing),
            patch("job.usecases.project_import_usecase.publish_metadata_update") as mock_metadata_update,
            patch.object(DataVersion, "get_current", return_value=target_version),
            nullcontext() if is_data_version_supported else pytest.raises(ImportProjectUnsupportedVersionException),
        ):
            ProjectImportUseCase().import_zip(
                file_id=file_id, creator_id=creator_id, progress_callback=fxt_mock_progress_callback
            )

        if is_data_version_supported:
            mock_metadata_update.assert_called_once()

    @pytest.mark.parametrize(
        "filename, target_env",
        [
            ("project_with_bad_signature.zip", "on-prem"),
            ("project_with_bad_signature.zip", "saas"),
            ("2_6-onprem-detection-empty.zip", "saas"),
        ],
        ids=[
            "Projects exported with tampered signature CANNOT be imported to on-prem",
            "Projects exported with tampered signature CANNOT be imported to saas",
            "Projects exported from on-prem CANNOT be imported to SaaS",
        ],
    )
    def test_import_zip_signature_verification_onprem_failed(
        self, filename, target_env, fxt_ote_id, fxt_mock_progress_callback
    ) -> None:
        # Arrange
        setup_envs(target_env)
        file_id = fxt_ote_id(0)
        creator_id = ID(str(uuid4()))
        filepath = os.path.join(TEST_PROJECT_ARCHIVES_DIR, "project_with_bad_signature.zip")

        with (
            patch.object(
                ProjectImportUseCase,
                "_download_import_zip",
                new=partial(copy_zip_to_local_path, source_zip_path=filepath),
            ),
            pytest.raises(SignatureVerificationFailed),
        ):
            ProjectImportUseCase().import_zip(
                file_id=file_id, creator_id=creator_id, progress_callback=fxt_mock_progress_callback
            )
