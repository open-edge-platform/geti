# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module tests commands to create task train dataset"""

from unittest.mock import MagicMock, patch

import pytest
from geti_types import ID
from iai_core_py.entities.model import ModelStatus
from jobs_common_extras.mlflow.adapters.geti_otx_interface import GetiOTXInterfaceAdapter

from job.tasks.prepare_and_train.train_helpers import finalize_train, prepare_train


@pytest.mark.JobsComponent
class TestTrainHelpers:
    @patch("job.tasks.prepare_and_train.train_helpers.GetiOTXInterfaceAdapter")
    @patch("job.tasks.prepare_and_train.train_helpers.ModelRepo")
    def test_prepare_train(
        self,
        mock_model_repo,
        mock_geti_otx_interface_adapter,
        mock_train_data,
        fxt_dataset_with_images,
    ) -> None:
        # Arrange
        mock_model_repo.generate_id.side_effect = [ID(str(i)) for i in range(5)]

        # Act
        train_output_models = prepare_train(
            train_data=mock_train_data,
            dataset=fxt_dataset_with_images,
        )
        output_model_ids = train_output_models.to_train_output_model_ids()

        # Assert
        assert output_model_ids.base == "0"
        assert output_model_ids.mo_fp32_with_xai == "1"
        assert output_model_ids.mo_fp32_without_xai == "2"
        assert output_model_ids.mo_fp16_without_xai == "3"
        assert output_model_ids.onnx == "4"

        mock_geti_otx_interface_adapter.return_value.push_placeholders.assert_called_once()
        mock_geti_otx_interface_adapter.return_value.push_metadata.assert_called_once()
        mock_geti_otx_interface_adapter.return_value.push_input_configuration.assert_called_once()
        mock_geti_otx_interface_adapter.return_value.push_input_model.assert_called_once()

    @patch("job.tasks.prepare_and_train.train_helpers.TrainOutputModels.from_train_output_model_ids")
    @patch("jobs_common_extras.mlflow.utils.train_output_models.ModelRepo")
    @patch("jobs_common_extras.mlflow.utils.train_output_models.ModelService")
    def test_finalize_train(
        self,
        mock_model_service,
        mock_model_repo,
        mock_from_train_output_model_ids,
        mock_train_data,
        fxt_train_output_model_ids,
        fxt_train_output_models,
        fxt_configurable_parameters_1,
    ) -> None:
        # Arrange
        mock_from_train_output_model_ids.return_value = fxt_train_output_models
        mock_geti_otx_interface_adapter = MagicMock(spec=GetiOTXInterfaceAdapter)
        mock_geti_otx_interface_adapter.pull_output_configuration.return_value = fxt_configurable_parameters_1

        # Act
        with patch.object(
            GetiOTXInterfaceAdapter,
            "__new__",
            return_value=mock_geti_otx_interface_adapter,
        ):
            finalize_train(
                train_data=mock_train_data,
                train_output_model_ids=fxt_train_output_model_ids,
            )

        # Assert
        mock_geti_otx_interface_adapter.clean.assert_called_once()
        mock_geti_otx_interface_adapter.update_output_models.assert_called_once()
        mock_geti_otx_interface_adapter.pull_metrics.assert_called_once()

        for model, call_args in zip(
            fxt_train_output_models.get_all_models(), mock_model_repo.return_value.update_model_status.call_args_list
        ):
            assert call_args.kwargs["model"] == model
            assert call_args.kwargs["model_status"] == ModelStatus.TRAINED_NO_STATS

        mock_geti_otx_interface_adapter.pull_output_configuration.assert_not_called()
