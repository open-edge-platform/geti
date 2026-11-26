#
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from model_api.utils.hf_hub_helper import (
    _HF_IMPORT_ERROR_MSG,
    download_from_hf,
    find_model_file,
)

# ───────────────────────── find_model_file tests ─────────────────────────


class TestFindModelFile:
    """Tests for the find_model_file utility."""

    def test_single_xml_file(self, tmp_path):
        (tmp_path / "model.xml").touch()
        (tmp_path / "model.bin").touch()
        assert find_model_file(tmp_path) == tmp_path / "model.xml"

    def test_single_onnx_file(self, tmp_path):
        (tmp_path / "model.onnx").touch()
        assert find_model_file(tmp_path) == tmp_path / "model.onnx"

    def test_xml_preferred_over_onnx(self, tmp_path):
        """When both a single .xml and .onnx exist, .xml should win."""
        (tmp_path / "model.xml").touch()
        (tmp_path / "model.bin").touch()
        (tmp_path / "model.onnx").touch()
        assert find_model_file(tmp_path) == tmp_path / "model.xml"

    def test_multiple_xml_raises(self, tmp_path):
        (tmp_path / "a.xml").touch()
        (tmp_path / "b.xml").touch()
        with pytest.raises(ValueError, match="Multiple OpenVINO IR model files"):
            find_model_file(tmp_path)

    def test_multiple_onnx_raises(self, tmp_path):
        (tmp_path / "a.onnx").touch()
        (tmp_path / "b.onnx").touch()
        with pytest.raises(ValueError, match="Multiple ONNX model files"):
            find_model_file(tmp_path)

    def test_no_model_files_raises(self, tmp_path):
        (tmp_path / "readme.txt").touch()
        with pytest.raises(FileNotFoundError, match="No model files"):
            find_model_file(tmp_path)

    def test_empty_dir_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="No model files"):
            find_model_file(tmp_path)

    def test_explicit_filename(self, tmp_path):
        (tmp_path / "custom.xml").touch()
        (tmp_path / "other.xml").touch()
        assert find_model_file(tmp_path, filename="custom.xml") == tmp_path / "custom.xml"

    def test_explicit_filename_missing_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="Specified model file not found"):
            find_model_file(tmp_path, filename="missing.xml")

    def test_nested_xml_file(self, tmp_path):
        subdir = tmp_path / "openvino"
        subdir.mkdir()
        (subdir / "model.xml").touch()
        (subdir / "model.bin").touch()
        assert find_model_file(tmp_path) == subdir / "model.xml"


# ─────────────────────── download_from_hf tests ─────────────────────────


class TestDownloadFromHf:
    """Tests for the download_from_hf function."""

    def test_import_error_when_hf_hub_missing(self):
        """Raises ImportError with a helpful message when huggingface_hub is absent."""
        with patch.dict("sys.modules", {"huggingface_hub": None}), pytest.raises(ImportError, match="huggingface_hub"):
            download_from_hf("user/repo")

    @patch("model_api.utils.hf_hub_helper.find_model_file")
    def test_snapshot_download_called_without_filename(self, mock_find):
        """When filename is None, snapshot_download should be used."""
        mock_find.return_value = Path("/cache/model.xml")
        auth_value = "test-hf-credential"

        with patch.dict("sys.modules", {"huggingface_hub": MagicMock()}) as _:
            import sys

            mock_hf = sys.modules["huggingface_hub"]
            mock_hf.snapshot_download.return_value = "/cache"

            result = download_from_hf(
                "user/repo",
                revision="main",
                token=auth_value,
                cache_dir="/custom/cache",
            )

            mock_hf.snapshot_download.assert_called_once_with(
                repo_id="user/repo",
                revision="main",
                token=auth_value,
                cache_dir="/custom/cache",
                local_dir=None,
                force_download=False,
                local_files_only=False,
                repo_type="model",
                allow_patterns=["*.xml", "*.bin", "*.onnx"],
            )
            assert result == Path("/cache/model.xml")

    def test_hf_hub_download_called_with_filename(self):
        """When filename is provided, hf_hub_download should be used."""
        auth_value = "test-hf-credential"

        with patch.dict("sys.modules", {"huggingface_hub": MagicMock()}) as _:
            import sys

            mock_hf = sys.modules["huggingface_hub"]
            mock_hf.hf_hub_download.return_value = "/cache/model.xml"

            result = download_from_hf(
                "user/repo",
                filename="model.xml",
                token=auth_value,
            )

            # Should download both .xml and .bin
            assert mock_hf.hf_hub_download.call_count == 2
            assert result == Path("/cache/model.xml")

    def test_hf_hub_download_onnx_no_bin_companion(self):
        """When filename is an .onnx file, no .bin companion is downloaded."""
        with patch.dict("sys.modules", {"huggingface_hub": MagicMock()}) as _:
            import sys

            mock_hf = sys.modules["huggingface_hub"]
            mock_hf.hf_hub_download.return_value = "/cache/model.onnx"

            result = download_from_hf(
                "user/repo",
                filename="model.onnx",
            )

            # Only one download call for .onnx (no .bin companion)
            mock_hf.hf_hub_download.assert_called_once()
            assert result == Path("/cache/model.onnx")

    def test_subfolder_forwarded(self):
        """The subfolder parameter should be forwarded to hf_hub_download."""
        with patch.dict("sys.modules", {"huggingface_hub": MagicMock()}) as _:
            import sys

            mock_hf = sys.modules["huggingface_hub"]
            mock_hf.hf_hub_download.return_value = "/cache/openvino/model.xml"

            download_from_hf(
                "user/repo",
                filename="model.xml",
                subfolder="openvino",
            )

            call_kwargs = mock_hf.hf_hub_download.call_args_list[0][1]
            assert call_kwargs["subfolder"] == "openvino"


