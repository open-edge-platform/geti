# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.
import json
import os
import tempfile
from unittest.mock import ANY, MagicMock, patch

import pytest

from service.model_converter import LARGE_MODEL_THRESHOLD_BYTES, GraphVariant, ModelConverter


@pytest.fixture
def mock_s3client():
    return MagicMock()


@pytest.fixture
def model_converter(mock_s3client) -> ModelConverter:
    return ModelConverter(s3client=mock_s3client)


@pytest.fixture
def mock_project():
    return MagicMock()


@pytest.fixture
def sample_models():
    return [
        MagicMock(model_id="model1", task_id="task3"),
        MagicMock(model_id="model2", task_id="task2"),
    ]


@pytest.fixture
def sample_project():
    return MagicMock(
        id="project",
        pipeline=MagicMock(
            tasks=[
                MagicMock(id="task1", task_type="DATASET"),
                MagicMock(
                    id="task2",
                    task_type="CLASSIFICATION",
                    labels=[
                        MagicMock(id="label_id_1", is_empty=False),
                        MagicMock(id="label_id_2", is_empty=False),
                        MagicMock(id="label_id_3", is_empty=False),
                        MagicMock(id="label_id_4", is_empty=True),
                    ],
                ),
                MagicMock(id="task3", task_type="DETECTION"),
                MagicMock(id="task4", task_type="CROP"),
            ],
            connections=[
                MagicMock(from_id="task1", to_id="task2"),
                MagicMock(from_id="task2", to_id="task3"),
                MagicMock(from_id="task3", to_id="task4"),
                MagicMock(from_id="task4", to_id="task5"),
            ],
        ),
    )


@patch("service.model_converter.ElementTree.parse")
def test_get_labels(mock_parse, model_converter, sample_project):
    mock_root = MagicMock()
    mock_parse.return_value.getroot.return_value = mock_root
    mock_root.find.return_value.get.return_value = "label_id_3 label_id_1 label_id_2 label_id_4"
    sample_project.pipeline.tasks[1].labels[0].name = "label_1"
    sample_project.pipeline.tasks[1].labels[1].name = "label_2"
    sample_project.pipeline.tasks[1].labels[2].name = "label_3"
    sample_project.pipeline.tasks[1].labels[3].name = "Empty"

    labels = model_converter._get_labels("task2", sample_project, "path")
    assert labels == ["label_3", "label_1", "label_2", "Empty"]


def test_delete_file(model_converter):
    file_path = "/tmp/file"
    with patch("os.remove") as mock_remove:
        model_converter._delete_file(file_path)
        mock_remove.assert_called_with(file_path)

        model_converter._delete_file(file_path)
        assert mock_remove.call_count == 2


def test_delete_dir(model_converter):
    dir_path = "/tmp/model_dir"
    with patch("shutil.rmtree") as mock_rmtree:
        model_converter._delete_dir(dir_path)
        mock_rmtree.assert_called_once_with(dir_path)
        model_converter._delete_dir(dir_path)
        assert mock_rmtree.call_count == 2


def test_get_empty_label(model_converter):
    mock_project = MagicMock(
        pipeline=MagicMock(
            tasks=[
                MagicMock(id="task_0"),
                MagicMock(id="task_1"),
                MagicMock(
                    id="task_1",
                    labels=[MagicMock(id="label_1", is_empty=False), MagicMock(id="label_2", is_empty=True)],
                ),
            ]
        )
    )
    mock_project.pipeline.tasks[2].labels[0].name = "Label"
    mock_project.pipeline.tasks[2].labels[1].name = "Empty"

    result = model_converter._get_empty_label("task_1", mock_project)
    assert result == ("label_2", "Empty")


def test_get_empty_label_empty_project(model_converter):
    mock_project = MagicMock()
    result = model_converter._get_empty_label("task", mock_project)
    assert result is None


def test_get_models_ordered(model_converter, sample_project, sample_models):
    models_ordered = model_converter._get_models_ordered(sample_project, [sample_models[0]])
    assert models_ordered == [sample_models[0]]
    models_ordered = model_converter._get_models_ordered(sample_project, sample_models)
    assert models_ordered == [sample_models[1], sample_models[0]]


def test_get_graph_type_chain(model_converter, sample_project, sample_models):
    graph = model_converter._get_graph_type(sample_project, [sample_models[0]])
    assert graph == "DETECTION"
    graph = model_converter._get_graph_type(sample_project, [sample_models[1]])
    assert graph == "CLASSIFICATION"
    graph = model_converter._get_graph_type(sample_project, sample_models)
    assert graph == "CHAIN_CLASSIFICATION_DETECTION"


@pytest.mark.parametrize("num_streams", [1, 2])
def test_create_subconfig(model_converter, sample_project, sample_models, num_streams):
    with tempfile.TemporaryDirectory() as path:
        model_converter._create_subconfig(path, sample_models, num_streams)
        with open(os.path.join(path, "config.json")) as f:
            content = json.load(f)
        print(content)
        assert "model_config_list" in content
        assert "config" in content["model_config_list"][0]
        assert "name" in content["model_config_list"][0]["config"]
        assert content["model_config_list"][0]["config"]["name"] == "model1"
        assert "plugin_config" in content["model_config_list"][0]["config"]
        assert "NUM_STREAMS" in content["model_config_list"][0]["config"]["plugin_config"]
        assert f"{num_streams}" in content["model_config_list"][0]["config"]["plugin_config"]["NUM_STREAMS"]


