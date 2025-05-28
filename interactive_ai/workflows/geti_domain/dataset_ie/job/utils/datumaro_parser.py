# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Parsers to create/update projects from Datumaro dataset"""

import logging
from collections.abc import Sequence
from typing import Any

import datumaro as dm
from geti_telemetry_tools import unified_tracing
from iai_core.entities.model_template import TaskType
from iai_core.factories import ProjectParser
from jobs_common.features.feature_flag_provider import FeatureFlag, FeatureFlagProvider
from jobs_common_extras.datumaro_conversion.convert_utils import ConvertUtils
from jobs_common_extras.datumaro_conversion.definitions import CHAINED_PROJECT_TYPES, GetiProjectType

from job.utils.exceptions import DatasetParsingException
from job.utils.import_utils import ImportUtils

logger = logging.getLogger(__name__)


class DatumaroProjectParser(ProjectParser):
    """
    An implementation of ProjectParser for Datumaro.
    ProjectFactory will call the fucntions in the parser to create a project.

    :param dm_dataset: Datumaro dataset instance
    :param project_name: A name of project to be created
    :param project_type: Geti project type
    :param label_to_ann_types: A mapping of label names in dataset to ann_types with which they appear
    :param selected_labels: label_names that a user selected to include in the created project
    :param color_by_label: Optional, mapping between label names and their color.
        Colors provided through this parameter override the ones in the Dataset, if any.
    :param include_all_labels: if True, ignore selected_labels then include all possible labels for each task_type
    """

    def __init__(  # noqa: PLR0913
        self,
        project_name: str,
        project_type: GetiProjectType,
        dm_infos: dict[str, Any],
        dm_categories: dm.CategoriesInfo,
        label_to_ann_types: dict[str, set[dm.AnnotationType]],
        selected_labels: Sequence[str] | None = None,
        color_by_label: dict[str, str] | None = None,
        include_all_labels: bool = False,
    ) -> None:
        if selected_labels is None:
            selected_labels = ()

        self._project_name: str = project_name
        self._project_type: GetiProjectType = project_type
        self._color_by_label = color_by_label if color_by_label else {}

        (
            self._task_names_ordered,
            self._task_name_to_task_type,
        ) = self._process_task_types(project_type=project_type)

        if project_type in [GetiProjectType.ANOMALY, GetiProjectType.ANOMALY_CLASSIFICATION]:
            label_cat: dm.LabelCategories = dm_categories[dm.AnnotationType.label]
            if label_cat.label_groups:
                label_cat.label_groups = []  # ignore label_groups to generate correct group name for new task

        valid_labels: Sequence[str] = ImportUtils.get_valid_project_labels(
            project_type=project_type,
            dm_infos=dm_infos,
            dm_categories=dm_categories,
            label_to_ann_types=label_to_ann_types,
            selected_labels=selected_labels,
            include_all_labels=include_all_labels,
        )

        self._task_name_to_label_metas: dict[str, dict[str, dict[str, Any]]] = (
            self._extract_labels_metadata_from_dm_dataset(
                dm_infos=dm_infos,
                dm_categories=dm_categories,
                selected_labels=valid_labels,
                include_all_labels=include_all_labels,
            )
        )

        self._keypoint_structure: dict[str, list] = self._extract_keypoint_structure_from_dm_dataset(
            dm_categories=dm_categories,
            selected_labels=valid_labels,
            include_all_labels=include_all_labels,
        )

        self._validate()

    def _validate(self):
        """
        Validate the parsed dataset data
        Raise an exception if parsed data is not proper to create a project
        """

        # 'Minimum 2 top-label calssifcation labels' rule
        # For a classification task, at least 2 labels should be provided.
        # Otherwise the task is ill-defined (a classification model that predicts only 1 class makes no sense).
        # Top-level means at the root level of the hierarchy.
        for task_name in self.get_tasks_names():
            task_type = self.get_task_type_by_name(task_name=task_name)

            if task_type != TaskType.CLASSIFICATION:
                continue

            label_names = self.get_custom_labels_names_by_task(task_name=task_name)

            # collects labels at the top-level
            top_level_label_names = []
            for label_name in label_names:
                parent_name = self.get_label_parent_by_name(task_name=task_name, label_name=label_name)
                if len(parent_name) == 0 or parent_name not in label_names:
                    top_level_label_names.append(label_name)

            if len(top_level_label_names) < 2:
                raise DatasetParsingException(
                    "Failed to parse the dataset: "
                    "At least 2 top level labels should be selected for constructing a classification task: "
                    f"selected [{', '.join(top_level_label_names)}]"
                )

        # 'Minimum 1 + empty labels for a detection task' rule
        for task_name in self.get_tasks_names():
            task_type = self.get_task_type_by_name(task_name=task_name)

            if task_type != TaskType.DETECTION:
                continue

            label_names = self.get_custom_labels_names_by_task(task_name=task_name)

            if len(label_names) < 1:
                raise DatasetParsingException(
                    "Failed to parse the dataset: "
                    "At least 1 labels should be selected for constructing a detection task"
                )

    @staticmethod
    def _get_label_name_to_label_meta(  # noqa: C901
        label_groups: list[dict[str, Any]] | None,
        label_name_to_parent: dict[str, str] | None,
        label_infos: list[dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        """
        Parse label metadata extracted from dm_dataset to generate a mapping from label_name to label_meta
        label_meta contains 'name', 'group', 'parent', 'color', and 'hotkey'

        :param label_groups: metadata for label group information each entry has 'name' and 'labels'
        :param label_name_to_parent: mapping from label_name to parent_name
        :param label_infos: metadata for label 'color' and 'hotkey'

        :return: mapping from label_name to label_meta
        """
        # Store label group name with label_name as key
        label_name_to_group = {}
        if label_groups is not None:
            for label_group in label_groups:
                group_name = label_group["name"]
                label_names = label_group["labels"]
                for label_name in label_names:
                    label_name_to_group[label_name] = group_name

        # label_infos optionaly has 'color, 'hotkey' meta-data
        label_meta: dict[str, dict[str, Any]] = {}
        for label_info in label_infos:
            label_name = label_info["name"]
            label_meta[label_name] = {}
            for info_key in ["color", "hotkey"]:
                if info_key in label_info:
                    label_meta[label_name][info_key] = label_info[info_key]

        # update parent meta-data
        if label_name_to_parent is not None:
            for label_name, _ in label_meta.items():
                if label_name in label_name_to_parent:
                    label_meta[label_name]["parent"] = label_name_to_parent[label_name]

        # update group meta-data
        for label_name, _ in label_meta.items():
            if label_name in label_name_to_group:
                label_meta[label_name]["group"] = label_name_to_group[label_name]

        return label_meta

    def _extract_labels_metadata_from_dm_dataset(
        self,
        dm_infos: dict[str, Any],
        dm_categories: dm.CategoriesInfo,
        selected_labels: Sequence[str],
        include_all_labels: bool = False,
    ) -> dict[str, dict[str, dict[str, Any]]]:
        """
        Parse Datumaro dataset instance to extracte label meta data.
        Label meta data includes 'parent', 'group', 'color', and 'hotkey' of labels

        :param dm_infos: Infos of datumaro dataset.
        :param dm_categories: Categories of datumaro dataset.
        :param selected_labels: label_names that a user selected to include in the created project
        :param include_all_labels: if True, ignore selected_labels then include all possible labels for each task_type
        :return: A dictionary stores label_meta with label_name as key
        """
        (
            label_groups,
            label_name_to_parent,
            label_infos,
        ) = ConvertUtils.get_label_metadata(
            dm_categories=dm_categories,
            dm_infos=dm_infos,
            selected_labels=selected_labels,
            project_type=self._project_type,
            include_all_labels=include_all_labels,
        )

        # mapping of label_name to label_meta
        # label_meta contains 'name', 'group', 'parent', 'hotkey', and 'color'
        label_name_to_label_meta = self._get_label_name_to_label_meta(
            label_groups=label_groups,
            label_name_to_parent=label_name_to_parent,
            label_infos=label_infos,
        )

        # assign task_name to label_meta
        task_name_to_label_meta = {}

        # For chained task, we should detach label_meta for detection task
        if self._project_type in CHAINED_PROJECT_TYPES:
            chained_task_type_with_labels = ImportUtils.parse_chained_task_labels_from_datumaro(dm_infos)

            detection_label_meta: dict[str, Any] = {}
            for task_type, label_names in chained_task_type_with_labels:
                if task_type == TaskType.DETECTION:
                    for label_name in label_names:
                        # label_name_to_label_meta includes the label_metas for the selected_labels
                        # we don't store the label_meta for the un-selected labels
                        if label_name not in label_name_to_label_meta:
                            continue
                        detection_label_meta[label_name] = label_name_to_label_meta[label_name]

            for task_name in self.get_tasks_names():
                task_type = self.get_task_type_by_name(task_name)
                if task_type != TaskType.DETECTION:
                    continue

                task_name_to_label_meta[task_name] = detection_label_meta

            for label_name in detection_label_meta:
                del label_name_to_label_meta[label_name]

        # assign label_metas to the last task
        last_task_name = self.get_tasks_names()[-1]
        last_task_type = self.get_task_type_by_name(task_name=last_task_name)

        # ProjectBuilder will generate Labels with pre-defined metadata for anomaly project
        if include_all_labels or last_task_type not in [
            TaskType.ANOMALY,
            TaskType.ANOMALY_CLASSIFICATION,
            TaskType.ANOMALY_DETECTION,
            TaskType.ANOMALY_SEGMENTATION,
        ]:
            task_name_to_label_meta[last_task_name] = label_name_to_label_meta

        return task_name_to_label_meta

    def _extract_keypoint_structure_from_dm_dataset(
        self,
        dm_categories: dm.CategoriesInfo,
        selected_labels: Sequence[str],
        include_all_labels: bool = False,
    ) -> dict[str, list]:
        """
        Parse Datumaro dataset instance to extract keypoint structure.

        :param dm_categories: Categories of datumaro dataset.
        :param selected_labels: label_names that a user selected to include in the created project
        :param include_all_labels: if True, ignore selected_labels then include all possible labels for each task_type
        :return: A dictionary representing the keypoint structure
        """
        if (
            not FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_KEYPOINT_DETECTION)
            or self._project_type != GetiProjectType.KEYPOINT_DETECTION
        ):
            return {}

        return ConvertUtils.get_keypoint_structure(
            dm_categories=dm_categories,
            selected_labels=selected_labels,
            include_all_labels=include_all_labels,
        )

    @staticmethod
    def _process_task_types(
        project_type: GetiProjectType,
    ) -> tuple[tuple[str, ...], dict[str, TaskType]]:
        """
        Assign task_name to task_type

        :param trainable_task_types: task node types that are trainable
        :return: A list of task_names (used in rest api), A dictionary mapping task_name to task_type
        """
        trainable_task_types = ImportUtils.get_trainable_tasks_of_project_type(project_type=project_type)

        project_task_types: list[TaskType]
        if len(trainable_task_types) == 1:
            project_task_types = [TaskType.DATASET, *trainable_task_types]
        elif len(trainable_task_types) == 2:
            # Only chained-classification/segmentation projects have multiple trainable task_types
            # We allow only [DETECTION, CLASSIFICATION] or [DETECTION, SEGMENTATION]
            if trainable_task_types[0] != TaskType.DETECTION or (
                trainable_task_types[1] != TaskType.CLASSIFICATION and trainable_task_types[1] != TaskType.SEGMENTATION
            ):
                raise DatasetParsingException(
                    "Failed to parse the dataset: "
                    "Unsupported task_names for creating a project: "
                    f"[{', '.join([ImportUtils.task_type_to_rest_api_string(t) for t in trainable_task_types])}]"
                )
            project_task_types = [
                TaskType.DATASET,
                trainable_task_types[0],
                TaskType.CROP,
                trainable_task_types[1],
            ]
        else:
            raise DatasetParsingException(
                "Failed to parse the dataset: "
                "Unsupported task_names for creating a project: "
                f"[{', '.join([ImportUtils.task_type_to_rest_api_string(t) for t in trainable_task_types])}]"
            )

        task_names: list[str] = []
        task_name_to_task_type: dict[str, TaskType] = {}
        for _, task_type in enumerate(project_task_types):
            task_name = ImportUtils.task_type_to_rest_api_string(task_type).replace("_", " ").title()
            task_names.append(task_name)
            task_name_to_task_type[task_name] = task_type

        return tuple(task_names), task_name_to_task_type

    def get_project_name(self) -> str:
        """
        Get the name of the project.

        :return: Project name as a string
        """
        return self._project_name

    def get_connections(self) -> tuple[tuple[str, str], ...]:
        """
        Get the list of connections that determine the topology of the task chain.

        :return: Tuple of tuples (<from>, <to>), where <from> are <to> the names of
        the connected source and destination task nodes, respectively
        """
        connections: list[tuple[str, str]] = []
        for i in range(len(self._task_names_ordered) - 1):
            connection: tuple[str, str] = (
                self._task_names_ordered[i],
                self._task_names_ordered[i + 1],
            )
            connections.append(connection)
        return tuple(connections)

    def get_tasks_names(self) -> tuple[str, ...]:
        """
        Get the names of the task nodes that compose the project.

        :return: Tuple (unordered) of names of the task nodes in the project
        """
        return self._task_names_ordered

    def get_task_type_by_name(self, task_name: str) -> TaskType:
        """
        Get the type of a task node in the project given its name.

        :param task_name: Name of the task node
        :return: Type of the task node
        """
        return self._task_name_to_task_type[task_name]

    def get_custom_labels_names_by_task(self, task_name: str) -> tuple[str, ...]:
        """
        Get the names of the labels defined in a task node.

        :param task_name: Name of the task node
        :return: Tuple (unordered) of names of the custom labels defined in a task
        """
        label_meta = self._task_name_to_label_metas.get(task_name, {})
        return tuple(label_meta.keys())

    def get_keypoint_structure(self) -> dict[str, list]:
        """
        Get the keypoint structure(a.k.a. skeleton/keypoint graph, and positions)
        if the Keypoint Detection task node exists in the project.

        :return: A dictionary representing the keypoint structure
        """
        return self._keypoint_structure

    def _get_label_meta(self, task_name: str, label_name: str) -> dict[str, Any]:
        """
        Get the label_meta of label:label_name in the task:task_name
        label_meta optionaly contains 'group', 'parent', 'color', and 'hotkey'

        :param task_name: Name of the task node
        :param label_name: Name of the label
        :return: label_meta
        """
        label_metas = self._task_name_to_label_metas.get(task_name, {})

        if label_name not in label_metas:
            raise DatasetParsingException(
                "Failed to parse the dataset: "
                f"Can't find metadata of label: task_name - {task_name}, label_name - {label_name}"
            )

        return label_metas[label_name]

    def get_label_group_by_name(self, task_name: str, label_name: str) -> str:
        """
        Get the name of the label group that contains a certain label.

        If the input data source does not have a notion of groups as in Geti, the
        method should return the default group name

        :param task_name: Name of the task where the label is defined
        :param label_name: Name of the label
        :return: Name of the group containing the label
        """
        label_meta = self._get_label_meta(task_name=task_name, label_name=label_name)
        return label_meta.get("group", f"{task_name} Task Labels")

    def get_label_hotkey_by_name(self, task_name: str, label_name: str) -> str:
        """
        Get the hotkey to associate with a certain label.

        :param task_name: Name of the task where the label is defined
        :param label_name: Name of the label
        :return: Hotkey of the label, if any, or an empty string
        """
        label_meta = self._get_label_meta(task_name=task_name, label_name=label_name)
        return label_meta.get("hotkey", "")

    def get_label_color_by_name(self, task_name: str, label_name: str) -> str:
        """
        Get the hex color (e.g. '#f3c3ed') to use for a certain label in the UI.

        If the label is not mapped to a color, or such information is unknown, the
        method shall return an empty string.

        :param task_name: Name of the task where the label is defined
        :param label_name: Name of the label
        :return: Color of the label (hex string), if any, or an empty string
        """
        # To resolve the color, we look in order:
        #  - in the parser arguments
        #  - in the dataset
        color: str = self._color_by_label.get(label_name, "")
        if not color:
            label_meta = self._get_label_meta(task_name=task_name, label_name=label_name)
            return label_meta.get("color", "")
        return color

    def get_label_parent_by_name(self, task_name: str, label_name: str) -> str:
        """
        Get the name of the parent label for a given label.

        :param task_name: Name of the task where the label is defined
        :param label_name: Name of the label
        :return: Name of the parent label, if any, or an empty string
        """
        label_meta = self._get_label_meta(task_name=task_name, label_name=label_name)
        return label_meta.get("parent", "")

    def parse_project_pipeline(self) -> dict[str, Any]:
        """
        Build the 'pipeline' field of the REST API 'datasets:prepare-for-import' endpoint
        retrieving the necessary information from a DatumaroProjectParser.

        :param project_parser: A parser to extract project meta-data from the dataset
        :return: dictionary with the following structure.
            e.g.)
            {
                "pipeline":{
                "connections":[
                {
                    "from": task_name_0,
                    "to": task_name_1,
                },
                ...
                ],
                "tasks":[
                {
                    "title": task_name_0,
                    "task_type": task_type string # e.g.) dataset, classification, ...
                    "labels":[
                        {
                            "name": label_name,
                            "group": label_group name,  # optional
                            "parent": label_parent name,    # optional
                        },
                        ...
                    ]
                },
                ...
                ]
            }
        """
        project_pipeline = {
            "connections": [
                {
                    "from": task_name_from,
                    "to": task_name_to,
                }
                for task_name_from, task_name_to in self.get_connections()
            ],
            "tasks": [],
        }

        tasks = []
        for task_name in self.get_tasks_names():
            task_type = self.get_task_type_by_name(task_name=task_name)
            labels = []

            label_names = self.get_custom_labels_names_by_task(task_name=task_name)
            for label_name in label_names:
                label_item = {
                    "name": label_name,
                }

                label_group = self.get_label_group_by_name(task_name=task_name, label_name=label_name)
                if len(label_group) > 0:
                    label_item["group"] = label_group.split("___")[-1]

                label_parent = self.get_label_parent_by_name(task_name=task_name, label_name=label_name)
                if len(label_parent) > 0 and label_parent in label_names:
                    label_item["parent"] = label_parent

                labels.append(label_item)

            task_type_name = task_type.name.lower()  # OTX TaskType name != ImportUtils.task_type_to_rest_api_string()
            task: dict[str, Any] = {
                "title": task_name,  # generated from ImportUtils.task_type_to_rest_api_string(...)
                "task_type": task_type_name,  # OTX TaskType name
                "labels": labels,
            }
            if (
                FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_KEYPOINT_DETECTION)
                and task_type == TaskType.KEYPOINT_DETECTION
            ):
                # need 'keypoint_structure' field in the task
                # "keypoint_structure": [
                #     "edges": [
                #         {"nodes": [label1, label2]},
                #          ...,
                #     ],
                #     "positions": [
                #         {"label": label1, "x": 0.5, "y": 0.5},
                #         ...,
                #     ]
                # ]
                task["keypoint_structure"] = self.get_keypoint_structure()

            tasks.append(task)
        project_pipeline["tasks"] = tasks  # type: ignore

        return project_pipeline

    def get_project_meta(self) -> dict[str, Any]:
        return {
            "project_type": self._project_type,
            "pipeline": self.parse_project_pipeline(),
        }

    def get_keypoint_structure_data(self, task_name: str) -> dict[str, list]:
        project_pipeline = self.parse_project_pipeline()
        for task in project_pipeline["tasks"]:
            if task.get("keypoint_structure", {}) and task["title"] == task_name:
                return task["keypoint_structure"]
        return {}


