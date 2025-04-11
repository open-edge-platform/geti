# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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

import logging

from communication.rest_views.dataset_storage_rest_views import DatasetStorageRESTViews
from communication.rest_views.performance_rest_views import PerformanceRESTViews
from communication.rest_views.pipeline import PipelineRESTViews

from geti_telemetry_tools import unified_tracing
from geti_types import ID
from sc_sdk.entities.label_schema import LabelSchemaView
from sc_sdk.entities.project import Project

logger = logging.getLogger(__name__)

ARCHIVED = "archived"
CREATION_TIME = "creation_time"
CREATOR = "creator_id"
DATASETS = "datasets"
DESCRIPTION = "description"
DIMENSIONS = "dimensions"
GROUP_TYPE = "group_type"
ID_ = "id"
ITEMS = "items"
PROJECT_COUNTS = "project_counts"
PROJECT_PAGE_COUNT = "project_page_count"
NEXT_PAGE = "next_page"
LABELS = "labels"
NAME = "name"
PIPELINE = "pipeline"
PIPELINE_REPRESENTATION = "pipeline_representation"
PERFORMANCE = "performance"
PROJECTS = "projects"
SELECTED = "selected"
SIZE = "size"
STORAGE_INFO = "storage_info"
THUMBNAIL = "thumbnail"
TYPE = "type"


class ProjectRESTViews:
    @staticmethod
    @unified_tracing
    def project_to_rest(
        organization_id: ID,
        project: Project,
        storage_info: dict,
        label_schema_per_task: dict[ID, LabelSchemaView],
        include_deleted_labels: bool = False,
        include_dataset_storages: bool = True,
    ) -> dict:
        """
        :param organization_id: ID of the organization
        :param project: project to convert to rest
        :param storage_info: storage info of the project
        :param label_schema_per_task: The label schema for each task node
        :param include_deleted_labels: If the rest representation should include labels
        that have been deleted
        :param include_dataset_storages: If true, include dataset storage information for the project.
        :return project converted to rest
        """
        project_rest = {
            ID_: str(project.id_),
            NAME: project.name,
            CREATION_TIME: project.creation_date.isoformat(),
            CREATOR: project.creator_id,
            PIPELINE: PipelineRESTViews.task_graph_to_rest(
                graph=project.task_graph,
                label_schema_per_task=label_schema_per_task,
                include_deleted_labels=include_deleted_labels,
                keypoint_structure=project.keypoint_structure,
            ),
            THUMBNAIL: f"/api/v1/organizations/{organization_id}/workspaces/{project.workspace_id}"
            f"/projects/{str(project.id_)}/thumbnail",
            PERFORMANCE: PerformanceRESTViews.project_performance_to_rest(project_performance=project.performance),
            STORAGE_INFO: storage_info,
        }
        if include_dataset_storages:
            dataset_storages = project.get_dataset_storages()
            project_rest |= DatasetStorageRESTViews.dataset_storages_to_rest(dataset_storages)
        return project_rest

    @staticmethod
    @unified_tracing
    def projects_to_rest(
        organization_id: ID,
        projects: list[Project],
        label_schema_per_task_per_project: list[dict[ID, LabelSchemaView]],
        project_counts: int,
        next_page: str,
        storage_info_per_project: list[dict],
    ) -> dict:
        """
        :param organization_id: ID of the organization
        :param projects: Projects to convert to rest
        :param label_schema_per_task_per_project: A list of the label schema for each task node,
         for each project in the projects list.
        :param project_counts: number of total projects
        :param next_page: url to request the next page
        :param storage_info_per_project: Whether to include (this will calculate) the project's size
        when listing all projects this is not wanted because it is time-consuming.
        :return: Projects converted to rest
        """
        project_list = []
        for project, label_schema_per_task, storage_info in zip(
            projects, label_schema_per_task_per_project, storage_info_per_project
        ):
            try:
                project_list.append(
                    ProjectRESTViews.project_to_rest(
                        organization_id=organization_id,
                        project=project,
                        label_schema_per_task=label_schema_per_task,
                        storage_info=storage_info,
                        include_dataset_storages=False,
                    )
                )
            except Exception:
                logger.exception(
                    "Project %s (ID %s) could not be converted to REST, skipping it.",
                    project.name,
                    project.id_,
                )
        return {
            PROJECTS: project_list,
            PROJECT_COUNTS: project_counts,
            PROJECT_PAGE_COUNT: len(projects),
            NEXT_PAGE: next_page,
        }

    @staticmethod
    def projects_names_to_rest(projects_names: dict[ID, str]) -> dict[str, list[dict[str, str]]]:
        return {PROJECTS: [{ID_: str(id_), NAME: projects_names[id_]} for id_ in projects_names]}