@pytest.mark.parametrize(
    "graph_type, module",
    [
        ("CLASSIFICATION", "ClassificationModel"),
        ("DETECTION", "DetectionModel"),
        ("KEYPOINT_DETECTION", "KeypointDetectionModel"),
        ("ROTATED_DETECTION", "MaskRCNNModel"),
        ("SEGMENTATION", "SegmentationModel"),
        ("INSTANCE_SEGMENTATION", "MaskRCNNModel"),
        ("ANOMALY_CLASSIFICATION", "AnomalyDetection"),
        ("ANOMALY_DETECTION", "AnomalyDetection"),
        ("ANOMALY_SEGMENTATION", "AnomalyDetection"),
    ],
)
@patch("service.model_converter.ElementTree.parse")
def test_convert_model(mock_parse, model_converter, sample_project, sample_models, graph_type, module):
    mock_root = MagicMock()
    mock_parse.return_value.getroot.return_value = mock_root
    mock_root.find.return_value.get.return_value = "label_id"
    with patch("service.model_converter." + module + ".create_model") as create_model, patch("os.makedirs") as makedirs:
        sample_project.pipeline.tasks[2].task_type = graph_type
        model_converter._convert_model("/model", "/export", sample_models[0], sample_project)
        assert create_model.call_count == 1
        assert makedirs.call_count == 1


@patch("service.model_converter.ElementTree.parse")
def test_convert_model_failed(mock_parse, model_converter, sample_project, sample_models):
    mock_root = MagicMock()
    mock_parse.return_value.getroot.return_value = mock_root
    mock_root.find.return_value.get.return_value = "label_id"
    with pytest.raises(Exception):
        sample_project.pipeline.tasks[2].task_type = "NOT_SUPPORTED"
        model_converter._convert_model("/model", "/export", sample_models[0], sample_project)


def test_check_dir_size(tmp_path, model_converter: ModelConverter):
    test_dir = tmp_path / "test"
    test_dir.mkdir()
    with open(test_dir / "test_file", "wb") as f:
        f.write(bytes(8192))

    assert model_converter._check_dir_size(test_dir) == 8192


@patch("service.model_converter.urllib.request.urlretrieve")
@pytest.mark.parametrize("graph_variant", [GraphVariant.INFERENCE, GraphVariant.OVMS_DEPLOYMENT])
@pytest.mark.parametrize("model_size", [LARGE_MODEL_THRESHOLD_BYTES - 100, LARGE_MODEL_THRESHOLD_BYTES + 100])
def test_prepare_graph(sample_project, sample_models, graph_variant, model_size, model_converter: ModelConverter):
    create_ovms_graph_files_mock = MagicMock(spec=model_converter._create_ovms_graph_files)
    model_converter._create_ovms_graph_files = create_ovms_graph_files_mock

    check_dir_size_mock = MagicMock(model_converter._check_dir_size, return_value=model_size)
    model_converter._check_dir_size = check_dir_size_mock

    create_subconfig_mock = MagicMock(model_converter._create_subconfig)
    model_converter._create_subconfig = create_subconfig_mock

    create_graph_mock = MagicMock(model_converter._create_graph)
    model_converter._create_graph = create_graph_mock

    model_converter.prepare_graph(project=sample_project, models=sample_models, graph_variant=graph_variant)

    assert create_ovms_graph_files_mock.call_count == (1 if graph_variant == GraphVariant.OVMS_DEPLOYMENT else 0)
    assert check_dir_size_mock.call_count == 1
    create_subconfig_mock.assert_called_once_with(
        ANY, ANY, num_streams=1 if model_size > LARGE_MODEL_THRESHOLD_BYTES else 2
    )
    assert create_graph_mock.call_count == 1


def test_create_ovms_graph_files(model_converter: ModelConverter, sample_project, tmp_path):
    # Prepare exported model files structure
    root_dir = tmp_path / "test-model"
    root_dir.mkdir()

    config_json = root_dir / "config.json"
    config_json.write_text("foo", encoding="utf-8")

    model_dir = root_dir / "1234-model" / "1"
    model_dir.mkdir(parents=True)

    model_xml = model_dir / "model.xml"
    model_xml.write_text("</foo>", encoding="utf-8")
    model_bin = model_dir / "model.bin"
    model_bin.write_text("0x0", encoding="utf-8")

    model_converter._create_ovms_graph_files(export_dir=root_dir, project=sample_project)

    assert (root_dir / "config.json").exists()
    assert (root_dir / f"{sample_project.id}-graph").exists()
    assert (root_dir / f"{sample_project.id}-graph" / "subconfig.json").exists()
    assert (root_dir / f"{sample_project.id}-graph" / "1234-model" / "1" / "model.xml").exists()
    assert (root_dir / f"{sample_project.id}-graph" / "1234-model" / "1" / "model.bin").exists()


def test_render_ovms_package_docs(model_converter: ModelConverter, tmp_path):
    # Prepare exported model files structure
    root_dir = tmp_path / "test-package-docs"
    root_dir.mkdir()

    template_file = root_dir / "readme_template.md"
    template_file.write_text("use OVMS_IMAGE_PLACEHOLDER image on GRAPH_NAME_PLACEHOLDER model", encoding="utf-8")

    output_path = root_dir / "README.md"
    graph_name = "test-graph"
    ovms_image = "ovms/test:latest"
    model_converter._render_ovms_package_docs(
        template_path=template_file, output_path=output_path, graph_name=graph_name, ovms_image=ovms_image
    )

    with open(output_path) as output_file:
        output_content = output_file.read()

    assert "OVMS_IMAGE_PLACEHOLDER" not in output_content
    assert "GRAPH_NAME_PLACEHOLDER" not in output_content

    assert graph_name in output_content
    assert ovms_image in output_content
