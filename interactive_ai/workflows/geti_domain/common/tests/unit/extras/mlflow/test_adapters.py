# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module tests GetiOTXInterfaceAdapter."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest
from sc_sdk.adapters.model_adapter import DataSource
from sc_sdk.configuration.helper import convert
from sc_sdk.entities.metrics import CurveMetric, LineChartInfo, LineMetricsGroup, Performance, ScoreMetric
from sc_sdk.entities.model import Model, ModelFormat, ModelOptimizationType, ModelPrecision, ModelStatus
from sc_sdk.repos.model_repo import ModelRepo

from jobs_common_extras.mlflow.adapters.definitions import OPENVINO_BIN_KEY, OPENVINO_XML_KEY, ClsSubTaskType
from jobs_common_extras.mlflow.adapters.geti_otx_interface import GetiOTXInterfaceAdapter


@pytest.mark.JobsComponent
class TestGetiOTXInterfaceAdapter:
    @pytest.fixture()
    def fxt_performance(self):
        return Performance(
            score=ScoreMetric("dummy", 1.0),
            dashboard_metrics=[
                LineMetricsGroup(
                    metrics=[CurveMetric(name="dummy", ys=[1, 2, 3], xs=[1, 2, 3])],
                    visualization_info=LineChartInfo(name="dummy", x_axis_label="x", y_axis_label="y"),
                )
            ],
        )

    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.TemporaryDirectory")
    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.ProjectRepo")
    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.MLFlowExperimentBinaryRepo")
    def test_push_placeholders(
        self,
        mock_repo,
        mock_project_repo,
        mock_tmp_dir,
        fxt_project,
        fxt_project_identifier,
        fxt_job_metadata,
        fxt_organization_id,
        tmp_path: Path,
    ) -> None:
        # Arrange
        mock_project_repo.return_value.get_by_id.return_value = fxt_project
        mock_repo.return_value.organization_id = fxt_organization_id
        mock_tmp_dir.return_value.__enter__.return_value = str(tmp_path)

        # Act
        adapter = GetiOTXInterfaceAdapter(project_identifier=fxt_project_identifier, job_metadata=fxt_job_metadata)
        adapter.push_placeholders()

        # Assert
        mock_repo.return_value.save_group.assert_called_once_with(source_directory=str(tmp_path))
        saved_file_names = {str(path.relative_to(tmp_path)) for path in tmp_path.glob("**/.placeholder")}
        assert saved_file_names == {
            os.path.join("jobs", fxt_job_metadata.id, "inputs", ".placeholder"),
            os.path.join("jobs", fxt_job_metadata.id, "live_metrics", ".placeholder"),
            os.path.join("jobs", fxt_job_metadata.id, "outputs", "models", ".placeholder"),
            os.path.join("jobs", fxt_job_metadata.id, "outputs", "exportable_codes", ".placeholder"),
            os.path.join("jobs", fxt_job_metadata.id, "outputs", "configurations", ".placeholder"),
            os.path.join("jobs", fxt_job_metadata.id, "outputs", "logs", ".placeholder"),
        }

    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.TemporaryDirectory")
    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.ProjectRepo")
    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.MLFlowExperimentBinaryRepo")
    def test_push_metadata(
        self,
        mock_repo,
        mock_project_repo,
        mock_tmp_dir,
        fxt_project,
        fxt_project_identifier,
        fxt_job_metadata,
        fxt_organization_id,
        tmp_path: Path,
    ) -> None:
        # Arrange
        mock_project_repo.return_value.get_by_id.return_value = fxt_project
        mock_repo.return_value.organization_id = fxt_organization_id
        mock_tmp_dir.return_value.__enter__.return_value = str(tmp_path)

        # Act
        adapter = GetiOTXInterfaceAdapter(project_identifier=fxt_project_identifier, job_metadata=fxt_job_metadata)
        adapter.push_metadata()

        # Assert
        mock_repo.return_value.save_group.assert_called_once_with(source_directory=str(tmp_path))
        saved_file_names = {str(path.relative_to(tmp_path)) for path in tmp_path.glob("**/*.json")}
        assert saved_file_names == {
            os.path.join("jobs", fxt_job_metadata.id, "metadata.json"),
            os.path.join("jobs", fxt_job_metadata.id, "project.json"),
            os.path.join("jobs", fxt_job_metadata.id, "run_info.json"),
            os.path.join("jobs", fxt_job_metadata.id, "live_metrics", "progress.json"),
        }

    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.ModelRepo")
    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.ProjectRepo")
    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.MLFlowExperimentBinaryRepo")
    def test_push_input_model(
        self,
        mock_repo,
        mock_project_repo,
        mock_model_repo,
        fxt_project,
        fxt_project_identifier,
        fxt_job_metadata,
        fxt_organization_id,
    ) -> None:
        # Arrange
        mock_project_repo.return_value.get_by_id.return_value = fxt_project
        mock_repo.return_value.organization_id = fxt_organization_id

        mock_model_repo.return_value = MagicMock(spec=ModelRepo)
        mock_model_binary_repo = MagicMock()
        mock_model_repo.return_value.binary_repo = mock_model_binary_repo

        mock_data_source = MagicMock(spec=DataSource)
        mock_src_filename = "dummy.pth"
        mock_data_source.binary_filename = mock_src_filename

        mock_model_adapter = MagicMock()
        mock_model_adapter.data_source = mock_data_source

        mock_model = MagicMock(spec=Model)
        mock_model.optimization_type = ModelOptimizationType.NONE
        mock_model.has_trained_weights.return_value = True
        mock_model.model_adapters = {"weights.pth": mock_model_adapter}

        # Act
        adapter = GetiOTXInterfaceAdapter(project_identifier=fxt_project_identifier, job_metadata=fxt_job_metadata)
        adapter.push_input_model(model=mock_model)

        # Assert
        mock_repo.return_value.copy_from.assert_called_once_with(
            model_binary_repo=mock_model_binary_repo,
            src_filename=mock_src_filename,
            dst_filepath=os.path.join("jobs", fxt_job_metadata.id, "inputs", "model.pth"),
        )

    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.ModelRepo")
    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.ProjectRepo")
    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.MLFlowExperimentBinaryRepo")
    def test_push_optimized_input_model(
        self,
        mock_repo,
        mock_project_repo,
        mock_model_repo,
        fxt_project,
        fxt_project_identifier,
        fxt_job_metadata,
        fxt_organization_id,
    ) -> None:
        # Arrange
        mock_project_repo.return_value.get_by_id.return_value = fxt_project
        mock_repo.return_value.organization_id = fxt_organization_id

        mock_model_repo.return_value = MagicMock(spec=ModelRepo)
        mock_model_binary_repo = MagicMock()
        mock_model_repo.return_value.binary_repo = mock_model_binary_repo

        mock_bin_data_source = MagicMock(spec=DataSource)
        mock_bin_src_filename = "dummy.bin"
        mock_bin_data_source.binary_filename = mock_bin_src_filename
        mock_xml_data_source = MagicMock(spec=DataSource)
        mock_xml_src_filename = "dummy.xml"
        mock_xml_data_source.binary_filename = mock_xml_src_filename

        mock_bin_model_adapter = MagicMock()
        mock_bin_model_adapter.data_source = mock_bin_data_source
        mock_xml_model_adapter = MagicMock()
        mock_xml_model_adapter.data_source = mock_xml_data_source

        mock_model = MagicMock(spec=Model)
        mock_model.optimization_type = ModelOptimizationType.MO
        mock_model.has_trained_weights.return_value = True
        mock_model.model_adapters = {
            OPENVINO_BIN_KEY: mock_bin_model_adapter,
            OPENVINO_XML_KEY: mock_xml_model_adapter,
        }

        # Act
        adapter = GetiOTXInterfaceAdapter(project_identifier=fxt_project_identifier, job_metadata=fxt_job_metadata)
        adapter.push_input_model(model=mock_model)

        # Assert
        mock_repo.return_value.copy_from.assert_has_calls(
            [
                call(
                    model_binary_repo=mock_model_binary_repo,
                    src_filename=mock_xml_src_filename,
                    dst_filepath=os.path.join("jobs", fxt_job_metadata.id, "inputs", OPENVINO_XML_KEY),
                ),
                call(
                    model_binary_repo=mock_model_binary_repo,
                    src_filename=mock_bin_src_filename,
                    dst_filepath=os.path.join("jobs", fxt_job_metadata.id, "inputs", OPENVINO_BIN_KEY),
                ),
            ]
        )

    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.TemporaryDirectory")
    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.ProjectRepo")
    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.MLFlowExperimentBinaryRepo")
    def test_push_input_configuration(
        self,
        mock_repo,
        mock_project_repo,
        mock_tmp_dir,
        fxt_project,
        fxt_project_identifier,
        fxt_job_metadata,
        fxt_organization_id,
        fxt_label_schema,
        tmp_path: Path,
    ) -> None:
        # Arrange
        mock_project_repo.return_value.get_by_id.return_value = fxt_project
        mock_repo.return_value.organization_id = fxt_organization_id
        mock_tmp_dir.return_value.__enter__.return_value = str(tmp_path)

        # Act
        adapter = GetiOTXInterfaceAdapter(project_identifier=fxt_project_identifier, job_metadata=fxt_job_metadata)
        adapter.push_input_configuration(
            model_template_id="dummy_id",
            hyper_parameters={"dummy": {"params": 1}},
            export_parameters={"export": [{"a": "b"}]},
            label_schema=fxt_label_schema,
        )

        # Assert
        mock_repo.return_value.save_group.assert_called_once_with(source_directory=str(tmp_path))
        saved_file_names = set(tmp_path.glob("**/*.json"))
        expected_path = Path(tmp_path) / "jobs" / fxt_job_metadata.id / "inputs" / "config.json"
        assert saved_file_names == {expected_path}

        with expected_path.open("r") as fp:
            config_dict = json.load(fp)

        assert config_dict["sub_task_type"] == ClsSubTaskType.MULTI_CLASS_CLS

    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.TemporaryDirectory")
    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.ProjectRepo")
    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.MLFlowExperimentBinaryRepo")
    def test_push_input_dataset(
        self,
        mock_repo,
        mock_project_repo,
        mock_tmp_dir,
        fxt_project,
        fxt_project_identifier,
        fxt_job_metadata,
        fxt_organization_id,
        tmp_path: Path,
    ) -> None:
        # Arrange
        mock_project_repo.return_value.get_by_id.return_value = fxt_project
        mock_repo.return_value.organization_id = fxt_organization_id

        upload_tmp_dir = tmp_path / "upload"
        mock_tmp_dir.return_value.__enter__.return_value = str(upload_tmp_dir)

        fname = "shard-0-of-1.arrow"
        local_path = Path(tmp_path) / fname
        with local_path.open("wb") as fp:
            fp.write(b"data")

        # Act
        adapter = GetiOTXInterfaceAdapter(project_identifier=fxt_project_identifier, job_metadata=fxt_job_metadata)
        adapter.push_input_dataset(shard_file_local_path=local_path)

        # Assert
        mock_repo.return_value.save_group.assert_called_once_with(source_directory=str(upload_tmp_dir))
        saved_file_names = {str(path.relative_to(upload_tmp_dir)) for path in upload_tmp_dir.glob("**/*.arrow")}
        assert saved_file_names == {os.path.join("jobs", fxt_job_metadata.id, "inputs", fname)}

    @pytest.mark.parametrize("has_additional_model_artifacts", [True, False])
    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.ModelRepo")
    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.ProjectRepo")
    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.MLFlowExperimentBinaryRepo")
    def test_update_output_models(
        self,
        mock_repo,
        mock_project_repo,
        mock_model_repo,
        fxt_project,
        fxt_project_identifier,
        fxt_job_metadata,
        fxt_organization_id,
        has_additional_model_artifacts: bool,
    ) -> None:
        # Arrange
        mock_project_repo.return_value.get_by_id.return_value = fxt_project
        mock_repo.return_value.organization_id = fxt_organization_id
        mock_repo.return_value.get_by_filename.return_value = b"data"
        if has_additional_model_artifacts:
            mock_repo.return_value.exists.return_value = True
        else:
            mock_repo.return_value.exists.return_value = False

        def _return_as_is(model_binary_repo, src_filepath) -> str:
            return os.path.basename(src_filepath)

        mock_repo.return_value.copy_to.side_effect = _return_as_is

        mock_model_repo.return_value = MagicMock(spec=ModelRepo)

        mock_base_model = MagicMock(spec=Model)
        mock_base_model.model_status = ModelStatus.NOT_READY
        mock_base_model.model_format = ModelFormat.BASE_FRAMEWORK
        mock_base_model.precision = [ModelPrecision.FP32]
        mock_base_model.has_xai_head = True

        mock_ov_model = MagicMock(spec=Model)
        mock_ov_model.model_status = ModelStatus.NOT_READY
        mock_ov_model.model_format = ModelFormat.OPENVINO
        mock_ov_model.precision = [ModelPrecision.FP16]
        mock_ov_model.has_xai_head = False

        mock_onnx_model = MagicMock(spec=Model)
        mock_onnx_model.model_status = ModelStatus.NOT_READY
        mock_onnx_model.model_format = ModelFormat.ONNX
        mock_onnx_model.precision = [ModelPrecision.FP32]
        mock_onnx_model.has_xai_head = False

        models_to_update = [
            mock_base_model,
            mock_ov_model,
            mock_onnx_model,
        ]

        # Act
        adapter = GetiOTXInterfaceAdapter(project_identifier=fxt_project_identifier, job_metadata=fxt_job_metadata)
        adapter.update_output_models(models_to_update=models_to_update)

        # Assert
        # BASE_FRAMEWORK
        called_set_data_keys = {call_args.kwargs.get("key") for call_args in mock_base_model.set_data.call_args_list}
        expected_set_data_keys = {"weights.pth"}
        assert expected_set_data_keys == called_set_data_keys

        # ONNX
        called_set_data_keys = {call_args.kwargs.get("key") for call_args in mock_onnx_model.set_data.call_args_list}
        expected_set_data_keys = {"model.onnx"}
        assert expected_set_data_keys == called_set_data_keys

        # OpenVINO
        called_set_data_keys = {call_args.kwargs.get("key") for call_args in mock_ov_model.set_data.call_args_list}
        expected_set_data_keys = {"openvino.xml", "openvino.bin"}
        if has_additional_model_artifacts:
            assert (
                expected_set_data_keys.union(["config.json", "tile_classifier.xml", "tile_classifier.bin"])
                == called_set_data_keys
            )
        else:
            assert expected_set_data_keys == called_set_data_keys
        assert "exportable-code" in mock_ov_model.exportable_code.binary_filename

        assert mock_base_model.model_status == ModelStatus.SUCCESS
        assert mock_ov_model.model_status == ModelStatus.SUCCESS
        assert mock_onnx_model.model_status == ModelStatus.SUCCESS

        called_filenames = {
            os.path.basename(call_args.kwargs.get("src_filepath"))
            for call_args in mock_repo.return_value.copy_to.call_args_list
        }
        expected_filenames = {
            "model_fp32_xai.pth",
            "model_fp16_non-xai.xml",
            "model_fp16_non-xai.bin",
            "exportable-code_fp16_non-xai.whl",
            "model_fp32_non-xai.onnx",
        }

        if has_additional_model_artifacts:
            assert (
                expected_filenames.union(
                    [
                        "config_fp16_non-xai.json",
                        "tile-classifier_fp16_non-xai.xml",
                        "tile-classifier_fp16_non-xai.bin",
                    ]
                )
                == called_filenames
            )
        else:
            assert expected_filenames == called_filenames

    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.ProjectRepo")
    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.MLFlowExperimentBinaryRepo")
    def test_pull_output_configuration(
        self,
        mock_repo,
        mock_project_repo,
        fxt_project,
        fxt_project_identifier,
        fxt_job_metadata,
        fxt_organization_id,
        fxt_configurable_parameters_1,
    ) -> None:
        # Arrange
        mock_project_repo.return_value.get_by_id.return_value = fxt_project
        mock_repo.return_value.organization_id = fxt_organization_id
        mock_repo.return_value.get_by_filename.return_value = json.dumps(
            convert(
                config=fxt_configurable_parameters_1,
                target=dict,
                enum_to_str=True,
                id_to_str=True,
            )
        ).encode()

        # Act
        adapter = GetiOTXInterfaceAdapter(project_identifier=fxt_project_identifier, job_metadata=fxt_job_metadata)
        configuration = adapter.pull_output_configuration()

        # Assert
        assert configuration == fxt_configurable_parameters_1

    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.ProjectRepo")
    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.MLFlowExperimentBinaryRepo")
    def test_pull_metrics(
        self,
        mock_repo,
        mock_project_repo,
        fxt_project,
        fxt_project_identifier,
        fxt_job_metadata,
        fxt_organization_id,
        fxt_performance: Performance,
    ) -> None:
        # Arrange
        mock_project_repo.return_value.get_by_id.return_value = fxt_project
        mock_repo.return_value.organization_id = fxt_organization_id
        performance_dict = {
            "dashboard_metrics": [
                {
                    "metrics": [{"name": "dummy", "type": "curve", "xs": [1.0, 2.0, 3.0], "ys": [1.0, 2.0, 3.0]}],
                    "visualization_info": {
                        "name": "dummy",
                        "palette": "DEFAULT",
                        "type": "LINE",
                        "x_axis_label": "x",
                        "y_axis_label": "y",
                    },
                }
            ],
            "score": {"label_id": None, "name": "dummy", "type": "score", "value": 1.0},
            "type": "Performance",
        }
        mock_repo.return_value.get_by_filename.return_value = json.dumps(performance_dict).encode()

        # Act
        adapter = GetiOTXInterfaceAdapter(project_identifier=fxt_project_identifier, job_metadata=fxt_job_metadata)
        performance = adapter.pull_metrics()

        # Assert
        assert performance == fxt_performance

    def test_pull_metrics_missing_file(self, fxt_project_identifier, fxt_job_metadata) -> None:
        # Arrange
        adapter = GetiOTXInterfaceAdapter(project_identifier=fxt_project_identifier, job_metadata=fxt_job_metadata)

        # Act
        performance = adapter.pull_metrics()

        # Assert
        assert performance is None

    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.MLFlowExperimentBinaryRepo")
    def test_pull_metrics_exception(
        self, mock_experiments_repo, fxt_organization_id, fxt_project_identifier, fxt_job_metadata
    ) -> None:
        # Arrange
        mock_experiments_repo.return_value.organization_id = fxt_organization_id
        mock_experiments_repo.return_value.get_by_filename.return_value = "data"
        adapter = GetiOTXInterfaceAdapter(project_identifier=fxt_project_identifier, job_metadata=fxt_job_metadata)

        # Act
        with patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.json.loads", side_effect=RuntimeError):
            performance = adapter.pull_metrics()

        # Assert
        assert performance is None

    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.ProjectRepo")
    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.MLFlowExperimentBinaryRepo")
    def test_pull_progress(
        self,
        mock_repo,
        mock_project_repo,
        fxt_project,
        fxt_project_identifier,
        fxt_job_metadata,
        fxt_organization_id,
    ) -> None:
        # Arrange
        mock_repo.return_value.get_by_filename.return_value = json.dumps({"progress": 1.0}).encode()

        # Act
        adapter = GetiOTXInterfaceAdapter(project_identifier=fxt_project_identifier, job_metadata=fxt_job_metadata)
        progress = adapter.pull_progress()

        # Assert
        assert progress == 1.0

    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.ProjectRepo")
    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.MLFlowExperimentBinaryRepo")
    def test_clean(
        self,
        mock_repo,
        mock_project_repo,
        fxt_project_identifier,
        fxt_job_metadata,
    ) -> None:
        # Act
        adapter = GetiOTXInterfaceAdapter(project_identifier=fxt_project_identifier, job_metadata=fxt_job_metadata)
        adapter.clean()

        # Assert
        mock_repo.return_value.delete_all_under_job_dir.assert_called_once_with(job_id=fxt_job_metadata.id)
