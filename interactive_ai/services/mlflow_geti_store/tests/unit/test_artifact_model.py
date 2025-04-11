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

import pytest
from mlflow_geti_store.artifact_model import (
    ConfigArtifact,
    DispatchingError,
    ErrorLogArtifact,
    ExportableCodeArtifact,
    FullLogArtifact,
    ModelArtifact,
    OptimizedConfigArtifact,
    PerformanceArtifact,
    TileClassifierArtifact,
    dispatch_artifact,
)


class TestArtifactModel:
    def test_model_artifact(self):
        # Succeed
        artifact_model = ModelArtifact.from_filepath("model_fp16_xai.pth")
        assert isinstance(artifact_model, ModelArtifact)
        assert artifact_model.to_object_storage_path() == "outputs/models/model_fp16_xai.pth"

        # Case insensitive
        artifact_model = ModelArtifact.from_filepath("model_INT8-NNCF_NON-XAI.pth")
        assert isinstance(artifact_model, ModelArtifact)

        # The number of fields parsed from the filename is incorrect
        with pytest.raises(ValueError):
            ModelArtifact.from_filepath("model_INT8.pth")

        # Raise errors on 3 fields
        with pytest.raises(ValueError) as ctx:
            ModelArtifact.from_filepath("model_fp64_xxxxai.txt")

        assert "3 validation errors" in str(ctx)

        # Raise errors on 4 fields
        with pytest.raises(ValueError) as ctx:
            ModelArtifact.from_filepath("not-model_fp64_xxxxai.txt")

        assert "4 validation errors" in str(ctx)

    def test_exportable_code_artifact(self):
        # Succeed
        artifact_model = ExportableCodeArtifact.from_filepath("exportable-code_fp16_xai.whl")
        assert isinstance(artifact_model, ExportableCodeArtifact)
        assert artifact_model.to_object_storage_path() == "outputs/exportable_codes/exportable-code_fp16_xai.whl"

        # Case insensitive
        artifact_model = ExportableCodeArtifact.from_filepath("exportable-code_INT8-NNCF_NON-XAI.whl")
        assert isinstance(artifact_model, ExportableCodeArtifact)

        # The number of fields parsed from the filename is incorrect
        with pytest.raises(ValueError):
            ExportableCodeArtifact.from_filepath("exportable-code_INT8.whl")

        # Raise errors on 3 fields
        with pytest.raises(ValueError) as ctx:
            ExportableCodeArtifact.from_filepath("exportable-code_fp64_xxxxai.txt")

        assert "3 validation errors" in str(ctx)

        # Raise errors on 4 fields
        with pytest.raises(ValueError) as ctx:
            ExportableCodeArtifact.from_filepath("not-exportable-code_fp64_xxxxai.txt")

        assert "4 validation errors" in str(ctx)

    def test_optimized_config_artifact(self):
        # Succeed
        artifact_model = OptimizedConfigArtifact.from_filepath("optimized-config.json")
        assert isinstance(artifact_model, OptimizedConfigArtifact)
        assert artifact_model.to_object_storage_path() == "outputs/configurations/optimized-config.json"

        # Case insensitive
        artifact_model = OptimizedConfigArtifact.from_filepath("Optimized-conFig.json")
        assert isinstance(artifact_model, OptimizedConfigArtifact)

        # The number of fields parsed from the filename is incorrect
        with pytest.raises(ValueError):
            OptimizedConfigArtifact.from_filepath("optimized-config_1.json")

        # Raise errors on 1 fields
        with pytest.raises(ValueError) as ctx:
            OptimizedConfigArtifact.from_filepath("not-optimized-config.json")

        assert "1 validation error" in str(ctx)

        # Raise errors on 2 fields
        with pytest.raises(ValueError) as ctx:
            OptimizedConfigArtifact.from_filepath("not-optimized-config.txt")

        assert "2 validation errors" in str(ctx)

    @pytest.mark.parametrize(
        "filepath, artifact_model_type",
        [
            ("model_fp16_xai.pth", ModelArtifact),
            ("exportable-code_fp16_xai.whl", ExportableCodeArtifact),
            ("optimized-config.json", OptimizedConfigArtifact),
            ("config_fp16_xai.json", ConfigArtifact),
            ("performance-json.bin", PerformanceArtifact),
            ("tile-classifier_fp16_xai.xml", TileClassifierArtifact),
            ("error.json", ErrorLogArtifact),
            ("otx-full.log", FullLogArtifact),
            ("unknown-file.abc", None),
        ],
    )
    def test_dispatch(self, filepath, artifact_model_type):
        if artifact_model_type is None:
            with pytest.raises(DispatchingError):
                dispatched = dispatch_artifact(filepath)
            return

        dispatched = dispatch_artifact(filepath)
        assert isinstance(dispatched, artifact_model_type)
