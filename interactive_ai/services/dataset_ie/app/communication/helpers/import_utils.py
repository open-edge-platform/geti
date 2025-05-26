# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements import utilities
"""

import logging

from domain.entities.geti_project_type import GetiProjectType

from iai_core.entities.label import Domain
from iai_core.entities.model_template import TaskType, task_type_to_label_domain
from iai_core.entities.project import Project

logger = logging.getLogger(__name__)

STR_DETECTION_ORIENTED: str = "detection_oriented"

SUPPORTED_DOMAINS = [
    Domain.CLASSIFICATION,
    Domain.DETECTION,
    Domain.SEGMENTATION,
    Domain.INSTANCE_SEGMENTATION,
    Domain.ANOMALY_CLASSIFICATION,
    Domain.ANOMALY_DETECTION,
    Domain.ANOMALY_SEGMENTATION,
    Domain.ANOMALY,
    Domain.ROTATED_DETECTION,
]


class ImportUtils:
    @staticmethod
    def task_type_to_rest_api_string(task_type: TaskType) -> str:
        """
        Convert TaskType to task_type string for REST API

        :param task_type: OTX task type identifier
        :return: task name for REST API
        """
        return task_type.name.lower() if task_type != TaskType.ROTATED_DETECTION else STR_DETECTION_ORIENTED

    @staticmethod
    def project_type_to_rest_api_string(geti_project_type: GetiProjectType) -> str:
        """
        Convert GetiProjectType to task_type string for REST API

        :param geti_project_type: Geti project type identifier
        :return: task_type string for REST API
        """
        exceptions = {
            GetiProjectType.HIERARCHICAL_CLASSIFICATION: "classification_hierarchical",
            GetiProjectType.CHAINED_DETECTION_CLASSIFICATION: "detection_classification",
            GetiProjectType.CHAINED_DETECTION_SEGMENTATION: "detection_segmentation",
            GetiProjectType.ROTATED_DETECTION: STR_DETECTION_ORIENTED,
        }
        return exceptions.get(geti_project_type, geti_project_type.name.lower())

    @staticmethod
    def rest_task_type_to_project_type(rest_task_type: str) -> GetiProjectType:
        """
        Get GetiProjectType from the task_type field in a REST API response

        :param rest_task_type: task_type value in the REST API response
        :return: project_type
        """
        rest_task_name = rest_task_type.lower()

        project_type = GetiProjectType.UNKNOWN
        for project_type_iter in GetiProjectType:
            if (
                rest_task_name == ImportUtils.project_type_to_rest_api_string(geti_project_type=project_type_iter)
                or rest_task_name == project_type_iter.name.lower()
            ):  # backward compatibility
                project_type = project_type_iter
                break
        return project_type

    @staticmethod
    def task_types_to_project_type(task_types: list[TaskType]) -> GetiProjectType:
        """
        Figure out the project_type from a list of trainable task_types

        :param task_types: a list of trainable task_types for a project
        :return: project_type
        """
        if len(task_types) == 0:
            return GetiProjectType.UNKNOWN

        project_type = GetiProjectType.UNKNOWN

        if len(task_types) == 1:
            try:
                project_type = GetiProjectType[task_types[0].name]
            except KeyError:
                if task_types[0].name == "ANOMALY":
                    project_type = GetiProjectType.ANOMALY_CLASSIFICATION
        elif len(task_types) == 2:
            if task_types == [TaskType.DETECTION, TaskType.CLASSIFICATION]:
                project_type = GetiProjectType.CHAINED_DETECTION_CLASSIFICATION
            elif task_types == [TaskType.DETECTION, TaskType.SEGMENTATION]:
                project_type = GetiProjectType.CHAINED_DETECTION_SEGMENTATION

        return project_type

    @staticmethod
    def get_project_type(project: Project) -> GetiProjectType:
        """
        Get project type
        We figure out the project_type from the project's trainable task nodes,
        then return the string representation of project_type

        :param project: Geti project object
        :return: geti project type
        """
        task_types = [task_node.task_properties.task_type for task_node in project.get_trainable_task_nodes()]
        return ImportUtils.task_types_to_project_type(task_types=task_types)

    @classmethod
    def get_validated_task_type(cls, project: Project) -> TaskType:
        """
        Validate project valid for dataset import and return the task type of the project

        :param project_id: str project id
        :return: task type of the (only) trainable task in the project
        """
        supported_types = [
            TaskType.CLASSIFICATION,
            TaskType.DETECTION,
            TaskType.SEGMENTATION,
            TaskType.INSTANCE_SEGMENTATION,
            TaskType.ANOMALY_CLASSIFICATION,
            TaskType.ANOMALY_DETECTION,
            TaskType.ANOMALY_SEGMENTATION,
            TaskType.ANOMALY,
            TaskType.ROTATED_DETECTION,
        ]

        trainable_tasks = project.get_trainable_task_nodes()
        if len(trainable_tasks) > 1:
            raise ValueError("Dataset import is not currently supported for task chain projects.")
        if len(trainable_tasks) < 1:
            raise ValueError("The project doesn't have a trainable task.")
        task_type = trainable_tasks[0].task_properties.task_type
        domain = task_type_to_label_domain(task_type)
        if domain not in SUPPORTED_DOMAINS:
            raise ValueError(
                f"Dataset import is not allowed for '{ImportUtils.task_type_to_rest_api_string(task_type)}' task. "
                f"Allowed task types are {[ImportUtils.task_type_to_rest_api_string(t) for t in supported_types]}"
            )

        return task_type
