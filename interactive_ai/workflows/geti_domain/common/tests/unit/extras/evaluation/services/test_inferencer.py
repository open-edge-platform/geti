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
import io
import json
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest
from geti_types import ID
from model_api.adapters import OpenvinoAdapter
from model_api.models import ImageModel, SAMDecoder, SAMImageEncoder, SAMLearnableVisualPrompter
from model_api.models.utils import AnomalyResult, ClassificationResult, DetectedKeypoints, ImageResultWithSoftPrediction
from model_api.tilers import DetectionTiler, InstanceSegmentationTiler
from sc_sdk.entities.annotation import AnnotationScene
from sc_sdk.entities.image import Image
from sc_sdk.entities.label import Domain
from sc_sdk.entities.label_schema import LabelGroup, LabelSchema
from sc_sdk.entities.media import MediaPreprocessing, MediaPreprocessingStatus
from sc_sdk.entities.model import Model, ModelConfiguration, ModelStatus, TrainingFramework, TrainingFrameworkType
from sc_sdk.entities.tensor import Tensor
from sc_sdk.repos.metadata_repo import FloatMetadata

from jobs_common_extras.evaluation.services.inferencer import (
    AnomalyInferencer,
    ClassificationInferencer,
    DetectionInferencer,
    InstanceSegmentationInferencer,
    KeypointDetectionInferencer,
    RotatedDetectionInferencer,
    SemanticSegmentationInferencer,
    VisualPromptingInferencer,
)
from jobs_common_extras.evaluation.services.prediction_to_annotation_converter import (
    AnomalyToAnnotationConverter,
    ClassificationToAnnotationConverter,
    DetectionToAnnotationConverter,
    InstanceSegmentationToAnnotationConverter,
    KeypointToAnnotationConverter,
    RotatedRectToAnnotationConverter,
    SemanticSegmentationToAnnotationConverter,
    VisualPromptingToAnnotationConverter,
)
from jobs_common_extras.evaluation.utils.metadata_utils import Metadata


def return_none(*args, **kwargs) -> None:
    return None


@pytest.fixture
def fxt_anomaly_label_schema(fxt_anomaly_labels_factory):
    anomaly_labels = fxt_anomaly_labels_factory(Domain.ANOMALY_CLASSIFICATION)
    label_schema = LabelSchema(id_=ID("anomaly_label_schema_id"))
    label_group = LabelGroup(labels=anomaly_labels, name="dummy anomaly classification label group")
    label_schema.add_group(label_group)
    yield label_schema


@pytest.fixture
def fxt_keypoint_detection_label_schema(fxt_keypoint_label):
    label_schema = LabelSchema(id_=ID("anomaly_label_schema_id"))
    label_group = LabelGroup(labels=fxt_keypoint_label, name="dummy keypoint detection label group")
    label_schema.add_group(label_group)
    yield label_schema


@pytest.fixture
def fxt_model_with_adapters(
    fxt_project,
    fxt_dataset_non_empty,
    fxt_model_storage,
    fxt_configuration,
    fxt_label_schema,
    fxt_mongo_id,
):
    yield Model(
        project=fxt_project,
        model_storage=fxt_model_storage,
        train_dataset=fxt_dataset_non_empty,
        configuration=ModelConfiguration(fxt_configuration.data, fxt_label_schema),
        id_=fxt_mongo_id(1),
        data_source_dict={
            "openvino.xml": b"DUMMY_MODEL_XML",
            "openvino.bin": b"DUMMY_MODEL_WEIGHT",
        },
        model_status=ModelStatus.NOT_IMPROVED,
    )


@pytest.fixture
def fxt_legacy_model(
    fxt_project,
    fxt_dataset_non_empty,
    fxt_model_storage,
    fxt_configuration,
    fxt_label_schema,
    fxt_mongo_id,
):
    yield Model(
        project=fxt_project,
        model_storage=fxt_model_storage,
        train_dataset=fxt_dataset_non_empty,
        configuration=ModelConfiguration(fxt_configuration.data, fxt_label_schema),
        id_=fxt_mongo_id(1),
        data_source_dict={
            "openvino.xml": b"DUMMY_LEGACY_MODEL_XML",
            "openvino.bin": b"DUMMY_LEGACY_MODEL_WEIGHT",
        },
        model_status=ModelStatus.NOT_IMPROVED,
        training_framework=TrainingFramework(type=TrainingFrameworkType.OTX, version="1.6.2"),
    )