def get_filtered_supported_project_types(
    dm_infos: dict[str, Any], label_to_ann_types: dict[str, set[dm.AnnotationType]]
) -> list[GetiProjectType]:
    """
    Return possible project types based on CVS-105432, excluding cross-mapping projects.

    Project mapping is different based on the dataset format.
    For Geti-exported Datumaro format:
      candaidates should be the task type itself (+ cross-mapping projects).
    For public formats(coco, voc, yolo) + Datumaro format not exported from Geti:
      candidate tasks would be decided based on annotation types.
      - label -> classification
      - bbox -> detection
      - polygon/ellipse/mask -> segmentation.
    """
    exported_project_type = ImportUtils.get_exported_project_type(dm_infos)
    if exported_project_type != GetiProjectType.UNKNOWN:
        filtered_supported_project_types = [exported_project_type]
    else:
        filtered_supported_project_types = []
        ann_types = set()
        for types in label_to_ann_types.values():
            ann_types.update(types)
        if dm.AnnotationType.label in ann_types:
            filtered_supported_project_types.append(GetiProjectType.CLASSIFICATION)
        if dm.AnnotationType.bbox in ann_types:
            filtered_supported_project_types.append(GetiProjectType.DETECTION)
        if (
            dm.AnnotationType.polygon in ann_types
            or dm.AnnotationType.ellipse in ann_types
            or dm.AnnotationType.mask in ann_types
        ):
            filtered_supported_project_types.extend(
                [GetiProjectType.SEGMENTATION, GetiProjectType.INSTANCE_SEGMENTATION]
            )
        if (
            FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_KEYPOINT_DETECTION)
            and dm.AnnotationType.points in ann_types
        ):
            filtered_supported_project_types.append(GetiProjectType.KEYPOINT_DETECTION)

    return filtered_supported_project_types