# ────────────────────── Model.from_pretrained tests ──────────────────────


class TestModelFromPretrained:
    """Tests for the Model.from_pretrained classmethod."""

    @patch("model_api.models.model.Model.create_model")
    @patch("model_api.utils.hf_hub_helper.download_from_hf")
    def test_from_pretrained_calls_create_model(self, mock_download, mock_create):
        """from_pretrained should download and delegate to create_model."""
        from model_api.models import Model

        mock_download.return_value = Path("/cache/model.xml")
        mock_create.return_value = MagicMock()

        Model.from_pretrained("user/repo", device="CPU", model_type="Classification")

        mock_download.assert_called_once_with(
            repo_id="user/repo",
            filename=None,
            revision=None,
            token=None,
            cache_dir=None,
            local_dir=None,
            force_download=False,
            local_files_only=False,
            subfolder=None,
            repo_type="model",
        )
        mock_create.assert_called_once_with(
            model=str(Path("/cache/model.xml")),
            model_type="Classification",
            configuration={},
            preload=True,
            core=None,
            weights_path=None,
            adaptor_parameters={},
            device="CPU",
            nstreams="1",
            nthreads=None,
            max_num_requests=0,
            precision="FP16",
        )

    @patch("model_api.models.model.Model.create_model")
    @patch("model_api.utils.hf_hub_helper.download_from_hf")
    def test_hf_params_forwarded(self, mock_download, mock_create):
        """All HF-specific parameters should be forwarded to download_from_hf."""
        from model_api.models import Model

        mock_download.return_value = Path("/cache/model.xml")
        mock_create.return_value = MagicMock()
        auth_value = "test-hf-credential"

        Model.from_pretrained(
            "user/private-repo",
            cache_dir="/my/cache",
            force_download=True,
            local_files_only=False,
            token=auth_value,
            revision="v2.0",
            local_dir="/my/local",
            subfolder="openvino",
            repo_type="model",
            filename="best.xml",
        )

        mock_download.assert_called_once_with(
            repo_id="user/private-repo",
            filename="best.xml",
            revision="v2.0",
            token=auth_value,
            cache_dir="/my/cache",
            local_dir="/my/local",
            force_download=True,
            local_files_only=False,
            subfolder="openvino",
            repo_type="model",
        )

    @patch("model_api.models.model.Model.create_model")
    @patch("model_api.utils.hf_hub_helper.download_from_hf")
    def test_create_model_params_forwarded(self, mock_download, mock_create):
        """All create_model parameters should be forwarded correctly."""
        from model_api.models import Model

        mock_download.return_value = Path("/cache/model.xml")
        mock_create.return_value = MagicMock()
        mock_core = MagicMock()

        Model.from_pretrained(
            "user/repo",
            model_type="SSD",
            configuration={"confidence_threshold": 0.3},
            preload=False,
            core=mock_core,
            weights_path="/custom/weights.bin",
            adaptor_parameters={"input_layouts": "NCHW"},
            device="GPU",
            nstreams="2",
            nthreads=4,
            max_num_requests=2,
            precision="FP32",
        )

        mock_create.assert_called_once_with(
            model=str(Path("/cache/model.xml")),
            model_type="SSD",
            configuration={"confidence_threshold": 0.3},
            preload=False,
            core=mock_core,
            weights_path="/custom/weights.bin",
            adaptor_parameters={"input_layouts": "NCHW"},
            device="GPU",
            nstreams="2",
            nthreads=4,
            max_num_requests=2,
            precision="FP32",
        )

    def test_import_error_propagated(self):
        """ImportError from download_from_hf should propagate."""
        from model_api.models import Model

        with (
            patch(
                "model_api.utils.hf_hub_helper.download_from_hf",
                side_effect=ImportError(_HF_IMPORT_ERROR_MSG),
            ),
            pytest.raises(ImportError, match="huggingface_hub"),
        ):
            Model.from_pretrained("user/repo")
