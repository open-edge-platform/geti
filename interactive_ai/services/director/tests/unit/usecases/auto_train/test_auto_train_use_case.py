# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os
import time
from unittest.mock import call, patch

import pytest

from coordination.dataset_manager.missing_annotations_helper import MissingAnnotationsHelper
from entities.auto_train_activation import AutoTrainActivation
from storage.repos.auto_train_activation_repo import ProjectBasedAutoTrainActivationRepo
from usecases.auto_train import AutoTrainUseCase

from geti_types import CTX_SESSION_VAR, ID, RequestSource, make_session, session_context
from sc_sdk.repos import ProjectRepo, TaskNodeRepo

WORKSPACE_ID = ID("workspace_id")


class TestAutoTrainUseCase:
    def test_check_conditions_and_set_auto_train_readiness_debounce(self, fxt_project_identifier) -> None:
        """
        Checks that when "_check_conditions_and_set_auto_train_readiness_debounce" is called, the
        "_check_conditions_and_set_auto_train_readiness_debounce" method starts after the debounce time.
        """
        CTX_SESSION_VAR.set(make_session())
        with (
            patch.object(
                AutoTrainUseCase, "_check_conditions_and_set_auto_train_readiness", return_value=None
            ) as mock_check_conditions_and_set_auto_train_readiness,
            patch.dict(os.environ, {"AUTO_TRAIN_DEBOUNCE_TIME": "0.1"}),
        ):
            AutoTrainUseCase()._check_conditions_and_set_auto_train_readiness_debounce(
                project_identifier=fxt_project_identifier
            )

            mock_check_conditions_and_set_auto_train_readiness.assert_not_called()
            time.sleep(0.2)
            mock_check_conditions_and_set_auto_train_readiness.assert_called_once_with(
                session=CTX_SESSION_VAR.get(),
                project_identifier=fxt_project_identifier,
                bypass_debouncer=False,
            )

    @pytest.mark.parametrize("enough_annotations", [True, False], ids=["enough annotations", "not enough annotations"])
    def test_check_conditions_and_set_auto_train_readiness(
        self,
        enough_annotations,
        fxt_project,
        fxt_missing_annotations,
        fxt_missing_annotations_zero_missing,
    ) -> None:
        """Checks that an auto-training request is submitted if and only if the conditions are met"""
        dataset_storage = fxt_project.get_training_dataset_storage()
        task_node = fxt_project.get_trainable_task_nodes()[0]
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project) as mock_get_project,
            patch.object(
                ProjectBasedAutoTrainActivationRepo, "set_auto_train_readiness_by_task_id", return_value=None
            ) as mock_set_readiness,
            patch.object(
                MissingAnnotationsHelper,
                "get_missing_annotations_for_task",
                return_value=(fxt_missing_annotations_zero_missing if enough_annotations else fxt_missing_annotations),
            ) as mock_get_missing_annotations,
        ):
            AutoTrainUseCase._check_conditions_and_set_auto_train_readiness(
                session=make_session(), project_identifier=fxt_project.identifier
            )

            mock_get_project.assert_called_once_with(fxt_project.id_)
            mock_get_missing_annotations.assert_called_once_with(
                dataset_storage_identifier=dataset_storage.identifier,
                task_node=task_node,
            )
            if enough_annotations:
                mock_set_readiness.assert_called_once_with(
                    task_node_id=task_node.id_,
                    readiness=True,
                    bypass_debouncer=True,
                    raise_exc_on_missing=False,
                )
            else:
                mock_set_readiness.assert_called_once_with(
                    task_node_id=task_node.id_,
                    readiness=False,
                    bypass_debouncer=True,
                    raise_exc_on_missing=False,
                )

    def test_upsert_auto_train_request_timestamps_for_tasks(
        self, fxt_project_identifier, fxt_session_ctx, fxt_ote_id
    ) -> None:
        task_id_1, task_id_2 = fxt_ote_id(201), fxt_ote_id(202)
        with (
            patch.object(TaskNodeRepo, "get_trainable_task_ids", return_value=[task_id_1, task_id_2]),
            patch.object(ProjectBasedAutoTrainActivationRepo, "upsert_timestamp_for_task") as mock_upsert_timestamp,
        ):
            AutoTrainUseCase.upsert_auto_train_request_timestamps_for_tasks(fxt_project_identifier)

        mock_upsert_timestamp.assert_has_calls(
            [
                call(instance=AutoTrainActivation(task_node_id=task_id_1, session=fxt_session_ctx)),
                call(instance=AutoTrainActivation(task_node_id=task_id_2, session=fxt_session_ctx)),
            ]
        )

    def test_on_configuration_changed(self, fxt_project_identifier) -> None:
        with patch.object(AutoTrainUseCase, "_check_conditions_and_set_auto_train_readiness") as mock_check_conditions:
            AutoTrainUseCase.on_configuration_changed(fxt_project_identifier)

        mock_check_conditions.assert_called_once_with(project_identifier=fxt_project_identifier)

    @pytest.mark.parametrize(
        "session_request_source,session_extra",
        [
            pytest.param(RequestSource.INTERNAL, {}, id="internal request (job)"),
            pytest.param(RequestSource.BROWSER, {}, id="browser request - media labeled manually)"),
            pytest.param(
                RequestSource.BROWSER, {"labeled_media_upload": "True"}, id="browser request - media labeled on upload"
            ),
            pytest.param(RequestSource.API_KEY, {}, id="API request - Geti SDK"),
            pytest.param(RequestSource.INTERNAL, {}, id="internal request - job"),
            pytest.param(RequestSource.UNKNOWN, {}, id="unknown origin request"),
        ],
    )
    def test_on_dataset_counters_updated(
        self, fxt_organization_id, fxt_project_identifier, session_request_source, session_extra
    ) -> None:
        auto_train_use_case = AutoTrainUseCase()
        session = make_session(
            organization_id=fxt_organization_id,
            workspace_id=fxt_project_identifier.workspace_id,
            source=session_request_source,
            extra=session_extra,
        )
        with (
            session_context(session),
            patch.object(AutoTrainUseCase, "upsert_auto_train_request_timestamps_for_tasks") as mock_upsert_timestamp,
            patch.object(
                auto_train_use_case, "_check_conditions_and_set_auto_train_readiness"
            ) as mock_check_conditions_immediate,
            patch.object(
                auto_train_use_case, "_check_conditions_and_set_auto_train_readiness_debounce"
            ) as mock_check_conditions_debounced,
        ):
            auto_train_use_case.on_dataset_counters_updated(fxt_project_identifier)

        mock_upsert_timestamp.assert_called_once_with(project_identifier=fxt_project_identifier)
        if session_request_source == RequestSource.INTERNAL:
            mock_check_conditions_immediate.assert_not_called()
            mock_check_conditions_debounced.assert_not_called()
        elif session_request_source == RequestSource.UNKNOWN or (
            session_request_source == RequestSource.BROWSER and not session_extra
        ):
            mock_check_conditions_immediate.assert_called_once_with(project_identifier=fxt_project_identifier)
            mock_check_conditions_debounced.assert_not_called()
        else:
            mock_check_conditions_immediate.assert_not_called()
            mock_check_conditions_debounced.assert_called_once_with(project_identifier=fxt_project_identifier)

    def test_on_training_successful(self, fxt_project_identifier) -> None:
        with patch.object(AutoTrainUseCase, "_check_conditions_and_set_auto_train_readiness") as mock_check_conditions:
            AutoTrainUseCase.on_training_successful(fxt_project_identifier)

        mock_check_conditions.assert_called_once_with(project_identifier=fxt_project_identifier)
