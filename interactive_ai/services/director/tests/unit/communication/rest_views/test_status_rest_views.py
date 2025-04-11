# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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

from communication.views.status_rest_views import StatusRestViews

from grpc_interfaces.job_submission.pb.job_service_pb2 import JobResponse


class TestStatusRESTViews:
    def test_project_status_to_rest_no_jobs(
        self,
        fxt_project,
        fxt_missing_annotations,
    ) -> None:
        task_node = fxt_project.get_trainable_task_nodes()[0]
        missing_annotations_per_task = {task_node.id_: fxt_missing_annotations}

        status_rest_view = StatusRestViews.project_status_to_rest(
            project=fxt_project,
            running_jobs=[],
            missing_annotations_per_task=missing_annotations_per_task,
            n_workspace_running_jobs=0,
        )

        assert status_rest_view["project_performance"] == {
            "score": None,
            "task_performances": [
                {
                    "task_id": str(task_node.id_),
                    "score": None,
                },
            ],
        }
        assert not status_rest_view["is_training"]
        assert status_rest_view["status"] == {
            "progress": -1,
        }
        assert (
            status_rest_view["n_required_annotations"]
            == fxt_missing_annotations.total_missing_annotations_auto_training
        )
        assert status_rest_view["n_new_annotations"] == fxt_missing_annotations.n_new_annotations
        assert status_rest_view["n_running_jobs"] == 0
        assert status_rest_view["n_running_jobs_project"] == 0
        task_status_rest = status_rest_view["tasks"][0]
        assert task_status_rest["id"] == task_node.id_
        assert not task_status_rest["is_training"]
        assert task_status_rest["status"] == {
            "progress": -1,
        }
        assert task_status_rest["title"] == task_node.title
        assert task_status_rest["ready_to_train"] == (
            fxt_missing_annotations.total_missing_annotations_manual_training == 0
        )
        assert task_status_rest["n_new_annotations"] == fxt_missing_annotations.n_new_annotations
        assert task_status_rest["required_annotations"] == StatusRestViews.missing_annotations_to_rest(
            missing_annotations=fxt_missing_annotations
        )

    def test_project_status_to_rest(
        self,
        fxt_project,
        fxt_missing_annotations,
    ) -> None:
        task_node = fxt_project.get_trainable_task_nodes()[0]
        missing_annotations_per_task = {task_node.id_: fxt_missing_annotations}
        running_job_response = JobResponse(
            type="train",
            step_details=[
                JobResponse.StepDetails(
                    state="running",
                    progress=0.5,
                )
            ],
            metadata=json.dumps(
                {
                    "project": {
                        "id": fxt_project.id_,
                        "name": fxt_project.name,
                    },
                    "task": {
                        "task_id": task_node.id_,
                        "name": task_node.title,
                    },
                }
            ),
        )
        status_rest_view = StatusRestViews.project_status_to_rest(
            project=fxt_project,
            running_jobs=[running_job_response],
            missing_annotations_per_task=missing_annotations_per_task,
            n_workspace_running_jobs=1,
        )
        assert status_rest_view["project_performance"] == {
            "score": None,
            "task_performances": [
                {
                    "task_id": str(task_node.id_),
                    "score": None,
                },
            ],
        }
        assert status_rest_view["is_training"]
        assert status_rest_view["status"] == {
            "progress": running_job_response.step_details[0].progress,
        }
        assert (
            status_rest_view["n_required_annotations"]
            == fxt_missing_annotations.total_missing_annotations_auto_training
        )
        assert status_rest_view["n_new_annotations"] == fxt_missing_annotations.n_new_annotations
        assert status_rest_view["n_running_jobs"] == 1
        assert status_rest_view["n_running_jobs_project"] == 1
        task_status_rest = status_rest_view["tasks"][0]
        assert task_status_rest["id"] == task_node.id_
        assert task_status_rest["is_training"]
        assert task_status_rest["ready_to_train"] == (
            fxt_missing_annotations.total_missing_annotations_manual_training == 0
        )
        assert task_status_rest["status"] == {
            "progress": running_job_response.step_details[0].progress,
        }
        assert task_status_rest["title"] == task_node.title
        assert task_status_rest["n_new_annotations"] == fxt_missing_annotations.n_new_annotations
        assert task_status_rest["required_annotations"] == StatusRestViews.missing_annotations_to_rest(
            missing_annotations=fxt_missing_annotations
        )

    def test_missing_annotations_to_rest(self, fxt_label, fxt_missing_annotations) -> None:
        missing_annotations_rest = StatusRestViews.missing_annotations_to_rest(
            missing_annotations=fxt_missing_annotations
        )

        assert missing_annotations_rest["value"] == fxt_missing_annotations.total_missing_annotations_auto_training
        missing_annotations_details_rest = missing_annotations_rest["details"][0]
        assert missing_annotations_details_rest["id"] == fxt_label.id_
        assert missing_annotations_details_rest["label_name"] == fxt_label.name
        assert missing_annotations_details_rest["label_color"] == fxt_label.color.hex_str
        assert (
            missing_annotations_details_rest["value"]
            == fxt_missing_annotations.missing_annotations_per_label[fxt_label.id_]
        )

    def test_incremental_learning_status_to_rest(self, fxt_mongo_id, fxt_missing_annotations):
        result = StatusRestViews.incremental_learning_status_to_rest(
            incremental_learning_status={fxt_mongo_id(0): fxt_missing_annotations}
        )

        assert result["n_required_annotations"] == fxt_missing_annotations.total_missing_annotations_auto_training
        assert result["n_new_annotations"] == fxt_missing_annotations.n_new_annotations
        per_task_result = result["status_per_task"][0]
        assert per_task_result["ready_to_train"] == (
            fxt_missing_annotations.total_missing_annotations_manual_training == 0
        )

        assert per_task_result["task_id"] == str(fxt_mongo_id(0))
        assert per_task_result["required_total"] == fxt_missing_annotations.total_missing_annotations_auto_training
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