@pytest.fixture
def fxt_anomaly_model_with_adapters(
    fxt_project,
    fxt_dataset_non_empty,
    fxt_model_storage,
    fxt_configuration,
    fxt_anomaly_label_schema,
    fxt_mongo_id,
):
    yield Model(
        project=fxt_project,
        model_storage=fxt_model_storage,
        train_dataset=fxt_dataset_non_empty,
        configuration=ModelConfiguration(fxt_configuration.data, fxt_anomaly_label_schema),
        id_=fxt_mongo_id(1),
        data_source_dict={
            "openvino.xml": b"DUMMY_MODEL_XML",
            "openvino.bin": b"DUMMY_MODEL_WEIGHT",
        },
        model_status=ModelStatus.NOT_IMPROVED,
    )


@pytest.fixture
def fxt_keypoint_detection_model_with_adapters(
    fxt_project,
    fxt_dataset_non_empty,
    fxt_model_storage,
    fxt_configuration,
    fxt_keypoint_detection_label_schema,
    fxt_mongo_id,
):
    yield Model(
        project=fxt_project,
        model_storage=fxt_model_storage,
        train_dataset=fxt_dataset_non_empty,
        configuration=ModelConfiguration(fxt_configuration.data, fxt_keypoint_detection_label_schema),
        id_=fxt_mongo_id(1),
        data_source_dict={
            "openvino.xml": b"DUMMY_MODEL_XML",
            "openvino.bin": b"DUMMY_MODEL_WEIGHT",
        },
        model_status=ModelStatus.NOT_IMPROVED,
    )


@pytest.fixture
def fxt_model_with_tiling_adapters(
    fxt_project,
    fxt_dataset_non_empty,
    fxt_model_storage,
    fxt_configuration,
    fxt_label_schema,
    fxt_mongo_id,
):
    yield Model(
        project=fxt_project,
        model_storage=fxt_model_storage,
        train_dataset=fxt_dataset_non_empty,
        configuration=ModelConfiguration(fxt_configuration.data, fxt_label_schema),
        id_=fxt_mongo_id(1),
        data_source_dict={
            "openvino.xml": b"DUMMY_MODEL_XML",
            "openvino.bin": b"DUMMY_MODEL_WEIGHT",
            "tile_classifier.xml": b"DUMMY_TILE_CLASSIFIER_XML",
            "tile_classifier.bin": b"DUMMY_TILE_CLASSIFIER_WEIGHT",
        },
        model_status=ModelStatus.NOT_IMPROVED,
    )


@pytest.fixture
def fxt_reference_feature_vector():
    yield np.zeros((1, 56))


@pytest.fixture
def fxt_reference_feature_vector_npz(fxt_reference_feature_vector):
    buffer = io.BytesIO()
    np.savez(buffer, array=fxt_reference_feature_vector)
    yield buffer.getvalue()


@pytest.fixture
def fxt_model_with_sam_adapters(
    fxt_project,
    fxt_dataset_non_empty,
    fxt_model_storage,
    fxt_configuration,
    fxt_label_schema,
    fxt_mongo_id,
    fxt_label,
    fxt_reference_feature_vector,
    fxt_reference_feature_vector_npz,
):
    numpy_filename = f"reference_feature_{fxt_label.id_}.npz"
    reference_feature_dict = {
        fxt_label.id_: {
            "label_id": fxt_label.id_,
            "name": fxt_label.name,
            "color": fxt_label.color.hex_str,
            "numpy_filename": numpy_filename,
        }
    }

    yield Model(
        project=fxt_project,
        model_storage=fxt_model_storage,
        train_dataset=fxt_dataset_non_empty,
        configuration=ModelConfiguration(fxt_configuration.data, fxt_label_schema),
        id_=fxt_mongo_id(1),
        data_source_dict={
            "encoder.xml": b"DUMMY_ENCODER_MODEL_XML",
            "encoder.bin": b"DUMMY_ENCODER_MODEL_WEIGHT",
            "decoder.xml": b"DUMMY_DECODER_MODEL_XML",
            "decoder.bin": b"DUMMY_DECODER_MODEL_WEIGHT",
            "reference_features.json": json.dumps(reference_feature_dict).encode(),
            numpy_filename: fxt_reference_feature_vector_npz,
        },
        model_status=ModelStatus.NOT_IMPROVED,
    )