@unified_tracing
def get_project_metas_with_labels(
    dm_infos: dict[str, Any],
    dm_categories: dm.CategoriesInfo,
    label_to_ann_types: dict[str, set[dm.AnnotationType]],
) -> list[dict[str, Any]]:
    """
    Get mapping of domains to label names in the dataset. The list of labels for the
    domain will be filled with the labels which are compatible with the domain.

    :param dm_dataset: datumaro dataset
    :return: A list containing a dictionary for each supported task with their
    compatible labels, list of possible domains in dataset based on present
    annotation types
    """

    # Project mapping is different based on the dataset format. (CVS-105432)
    # For Geti-exported Datumaro format:
    #   candaidates should be the task type itself + cross-mapping projects.
    # For public formats(coco, voc, yolo) + Datumaro format not exported from Geti:
    #   candidate tasks would be decided based on annotation types.
    #   - label -> classification
    #   - bbox -> detection
    #   - polygon/ellipse/mask -> segmentation.

    filtered_supported_project_types = get_filtered_supported_project_types(
        dm_infos=dm_infos, label_to_ann_types=label_to_ann_types
    )

    # Extract project meta-data that will be utilized when build a REST API response
    project_metas_with_labels: list[dict[str, Any]] = []
    for project_type in filtered_supported_project_types:
        try:
            project_parser = DatumaroProjectParser(
                project_name=f"prepare {ImportUtils.project_type_to_rest_api_string(project_type)} project",
                project_type=project_type,
                dm_infos=dm_infos,
                dm_categories=dm_categories,
                label_to_ann_types=label_to_ann_types,
                include_all_labels=True,
            )
            n_project_label_metas = 0
            for task_name in project_parser.get_tasks_names():
                n_project_label_metas += len(project_parser.get_custom_labels_names_by_task(task_name=task_name))
            if n_project_label_metas == 0:
                continue
            project_metas_with_labels.append(project_parser.get_project_meta())
        except Exception as e:
            logger.warning(
                "dm_dataset is not suitable to be parsed as "
                f"{ImportUtils.project_type_to_rest_api_string(project_type)}: {e}"
            )

    # Re-map project_type for hierarchical classifcation task.
    # Note that single-label/multi-label/hierarchical classification project has the same project_type in Geti.
    # But we should distinguish hierarchical classification on REST API
    for project_meta in project_metas_with_labels:
        project_type = project_meta["project_type"]
        if project_type == GetiProjectType.CLASSIFICATION and ImportUtils.is_dataset_from_hierarchical_classification(
            dm_categories, dm_infos
        ):
            project_type = GetiProjectType.HIERARCHICAL_CLASSIFICATION
        project_meta["project_type"] = project_type

    return project_metas_with_labels
