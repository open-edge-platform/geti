# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Converters between objects and their corresponding REST views
"""

import json
import logging
from typing import Any

from communication.views.performance_rest_views import PerformanceRESTViews
from coordination.dataset_manager.missing_annotations_helper import MissingAnnotations

from geti_types import ID
from grpc_interfaces.job_submission.pb.job_service_pb2 import JobResponse
from iai_core_py.entities.project import Project
from iai_core_py.entities.task_node import TaskNode

logger = logging.getLogger(__name__)


class StatusRestViews:
    @staticmethod
    def incremental_learning_status_to_rest(incremental_learning_status: dict[ID, MissingAnnotations]) -> dict:
        """
        Returns REST view of a dictionary containing the MissingAnnotations for every task

        :param incremental_learning_status: Dictionary mapping every task ID to a MissingAnnotations object describing
        the annotations required before training can be started
        :return: REST view of the missing annotations per task
        """
        total_required_annotations = sum(
            missing_annotations.total_missing_annotations_auto_training
            for missing_annotations in incremental_learning_status.values()
        )
        total_n_new_annotations = sum(
            missing_annotations.n_new_annotations for missing_annotations in incremental_learning_status.values()
        )
        return {
            "n_required_annotations": total_required_annotations,
            "n_new_annotations": total_n_new_annotations,
            "status_per_task": [
                StatusRestViews.missing_annotations_for_task_to_rest(
                    task_id=task_id, missing_annotations=missing_annotations
                )
                for task_id, missing_annotations in incremental_learning_status.items()
            ],
        }

    @staticmethod
    def missing_annotations_for_task_to_rest(task_id: ID, missing_annotations: MissingAnnotations) -> dict:
        """
        Returns REST view of a per-task MissingAnnotations object

        :param task_id: ID of the task the missing annotations are returned for
        :param missing_annotations: MissingAnnotations object describing the number of required annotations before the
        training will start
        :return: REST view of the missing annotations.
        """
        task_ready_for_manual_training = missing_annotations.total_missing_annotations_manual_training == 0
        required_per_label = []
        for (
            label_id,
            label_value,
        ) in missing_annotations.missing_annotations_per_label.items():
            matched_labels = list(filter(lambda x: x.id_ == label_id, missing_annotations.task_label_data))
            label = matched_labels[0]

            if label_value > 0:
                required_per_label.append(
                    {
                        "id": str(label.id_),
                        "label_name": label.name,
                        "label_color": label.color_hex_str,
                        "value": label_value,
                    }
                )
        return {
            "task_id": str(task_id),
            "required_total": missing_annotations.total_missing_annotations_auto_training,
            "n_new_annotations": missing_annotations.n_new_annotations,
            "required_per_label": required_per_label,
            "ready_to_train": task_ready_for_manual_training,
        }

    @staticmethod
    def missing_annotations_to_rest(
        missing_annotations: MissingAnnotations,
    ) -> dict:
        """
        Returns REST view of MissingAnnotations

        :param missing_annotations: a MissingAnnotations object to be converted to RESTView
        :return: REST view of MissingAnnotations.
            Structure:
            {
                "details": [
                    {
                        "id": label id
                        "label_name": label name,
                        "label_color": label color,
                        "value": number of annotations required for this label
                    },
                    {...}
                ]
                "value": total required annotations over all labels

            }
        """
        value = missing_annotations.total_missing_annotations_auto_training
        details = []
        for (
            label_id,
            label_value,
        ) in missing_annotations.missing_annotations_per_label.items():
            matched_labels = list(filter(lambda x: x.id_ == label_id, missing_annotations.task_label_data))
            label = matched_labels[0]

            if label_value > 0:
                details.append(
                    {
                        "id": label.id_,
                        "label_name": label.name,
                        "label_color": label.color_hex_str,
                        "value": label_value,
                    }
                )
        return {"value": value, "details": details}

    @staticmethod
    def project_status_to_rest(
        project: Project,
        running_jobs: list[JobResponse],
        missing_annotations_per_task: dict[ID, MissingAnnotations],
        n_workspace_running_jobs: int,
    ) -> dict:
        """
        Convert the status of the project to a REST view, which contains information on the running jobs, required
        annotations and the performance of the project.

        :param project: Project to get convert the status to REST view for
        :param running_jobs: List of jobs that are currently running for the project
        :param missing_annotations_per_task: For each task, a MissingAnnotations object containing information on how
        many annotations are required to start training.
        :param performance: Performance object describing the performance of the latest active model
        :param n_workspace_running_jobs: number of running jobs for the whole workspace
        :return: REST view of the project status
        """
        n_missing_annotations_per_task = {
            task_id: missing_annotations.total_missing_annotations_auto_training
            for task_id, missing_annotations in missing_annotations_per_task.items()
        }
        n_new_annotations_per_task = {
            task_id: missing_annotations.n_new_annotations
            for task_id, missing_annotations in missing_annotations_per_task.items()
        }

        highest_prio_running_job = running_jobs[-1] if running_jobs else None
        job_progress: float | None = None
        if highest_prio_running_job:
            for job_step_details in highest_prio_running_job.step_details:
                if job_step_details.state == "running":
                    job_progress = job_step_details.progress
                    break

        is_training = any("train" in job.type for job in running_jobs)

        result = {
            "project_performance": PerformanceRESTViews.project_performance_to_rest(project.performance),
            "is_training": is_training,
            "status": {
                "progress": job_progress if job_progress is not None else -1,
            },
            "n_required_annotations": sum(n_missing_annotations_per_task.values()),
            "n_new_annotations": sum(n_new_annotations_per_task.values()),
            "n_running_jobs": n_workspace_running_jobs,
            "n_running_jobs_project": len(running_jobs),
        }

        last_running_job_per_task = {}
        for job in running_jobs:
            if not job.metadata:
                continue
            metadata = json.loads(job.metadata)
            if "task" in metadata:
                task_id = ID(metadata["task"]["task_id"])
                last_running_job_per_task[task_id] = job

        result["tasks"] = [
            StatusRestViews._get_rest_task_status(
                last_running_job_per_task,
                missing_annotations_per_task,
                n_new_annotations_per_task,
                task_node,
            )
            for task_node in project.get_trainable_task_nodes()
        ]
        return result

    @staticmethod
    def _get_rest_task_status(
        last_running_job_per_task: dict[ID, JobResponse],
        missing_annotations_per_task: dict[ID, MissingAnnotations],
        n_new_annotations_per_task: dict[ID, int],
        task_node: TaskNode,
    ) -> dict[str, Any]:
        task_ready_for_manual_training = (
            missing_annotations_per_task[task_node.id_].total_missing_annotations_manual_training == 0
        )
        # TODO: job status to be removed after CVS-107662
        task_job = last_running_job_per_task.get(task_node.id_)
        progress: float = -1.0
        if task_job:
            for job_step_details in task_job.step_details:
                if job_step_details.state == "running":
                    progress = job_step_details.progress
                    break
        rest_task_status = {
            "id": str(task_node.id_),
            "is_training": bool(task_job),
            "status": {
                "progress": progress,
            },
            "title": task_node.title,
            "n_new_annotations": n_new_annotations_per_task[task_node.id_],
            "ready_to_train": task_ready_for_manual_training,
        }
        if task_node.id_ in missing_annotations_per_task:
            missing_annotations_task = missing_annotations_per_task[task_node.id_]
            required_annotations_rest = StatusRestViews.missing_annotations_to_rest(
                missing_annotations=missing_annotations_task
            )
        else:
            required_annotations_rest = {"details": [], "value": 0}
        rest_task_status["required_annotations"] = required_annotations_rest
        return rest_task_status
