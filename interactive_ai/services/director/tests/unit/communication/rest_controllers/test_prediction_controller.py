# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch

import pytest

from communication.controllers.prediction_controller import PredictionController
from communication.exceptions import NoModelTrainedException
from communication.views.prediction_rest_views import PredictionRESTViews
from entities import PredictionType
from service.label_schema_service import LabelSchemaService
from service.prediction_service import PredictionService
from service.project_service import ProjectService

from iai_core.entities.model import NullModel
from iai_core.services import ModelService


class TestPredictionController:
    def test_get_predictions_by_id(
        self,
        fxt_mongo_id,
        fxt_project,
        fxt_dataset_storage,
        fxt_media_identifier,
        fxt_annotation_scene,
        fxt_model,
        fxt_label_schema,
    ) -> None:
        project_id = fxt_project.id_
        dataset_storage_id = fxt_dataset_storage.id_
        prediction_id = fxt_mongo_id(1)
        rest_response = {"test_key": "test_value"}
        expected_result = {"test_key": "test_value", "maps": []}

        with (
            patch.object(ProjectService, "get_by_id", return_value=fxt_project) as patched_get_project,
            patch.object(
                ProjectService,
                "get_dataset_storage_by_id",
                return_value=fxt_dataset_storage,
            ) as patched_get_dataset_storage,
            patch.object(
                PredictionService,
                "get_prediction_by_id",
                return_value=fxt_annotation_scene,
            ) as patched_get_prediction_by_id,
            patch.object(PredictionService, "get_prediction_by_type") as patched_get_prediction_by_type,
            patch.object(
                LabelSchemaService,
                "get_latest_label_schema_for_project",
                return_value=fxt_label_schema,
            ) as patched_get_latest_label_schema,
            patch.object(
                PredictionRESTViews,
                "media_2d_prediction_to_rest",
                return_value=rest_response,
            ) as patched_to_rest,
            patch.object(ModelService, "get_inference_active_model", return_value=fxt_model),
        ):
            result = PredictionController.get_prediction(
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
                media_identifier=fxt_media_identifier,
                prediction_id=prediction_id,
            )

        patched_get_project.assert_called_once_with(project_id=project_id)
        patched_get_dataset_storage.assert_called_once_with(fxt_project, dataset_storage_id)
        patched_get_prediction_by_id.assert_called_once_with(
            dataset_storage_identifier=fxt_dataset_storage.identifier,
            prediction_id=prediction_id,
            media_identifier=fxt_media_identifier,
        )
        patched_get_prediction_by_type.assert_not_called()
        patched_get_latest_label_schema.assert_called_once_with(
            fxt_project.identifier,
        )
        patched_to_rest.assert_called_once_with(
            prediction=fxt_annotation_scene,
            project=fxt_project,
            label_schema=fxt_label_schema,
            label_only=False,
            update_response_for_inference_gateway=False,
        )
        assert result == expected_result

    def test_get_predictions_by_type(
        self,
        fxt_project,
        fxt_dataset_storage,
        fxt_media_identifier,
        fxt_annotation_scene,
        fxt_model,
        fxt_label_schema,
    ) -> None:
        project_id = fxt_project.id_
        dataset_storage_id = fxt_dataset_storage.id_
        prediction_type = PredictionType.LATEST
        rest_response = {"test_key": "test_value"}
        expected_result = {"test_key": "test_value", "maps": []}

        with (
            patch.object(ProjectService, "get_by_id", return_value=fxt_project) as patched_get_project,
            patch.object(
                ProjectService,
                "get_dataset_storage_by_id",
                return_value=fxt_dataset_storage,
            ) as patched_get_dataset_storage,
            patch.object(PredictionService, "get_prediction_by_id") as patched_get_prediction_by_id,
            patch.object(
                PredictionService,
                "get_prediction_by_type",
                return_value=fxt_annotation_scene,
            ) as patched_get_prediction_by_type,
            patch.object(
                LabelSchemaService,
                "get_latest_label_schema_for_project",
                return_value=fxt_label_schema,
            ) as patched_get_latest_label_schema,
            patch.object(
                PredictionRESTViews,
                "media_2d_prediction_to_rest",
                return_value=rest_response,
            ) as patched_to_rest,
            patch.object(ModelService, "get_inference_active_model", return_value=fxt_model),
        ):
            result = PredictionController.get_prediction(
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
                media_identifier=fxt_media_identifier,
                prediction_type=prediction_type,
            )

        patched_get_project.assert_called_once_with(project_id=project_id)
        patched_get_dataset_storage.assert_called_once_with(fxt_project, dataset_storage_id)
        patched_get_prediction_by_id.assert_not_called()
        patched_get_prediction_by_type.assert_called_once_with(
            project=fxt_project,
            dataset_storage=fxt_dataset_storage,
            media_identifier=fxt_media_identifier,
            prediction_type=prediction_type,
            task_id=None,
            model_ids={fxt_model.id_},
        )
        patched_get_latest_label_schema.assert_called_once_with(
            fxt_project.identifier,
        )
        patched_to_rest.assert_called_once_with(
            prediction=fxt_annotation_scene,
            project=fxt_project,
            label_schema=fxt_label_schema,
            label_only=False,
            update_response_for_inference_gateway=False,
        )
        assert result == expected_result

    def test_get_predictions_by_type_and_model_id(
        self,
        fxt_project,
        fxt_dataset_storage,
        fxt_media_identifier,
        fxt_annotation_scene,
        fxt_ote_id,
        fxt_label_schema,
    ) -> None:
        project_id = fxt_project.id_
        dataset_storage_id = fxt_dataset_storage.id_
        prediction_type = PredictionType.LATEST
        model_id = fxt_ote_id(13)
        rest_response = {"test_key": "test_value"}
        expected_result = {"test_key": "test_value"}

        with (
            patch.object(ProjectService, "get_by_id", return_value=fxt_project) as patched_get_project,
            patch.object(
                ProjectService,
                "get_dataset_storage_by_id",
                return_value=fxt_dataset_storage,
            ) as patched_get_dataset_storage,
            patch.object(PredictionService, "get_prediction_by_id") as patched_get_prediction_by_id,
            patch.object(
                PredictionService,
                "get_prediction_by_type",
                return_value=fxt_annotation_scene,
            ) as patched_get_prediction_by_type,
            patch.object(
                LabelSchemaService,
                "get_latest_label_schema_for_project",
                return_value=fxt_label_schema,
            ) as patched_get_latest_label_schema,
            patch.object(
                PredictionRESTViews,
                "media_2d_prediction_to_rest",
                return_value=rest_response,
            ) as patched_to_rest,
        ):
            result = PredictionController.get_prediction(
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
                media_identifier=fxt_media_identifier,
                prediction_type=prediction_type,
                model_id=model_id,
                for_inf_gateway=True,
            )

        patched_get_project.assert_called_once_with(project_id=project_id)
        patched_get_dataset_storage.assert_called_once_with(fxt_project, dataset_storage_id)
        patched_get_prediction_by_id.assert_not_called()
        patched_get_prediction_by_type.assert_called_once_with(
            project=fxt_project,
            dataset_storage=fxt_dataset_storage,
            media_identifier=fxt_media_identifier,
            prediction_type=prediction_type,
            task_id=None,
            model_ids={model_id},
        )
        patched_get_latest_label_schema.assert_called_once_with(
            fxt_project.identifier,
        )
        patched_to_rest.assert_called_once_with(
            prediction=fxt_annotation_scene,
            project=fxt_project,
            label_schema=fxt_label_schema,
            label_only=False,
            update_response_for_inference_gateway=True,
        )

        assert result == expected_result

    def test_get_predictions_error(
        self,
        fxt_project,
        fxt_dataset_storage,
        fxt_media_identifier,
        fxt_model,
    ) -> None:
        project_id = fxt_project.id_
        dataset_storage_id = fxt_dataset_storage.id_

        with (
            patch.object(ProjectService, "get_by_id", return_value=fxt_project) as patched_get_project,
            patch.object(
                ProjectService,
                "get_dataset_storage_by_id",
                return_value=fxt_dataset_storage,
            ) as patched_get_dataset_storage,
            pytest.raises(ValueError) as error,
            patch.object(ModelService, "get_inference_active_model", return_value=fxt_model),
        ):
            PredictionController.get_prediction(
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
                media_identifier=fxt_media_identifier,
            )

        patched_get_project.assert_called_once_with(project_id=project_id)
        patched_get_dataset_storage.assert_called_once_with(fxt_project, dataset_storage_id)
        assert str(error.value) == "Either prediction_id or prediction_type should be not None."

    def test_get_predictions_no_model_trained_error(
        self,
        fxt_project,
        fxt_dataset_storage,
        fxt_media_identifier,
    ) -> None:
        project_id = fxt_project.id_
        dataset_storage_id = fxt_dataset_storage.id_
        with (
            patch.object(ProjectService, "get_by_id", return_value=fxt_project) as patched_get_project,
            patch.object(
                ProjectService,
                "get_dataset_storage_by_id",
                return_value=fxt_dataset_storage,
            ) as patched_get_dataset_storage,
            patch.object(ModelService, "get_inference_active_model", return_value=NullModel()),
            pytest.raises(NoModelTrainedException),
        ):
            PredictionController.get_prediction(
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
                media_identifier=fxt_media_identifier,
            )

        patched_get_project.assert_called_once_with(project_id=project_id)
        patched_get_dataset_storage.assert_called_once_with(fxt_project, dataset_storage_id)

    def test_get_predictions_model_id_online_error(
        self,
        fxt_project,
        fxt_dataset_storage,
        fxt_media_identifier,
        fxt_ote_id,
    ) -> None:
        project_id = fxt_project.id_
        dataset_storage_id = fxt_dataset_storage.id_
        fxt_project.get_trainable_task_nodes()[0].id_
        expected_error_msg = "A model_id can only be specified for prediction type latest."

        with (
            patch.object(ProjectService, "get_by_id", return_value=fxt_project) as patched_get_project,
            patch.object(
                ProjectService,
                "get_dataset_storage_by_id",
                return_value=fxt_dataset_storage,
            ) as patched_get_dataset_storage,
            pytest.raises(ValueError) as error,
        ):
            PredictionController.get_prediction(
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
                media_identifier=fxt_media_identifier,
                prediction_type=PredictionType.ONLINE,
                model_id=fxt_ote_id(12),
            )

        patched_get_project.assert_called_once_with(project_id=project_id)
        patched_get_dataset_storage.assert_called_once_with(fxt_project, dataset_storage_id)
        assert str(error.value) == expected_error_msg
