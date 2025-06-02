# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from mlflow import MlflowClient
from mlflow.entities import Run
from otx.algo.classification.vit import VisionTransformerForMulticlassCls
from otx.core.types.export import OTXExportFormatType
from otx.core.types.label import LabelInfo
from scripts.optimize import optimize
from scripts.utils import OTXConfig


@pytest.fixture()
def fxt_config(fxt_dir_assets):
    config_file_path = fxt_dir_assets / "pot_config.json"
    return OTXConfig.from_json_file(config_file_path)


@pytest.fixture()
def fxt_openvino_model(tmpdir):
    model = VisionTransformerForMulticlassCls(LabelInfo.from_num_classes(3))

    export_dir = Path(tmpdir)
    checkpoint_path = model.export(
        output_dir=export_dir,
        base_name="openvino",
        export_format=OTXExportFormatType.OPENVINO,
        to_exportable_code=False,
    )

    return checkpoint_path


# TODO (vinnamki): Remove this fixture after fixing
# CVS-142373
@pytest.fixture()
def fxt_exportable_code_side_effect(tmpdir):
    def side_effect(*args, **kwargs):
        model = VisionTransformerForMulticlassCls(LabelInfo.from_num_classes(3))

        export_dir = Path(tmpdir) / "export"
        checkpoint_path = model.export(
            output_dir=export_dir,
            base_name="exported_model",
            export_format=OTXExportFormatType.OPENVINO,
            to_exportable_code=True,
        )

        return checkpoint_path

    return side_effect


@patch("otx.engine.engine.Engine.export")
@patch("scripts.optimize.load_trained_model_weights")
def test_optimize(
    mock_load_trained_model_weights,
    mock_engine_export,
    fxt_config,
    fxt_dir_assets,
    fxt_exportable_code_side_effect,
    fxt_openvino_model,
    tmpdir,
):
    # Arrange
    mock_run = MagicMock(spec=Run)
    mock_client = MagicMock(spec=MlflowClient)
    mock_load_trained_model_weights.return_value = fxt_openvino_model
    mock_engine_export.side_effect = fxt_exportable_code_side_effect

    # Act
    optimize(
        config=fxt_config,
        client=mock_client,
        run=mock_run,
        dataset_dir=fxt_dir_assets,
        work_dir=Path(tmpdir),
    )

    # Assert
    logged_local_paths = [call_args.kwargs["artifact_path"] for call_args in mock_client.log_artifact.call_args_list]
    logged_local_names = {os.path.basename(path) for path in logged_local_paths}

    assert logged_local_names == {
        # OPENVINO INT8
        "model_int8-pot_non-xai.xml",
        "model_int8-pot_non-xai.bin",
        # Exportable codes
        "exportable-code_int8-pot_non-xai.whl",
    }

    keys = set()
    for call_args_list in mock_client.log_batch.call_args_list:
        for key in call_args_list.kwargs:
            keys.add(key)

    assert "tags" in keys  # ProgressUpdater uses tags
