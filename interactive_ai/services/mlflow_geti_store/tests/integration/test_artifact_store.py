# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os
from pathlib import Path

import pytest
from mlflow.exceptions import MlflowException
from mlflow_geti_store.artifact_store import GetiArtifactRepository
from mlflow_geti_store.utils import ARTIFACT_ROOT_URI_PREFIX, Identifier


class TestGetiArtifactRepository:
    @pytest.fixture()
    def fxt_artifact_uri(
        self,
        fxt_organization_id,
        fxt_workspace_id,
        fxt_project_id,
        fxt_job_id,
    ):
        path = Identifier(
            organization_id=fxt_organization_id,
            workspace_id=fxt_workspace_id,
            project_id=fxt_project_id,
            job_id=fxt_job_id,
        ).to_path()
        return ARTIFACT_ROOT_URI_PREFIX + str(path)

    @pytest.fixture()
    def fxt_artifact_repo(self, fxt_artifact_uri) -> GetiArtifactRepository:
        return GetiArtifactRepository(artifact_uri="geti://")

    @pytest.fixture()
    def fxt_valid_files_dir(self, tmp_path: Path):
        root_dir = tmp_path / "valid_outputs"

        (root_dir / "models").mkdir(parents=True)
        (root_dir / "exportable_codes").mkdir(parents=True)
        (root_dir / "configurations").mkdir(parents=True)

        (root_dir / "models" / "model_fp16_xai.pth").write_bytes(b"data")
        (root_dir / "exportable_codes" / "exportable-code_fp16_xai.whl").write_bytes(b"data")
        (root_dir / "configurations" / "optimized-config.json").write_bytes(b"data")

        yield root_dir

    @pytest.fixture()
    def fxt_invalid_files_dir(self, tmp_path: Path):
        root_dir = tmp_path / "invalid_outputs"

        (root_dir / "models").mkdir(parents=True)
        (root_dir / "exportable_codes").mkdir(parents=True)
        (root_dir / "configurations").mkdir(parents=True)

        (root_dir / "models" / "not-model_fp64_xxxxai.txt").write_bytes(b"data")
        (root_dir / "exportable_codes" / "not-exportable-code_fp64_xxxxai.txt").write_bytes(b"data")
        (root_dir / "configurations" / "not-optimized-config.txt").write_bytes(b"data")

        yield root_dir

    def test_log_artifacts(
        self,
        fxt_artifact_repo: GetiArtifactRepository,
        fxt_valid_files_dir,
        fxt_invalid_files_dir,
        fxt_artifact_uri: str,
    ):
        fxt_artifact_repo.log_artifacts(
            local_dir=fxt_valid_files_dir,
            artifact_path=fxt_artifact_uri,
        )
        outputs_uri = os.path.join(fxt_artifact_uri, "outputs")
        file_infos = fxt_artifact_repo.list_artifacts(outputs_uri)

        assert len(list(file_infos)) == 3

        with pytest.raises(MlflowException):
            fxt_artifact_repo.log_artifacts(
                local_dir=fxt_invalid_files_dir,
                artifact_path=fxt_artifact_uri,
            )

    def test_download_file(
        self,
        fxt_artifact_repo: GetiArtifactRepository,
        fxt_valid_files_dir: Path,
        fxt_artifact_uri: str,
        fxt_identifier: dict,
        tmp_path: Path,
    ):
        fxt_artifact_repo.log_artifacts(
            local_dir=str(fxt_valid_files_dir),
            artifact_path=fxt_artifact_uri,
        )

        dst_path = tmp_path / "download"
        dst_path.mkdir()

        fxt_artifact_repo.download_artifacts(artifact_path=os.path.join(fxt_artifact_uri, "outputs"), dst_path=dst_path)

    def test_delete_artifacts(
        self,
        fxt_artifact_repo: GetiArtifactRepository,
        fxt_valid_files_dir,
        fxt_artifact_uri,
    ):
        fxt_artifact_repo.log_artifacts(
            local_dir=fxt_valid_files_dir,
            artifact_path=fxt_artifact_uri,
        )
        file_infos = fxt_artifact_repo.list_artifacts(os.path.join(fxt_artifact_uri, "outputs", "models"))
        assert len(list(file_infos)) == 1

        fxt_artifact_repo.delete_artifacts(
            artifact_path=os.path.join(fxt_artifact_uri, "outputs", "models", "model_fp16_xai.pth"),
        )
        file_infos = fxt_artifact_repo.list_artifacts(os.path.join(fxt_artifact_uri, "outputs", "models"))
        assert len(list(file_infos)) == 0