@pytest.fixture
def fxt_model_api_image_model():
    image_model = MagicMock()
    image_model.preprocess = lambda image: (image, None)
    yield image_model


@pytest.fixture
def fxt_image(fxt_ote_id) -> Image:
    return Image(
        name="dummy_image.jpg",
        uploader_id="dummy_name",
        id=fxt_ote_id(1),
        width=100,
        height=100,
        size=100,
        preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
    )


@pytest.mark.JobsComponent
class TestInferencer:
    def test_classification_inferencer(
        self, fxt_dataset_storage, fxt_model_with_adapters, fxt_image, fxt_model_api_image_model
    ) -> None:
        mock_feature_vector = np.zeros((1, 10, 1, 1))
        mock_saliency_map = np.zeros((1, 2, 7, 7))
        mock_pred_label = (1, "zebra", 0.81544286)
        mock_scores = [0.18455714, 0.81544286]
        image_numpy_data = np.zeros(shape=(100, 100, 3))
        fxt_model_api_image_model.postprocess.return_value = ClassificationResult(
            top_labels=[mock_pred_label],
            raw_scores=mock_scores,
            feature_vector=mock_feature_vector,
            saliency_map=mock_saliency_map,
        )
        with (
            patch.object(
                OpenvinoAdapter,
                "__init__",
                new=return_none,
            ),
            patch.object(
                OpenvinoAdapter,
                "get_rt_info",
                return_value=None,
            ),
            patch.object(
                ImageModel,
                "create_model",
                return_value=fxt_model_api_image_model,
            ),
            patch.object(
                ClassificationToAnnotationConverter,
                "convert_to_annotations",
                return_value=[],
            ) as mock_convert_to_annotations,
            patch(
                "jobs_common_extras.evaluation.services.inferencer.get_media_roi_numpy",
                return_value=image_numpy_data,
            ) as mock_get_media_roi_numpy,
        ):
            inferencer = ClassificationInferencer(model=fxt_model_with_adapters)
            predicted_scene, metadata = inferencer.predict(
                dataset_storage_id=fxt_dataset_storage.identifier, media=fxt_image
            )

        mock_convert_to_annotations.assert_called_once()
        assert isinstance(predicted_scene, AnnotationScene)
        assert any(m for m in metadata if isinstance(m, Tensor) and m.name == Metadata.REPRESENTATION_VECTOR.value)
        assert any(m for m in metadata if isinstance(m, FloatMetadata) and m.name == Metadata.ACTIVE_SCORE.value)
        mock_get_media_roi_numpy.assert_called_once()

    @pytest.mark.parametrize(
        "enable_tiling, lazyfxt_model",
        (
            [True, "fxt_model_with_adapters"],
            [True, "fxt_legacy_model"],
            [False, "fxt_model_with_adapters"],
            [False, "fxt_legacy_model"],
        ),
    )
    def test_detection_inferencer(
        self, enable_tiling, lazyfxt_model, request, fxt_dataset_storage, fxt_image, fxt_model_api_image_model
    ) -> None:
        # Arrange
        model_config = {
            "tiling_parameters": {
                "enable_tiling": enable_tiling,
            }
        }
        image_numpy_data = np.zeros(shape=(100, 100, 3))
        dummy_tiler = MagicMock()
        model = request.getfixturevalue(lazyfxt_model)

        # Act
        with (
            patch.object(
                OpenvinoAdapter,
                "__init__",
                new=return_none,
            ),
            patch.object(
                ImageModel,
                "create_model",
                return_value=fxt_model_api_image_model,
            ),
            patch(
                "jobs_common_extras.evaluation.services.inferencer.get_legacy_detection_inferencer_configuration",
                return_value=model_config,
            ) as mock_det_config,
            patch(
                "jobs_common_extras.evaluation.services.inferencer.get_tiling_parameters",
                return_value=model_config["tiling_parameters"],
            ) as mock_tiling_param,
            patch(
                "jobs_common_extras.evaluation.services.inferencer.get_tiler_configuration",
                return_value={},
            ) as mock_get_tiler_configuration,
            patch.object(
                DetectionToAnnotationConverter,
                "convert_to_annotations",
                return_value=[],
            ) as mock_convert_to_annotations,
            patch.object(
                DetectionTiler,
                "__init__",
                new=return_none,
            ),
            patch(
                "jobs_common_extras.evaluation.services.inferencer.get_media_roi_numpy",
                return_value=image_numpy_data,
            ) as mock_get_media_roi_numpy,
        ):
            inferencer = DetectionInferencer(model=model)
            if enable_tiling:
                inferencer.tiler = dummy_tiler
            predicted_scene, _ = inferencer.predict(dataset_storage_id=fxt_dataset_storage.identifier, media=fxt_image)

        # Assert
        if enable_tiling:
            np.testing.assert_array_equal(dummy_tiler.call_args[0][0], image_numpy_data)
            assert inferencer.tiling_enabled
            if inferencer.is_legacy_otx_model:
                mock_det_config.assert_called_with(model=model)
                mock_get_tiler_configuration.assert_called_once_with(
                    tiling_parameters=model_config["tiling_parameters"]
                )
        else:
            mock_get_tiler_configuration.assert_not_called()

        mock_tiling_param.assert_called_once_with(model=model)
        mock_convert_to_annotations.assert_called_once()
        assert isinstance(predicted_scene, AnnotationScene)
        mock_get_media_roi_numpy.assert_called_once()

    @pytest.mark.parametrize(
        "enable_tiling, enable_tile_classifier, lazyfxt_model",
        (
            # tile classifier is only supported by legacy OTX model
            [True, False, "fxt_model_with_adapters"],
            [True, True, "fxt_legacy_model"],
            [False, False, "fxt_model_with_adapters"],
            [False, False, "fxt_legacy_model"],
        ),
    )
    def test_rotated_detection_inferencer(
        self,
        enable_tiling,
        enable_tile_classifier,
        lazyfxt_model,
        request,
        fxt_dataset_storage,
        fxt_model_with_tiling_adapters,
        fxt_image,
        fxt_model_api_image_model,
    ) -> None:
        # Arrange
        model_config = {
            "tiling_parameters": {
                "enable_tiling": enable_tiling,
                "enable_tile_classifier": enable_tile_classifier,
            }
        }
        image_numpy_data = np.zeros(shape=(100, 100, 3))
        dummy_tiler = MagicMock()
        model = request.getfixturevalue(lazyfxt_model)

        # Act
        with (
            patch.object(
                OpenvinoAdapter,
                "__init__",
                new=return_none,
            ),
            patch.object(
                ImageModel,
                "create_model",
                return_value=fxt_model_api_image_model,
            ),
            patch(
                "jobs_common_extras.evaluation.services.inferencer.get_legacy_detection_inferencer_configuration",
                return_value=model_config,
            ) as mock_det_config,
            patch(
                "jobs_common_extras.evaluation.services.inferencer.get_tiling_parameters",
                return_value=model_config["tiling_parameters"],
            ) as mock_tiling_param,
            patch.object(
                InstanceSegmentationToAnnotationConverter,
                "convert_to_annotations",
                return_value=[],
            ) as mock_convert_to_annotations,
            patch(
                "jobs_common_extras.evaluation.services.inferencer.get_tiler_configuration",
                return_value=model_config["tiling_parameters"],
            ) as mock_get_tiler_configuration,
            patch.object(
                InstanceSegmentationTiler,
                "__init__",
                new=return_none,
            ),
            patch.object(
                ImageModel,
                "__init__",
                new=return_none,
            ),
            patch(
                "jobs_common_extras.evaluation.services.inferencer.get_media_roi_numpy",
                return_value=image_numpy_data,
            ) as mock_get_media_roi_numpy,
        ):
            inferencer = InstanceSegmentationInferencer(model=fxt_model_with_tiling_adapters)
            if enable_tiling:
                inferencer.tiler = dummy_tiler
            predicted_scene, _ = inferencer.predict(dataset_storage_id=fxt_dataset_storage.identifier, media=fxt_image)

        # Assert
        if enable_tiling:
            np.testing.assert_array_equal(dummy_tiler.call_args[0][0], image_numpy_data)
            assert inferencer.tiling_enabled
            if inferencer.is_legacy_otx_model:
                mock_det_config.assert_called_with(model=model)
                mock_get_tiler_configuration.assert_called_once_with(
                    tiling_parameters=model_config["tiling_parameters"]
                )
        else:
            mock_get_tiler_configuration.assert_not_called()

        if enable_tile_classifier:
            assert inferencer.tiling_classifier_enabled
        mock_tiling_param.assert_called_once_with(model=model)
        mock_convert_to_annotations.assert_called_once()
        assert isinstance(predicted_scene, AnnotationScene)
        mock_get_media_roi_numpy.assert_called_once()

    @pytest.mark.parametrize(
        "enable_tiling, enable_tile_classifier, lazyfxt_model",
        (
            # tile classifier is only supported by legacy OTX model
            [True, False, "fxt_model_with_adapters"],
            [True, True, "fxt_legacy_model"],
            [False, False, "fxt_model_with_adapters"],
            [False, False, "fxt_legacy_model"],
        ),
    )
    def test_instance_segmentation_inferencer(
        self,
        enable_tiling,
        enable_tile_classifier,
        lazyfxt_model,
        request,
        fxt_dataset_storage,
        fxt_model_with_tiling_adapters,
        fxt_image,
        fxt_model_api_image_model,
    ) -> None:
        # Arrange
        model_config = {
            "tiling_parameters": {
                "enable_tiling": enable_tiling,
                "enable_tile_classifier": enable_tile_classifier,
            }
        }
        image_numpy_data = np.zeros(shape=(100, 100, 3))
        dummy_tiler = MagicMock()
        model = request.getfixturevalue(lazyfxt_model)

        # Act
        with (
            patch.object(
                OpenvinoAdapter,
                "__init__",
                new=return_none,
            ),
            patch.object(
                ImageModel,
                "create_model",
                return_value=fxt_model_api_image_model,
            ),
            patch(
                "jobs_common_extras.evaluation.services.inferencer.get_legacy_instance_segmentation_inferencer_configuration",
                return_value=model_config,
            ) as mock_seg_config,
            patch(
                "jobs_common_extras.evaluation.services.inferencer.get_tiling_parameters",
                return_value=model_config["tiling_parameters"],
            ) as mock_tiling_param,
            patch.object(
                RotatedRectToAnnotationConverter,
                "convert_to_annotations",
                return_value=[],
            ) as mock_convert_to_annotations,
            patch(
                "jobs_common_extras.evaluation.services.inferencer.get_tiler_configuration",
                return_value={},
            ) as mock_get_tiler_configuration,
            patch.object(
                InstanceSegmentationTiler,
                "__init__",
                new=return_none,
            ),
            patch.object(
                ImageModel,
                "__init__",
                new=return_none,
            ),
            patch(
                "jobs_common_extras.evaluation.services.inferencer.get_media_roi_numpy",
                return_value=image_numpy_data,
            ) as mock_get_media_roi_numpy,
        ):
            inferencer = RotatedDetectionInferencer(model=fxt_model_with_tiling_adapters)
            if enable_tiling:
                inferencer.tiler = dummy_tiler
            predicted_scene, _ = inferencer.predict(dataset_storage_id=fxt_dataset_storage.identifier, media=fxt_image)

        # Assert
        if enable_tiling:
            np.testing.assert_array_equal(dummy_tiler.call_args[0][0], image_numpy_data)
            assert inferencer.tiling_enabled
            if inferencer.is_legacy_otx_model:
                mock_seg_config.assert_called_with(model=model)
                mock_get_tiler_configuration.assert_called_once_with(
                    tiling_parameters=model_config["tiling_parameters"]
                )
        else:
            mock_get_tiler_configuration.assert_not_called()

        if enable_tile_classifier:
            assert inferencer.tiling_classifier_enabled
        mock_tiling_param.assert_called_once_with(model=model)
        mock_convert_to_annotations.assert_called_once()
        assert isinstance(predicted_scene, AnnotationScene)
        mock_get_media_roi_numpy.assert_called_once()

    def test_semantic_segmentation_inferencer(
        self, fxt_dataset_storage, fxt_model_with_adapters, fxt_image, fxt_model_api_image_model
    ) -> None:
        mock_result_image = MagicMock()
        mock_soft_prediction = np.zeros((5, 5, 2))
        mock_saliency_map = np.zeros((1, 2, 7, 7))
        mock_feature_vector = np.zeros((1, 10, 1, 1))
        fxt_model_api_image_model.postprocess.return_value = ImageResultWithSoftPrediction(
            resultImage=mock_result_image,
            soft_prediction=mock_soft_prediction,
            saliency_map=mock_saliency_map,
            feature_vector=mock_feature_vector,
        )
        image_numpy_data = np.zeros(shape=(100, 100, 3))
        with (
            patch.object(
                OpenvinoAdapter,
                "__init__",
                new=return_none,
            ),
            patch.object(
                ImageModel,
                "create_model",
                return_value=fxt_model_api_image_model,
            ),
            patch.object(
                SemanticSegmentationToAnnotationConverter,
                "convert_to_annotations",
                return_value=[],
            ) as mock_convert_to_annotations,
            patch.object(cv2, "applyColorMap"),
            patch.object(cv2, "cvtColor"),
            patch(
                "jobs_common_extras.evaluation.services.inferencer.get_media_roi_numpy",
                return_value=image_numpy_data,
            ) as mock_get_media_roi_numpy,
        ):
            inferencer = SemanticSegmentationInferencer(model=fxt_model_with_adapters)
            predicted_scene, metadata = inferencer.predict(
                dataset_storage_id=fxt_dataset_storage.identifier, media=fxt_image
            )

        assert inferencer.get_configuration() == {}
        mock_convert_to_annotations.assert_called_once()
        assert isinstance(predicted_scene, AnnotationScene)
        assert any(m for m in metadata if isinstance(m, Tensor) and m.name == Metadata.REPRESENTATION_VECTOR.value)
        mock_get_media_roi_numpy.assert_called_once()

    def test_anomaly_inferencer(
        self, fxt_dataset_storage, fxt_anomaly_model_with_adapters, fxt_image, fxt_model_api_image_model
    ) -> None:
        mock_anomaly_map = MagicMock()
        fxt_model_api_image_model.postprocess.return_value = AnomalyResult(anomaly_map=mock_anomaly_map)
        labels = fxt_anomaly_model_with_adapters.get_label_schema().get_labels(include_empty=False)
        image_numpy_data = np.zeros(shape=(100, 100, 3))

        with (
            patch.object(
                OpenvinoAdapter,
                "__init__",
                new=return_none,
            ),
            patch.object(
                ImageModel,
                "create_model",
                return_value=fxt_model_api_image_model,
            ),
            patch.object(
                AnomalyToAnnotationConverter,
                "__init__",
                new=return_none,
            ),
            patch.object(
                AnomalyToAnnotationConverter,
                "convert_to_annotations",
                return_value=[],
            ) as mock_convert_to_annotations,
            patch.object(AnnotationScene, "get_label_ids", return_value={label.id_ for label in labels}),
            patch(
                "jobs_common_extras.evaluation.services.inferencer.get_media_roi_numpy",
                return_value=image_numpy_data,
            ) as mock_get_media_roi_numpy,
        ):
            inferencer = AnomalyInferencer(model=fxt_anomaly_model_with_adapters)
            predicted_scene, metadata = inferencer.predict(
                dataset_storage_id=fxt_dataset_storage.identifier, media=fxt_image
            )

        assert inferencer.get_configuration() == {}
        mock_convert_to_annotations.assert_called_once()
        assert isinstance(predicted_scene, AnnotationScene)
        assert not metadata  # no metadata for anomaly
        mock_get_media_roi_numpy.assert_called_once()

    def test_keypoint_detection_inferencer(
        self, fxt_dataset_storage, fxt_keypoint_detection_model_with_adapters, fxt_image, fxt_model_api_image_model
    ) -> None:
        fxt_model_api_image_model.postprocess.return_value = DetectedKeypoints(
            keypoints=[[20, 30], [40, 50]],
            scores=[0.8, 0.9],
        )
        image_numpy_data = np.zeros(shape=(100, 100, 3))
        labels = fxt_keypoint_detection_model_with_adapters.get_label_schema().get_labels(include_empty=False)

        with (
            patch.object(
                OpenvinoAdapter,
                "__init__",
                new=return_none,
            ),
            patch.object(
                ImageModel,
                "create_model",
                return_value=fxt_model_api_image_model,
            ),
            patch.object(
                KeypointToAnnotationConverter,
                "__init__",
                new=return_none,
            ),
            patch.object(
                KeypointToAnnotationConverter,
                "convert_to_annotations",
                return_value=[],
            ) as mock_convert_to_annotations,
            patch.object(AnnotationScene, "get_label_ids", return_value={label.id_ for label in labels}),
            patch(
                "jobs_common_extras.evaluation.services.inferencer.get_media_roi_numpy",
                return_value=image_numpy_data,
            ) as mock_get_media_roi_numpy,
        ):
            inferencer = KeypointDetectionInferencer(model=fxt_keypoint_detection_model_with_adapters)
            predicted_scene, metadata = inferencer.predict(
                dataset_storage_id=fxt_dataset_storage.identifier, media=fxt_image
            )

        assert inferencer.get_configuration() == {}
        mock_convert_to_annotations.assert_called_once()
        assert isinstance(predicted_scene, AnnotationScene)
        assert not metadata  # no metadata for keypoint detection
        mock_get_media_roi_numpy.assert_called_once()

    def test_visual_prompting_inferencer(
        self, fxt_dataset_storage, fxt_model_with_sam_adapters, fxt_image, fxt_label
    ) -> None:
        mock_results = MagicMock()
        image_numpy_data = np.zeros(shape=(100, 100, 3))

        with (
            patch.object(OpenvinoAdapter, "__init__", new=return_none),
            patch.object(SAMImageEncoder, "__init__", new=return_none),
            patch.object(SAMDecoder, "__init__", new=return_none),
            patch.object(SAMLearnableVisualPrompter, "__init__", new=return_none),
            patch.object(SAMLearnableVisualPrompter, "infer", return_value=mock_results) as mock_sam_infer,
            patch.object(
                VisualPromptingToAnnotationConverter,
                "convert_to_annotations",
                return_value=[],
            ) as mock_convert_to_annotations,
            patch(
                "jobs_common_extras.evaluation.services.inferencer.get_media_roi_numpy",
                return_value=image_numpy_data,
            ) as mock_get_media_roi_numpy,
        ):
            inferencer = VisualPromptingInferencer(model=fxt_model_with_sam_adapters)
            predicted_scene, metadata = inferencer.predict(
                dataset_storage_id=fxt_dataset_storage.identifier, media=fxt_image
            )

        np.testing.assert_array_equal(mock_sam_infer.call_args[1]["image"], image_numpy_data)
        assert mock_sam_infer.call_args[1]["apply_masks_refinement"] is False
        mock_convert_to_annotations.assert_called_once_with(
            predictions=mock_results,
            metadata={"original_shape": image_numpy_data.shape},
        )
        assert not metadata
        mock_get_media_roi_numpy.assert_called_once()
