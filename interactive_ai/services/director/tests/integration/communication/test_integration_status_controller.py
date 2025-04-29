# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import time
from unittest.mock import patch

from communication.controllers.status_controller import StatusController
from coordination.dataset_manager.missing_annotations_helper import MissingAnnotationsHelper


class TestStatusController:
    def test_get_incremental_learning_status(
        self,
        fxt_db_project_service,
        fxt_missing_annotations,
    ) -> None:
        """
        <b>Description:</b>
        To check the functionality of the DirectorRest.get_incremental_learning_status function.

        <b>Input data:</b>
        An instance of the StatusController class.

        <b>Expected results:</b>
        Test passes if the incremental learning response is as expected

        <b>Steps</b>
        1. Create an instance of the DirectorRest class and create a mock project and workspace
        2. Mock the MissingAnnotationsHelper.get_missing_annotations_for_task method
        3. Request the incremental learning status and assert that we receive the correct value
        """
        time.sleep(1)

        project = fxt_db_project_service.create_empty_project()

        with patch.object(
            MissingAnnotationsHelper,
            "get_missing_annotations_for_task",
            return_value=fxt_missing_annotations,
        ):
            result = StatusController().get_incremental_learning_status(
                project_id=project.id_, workspace_id=project.workspace_id
            )

            assert result["n_required_annotations"] == fxt_missing_annotations.total_missing_annotations_auto_training
            assert result["n_new_annotations"] == fxt_missing_annotations.n_new_annotations
            per_task_result = result["status_per_task"][0]
            assert per_task_result["task_id"] == str(fxt_db_project_service.task_node_1.id_)
            assert per_task_result["required_total"] == fxt_missing_annotations.total_missing_annotations_auto_training
            assert not per_task_result["ready_to_train"]
            assert per_task_result["n_new_annotations"] == fxt_missing_annotations.n_new_annotations
            assert per_task_result["required_per_label"] == [
                {
                    "id": label_id,
                    "value": missing_for_label,
                    "label_name": fxt_missing_annotations.task_label_data[0].name,
                    "label_color": fxt_missing_annotations.task_label_data[0].color_hex_str,
                }
                for label_id, missing_for_label in fxt_missing_annotations.missing_annotations_per_label.items()
            ]
