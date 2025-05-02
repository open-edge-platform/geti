# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements import utilities
"""

import logging
from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import datumaro as dm
from datumaro import ImportErrorPolicy, errors
from datumaro.components.errors import AnnotationImportError, ItemImportError, MultipleFormatsMatchError
from iai_core_py.entities.label import Domain
from iai_core_py.entities.model_template import TaskType, task_type_to_label_domain
from iai_core_py.entities.project import Project

from jobs_common.features.feature_flag_provider import FeatureFlag, FeatureFlagProvider
from jobs_common_extras.datumaro_conversion.definitions import (
    ANNOTATION_TYPE_TO_SUPPORTED_DOMAINS,
    CHAINED_PROJECT_TYPES,
    FORMAT_NAME_MAP,
    GetiProjectType,
)

logger = logging.getLogger(__name__)


class ScImportErrorPolicy(ImportErrorPolicy):
    """
    Import error policy used to collect errors encountered during dataset parsing
    """

    def __init__(self) -> None:
        self.errors: list[errors.ItemImportError] = []

    def _handle_item_error(self, error):  # noqa: ANN001
        self.errors.append(error)

    def _handle_annotation_error(self, error):  # noqa: ANN001
        self.errors.append(error)


@dataclass
class ImportErrorDetail:
    """
    Data class used to collect number of different types of
    errors and warnings in dataset
    """

    n_item_parsing_errors: int = 0
    n_annotation_parsing_errors: int = 0
    n_multi_label_errors: int = 0
    n_classification_missing_ann_errors: int = 0
    n_detection_missing_ann_errors: int = 0
    n_segmentation_missing_ann_errors: int = 0
    n_merged_subsets: int = 0


STR_DETECTION_ORIENTED: str = "detection_oriented"

SUPPORTED_DOMAINS = [
    Domain.CLASSIFICATION,
    Domain.DETECTION,
    Domain.SEGMENTATION,
    Domain.INSTANCE_SEGMENTATION,
    Domain.ANOMALY_CLASSIFICATION,
    Domain.ANOMALY_DETECTION,
    Domain.ANOMALY_SEGMENTATION,
    Domain.ROTATED_DETECTION,
]


class ImportUtils:
    @staticmethod
    def detect_format(path: str) -> str:
        """
        Detect format of dataset in path

        :param path: path of the dataset
        :return: detected format of the dataset
        """
        try:
            dataset_format = dm.Dataset.detect(path)
        except MultipleFormatsMatchError as ex:
            intersection = list(set(ex.formats) & set(FORMAT_NAME_MAP.keys()))
            if len(intersection) == 1:
                dataset_format = intersection[0]
            else:
                raise

        if dataset_format not in FORMAT_NAME_MAP:
            raise KeyError(dataset_format)

        return dataset_format

    @classmethod
    def parse_dataset(cls, path: str, fmt: str) -> tuple[dm.Dataset, ScImportErrorPolicy]:
        """
        Parse dataset into datumaro format.

        :param path: path to dataset
        :param fmt: format of the dataset
        :return: datumaro dataset and error collector object.
        """
        fmt = FORMAT_NAME_MAP[fmt]

        # For DmStreamDataset, the error collecting will be conducted later during iterating items.
        # Therefore, error_collector.errors must be accessed after the iterator runs.
        # And adding a progress_reporter here would result in inaccurate reporting
        # due to the same reason (Actual iteration would occur later).
        error_collector = ScImportErrorPolicy()
        dm_dataset = dm.StreamDataset.import_from(path, fmt, error_policy=error_collector)

        return dm_dataset, error_collector

    @staticmethod
    def is_dataset_from_multi_label_classification(
        dm_categories: dm.CategoriesInfo,
        dm_infos: dict[str, Any],
    ) -> bool:
        """
        Check if given dm_dataset is exported from multi-label classification

        :param dm_categories: Categories of Datumaro dataset obejct
        :param dm_infos: Infos of Datumaro dataset obejct
        :return: True if dm_dataset is exported from multi-label classification project
        """
        project_type = ImportUtils.get_exported_project_type(dm_infos)
        if project_type != GetiProjectType.CLASSIFICATION:
            return False

        label_cat: dm.LabelCategories = dm_categories[dm.AnnotationType.label]

        dm_label_groups: list[dm.LabelCategories.LabelGroup] = label_cat.label_groups

        dm_grouped_labels = []
        dm_groups = []
        for dm_label_group in dm_label_groups:
            dm_grouped_labels += dm_label_group.labels
            dm_groups.append(dm_label_group.name)

        return len(dm_groups) > 1 and len(dm_groups) == len(dm_grouped_labels)

    @staticmethod
    def get_exported_project_type(dm_infos: dict[str, Any]) -> GetiProjectType:
        """
        Find the Geti project type where dm_dataset is exported from

        :param dm_infos: Infos of Datumaro dataset obejct
        :return: Geti project type
        """
        project_task_type: str = dm_infos.get("GetiProjectTask", "NONE")
        project_type = ImportUtils.rest_task_type_to_project_type(project_task_type)
        if project_type == GetiProjectType.UNKNOWN:
            logger.info("The dataset is not exported from Geti('GetiProjectTask': '{project_task_type}')")
        if project_type == GetiProjectType.KEYPOINT_DETECTION and not FeatureFlagProvider.is_enabled(
            FeatureFlag.FEATURE_FLAG_KEYPOINT_DETECTION
        ):
            project_type = GetiProjectType.UNKNOWN
        return project_type

    @staticmethod
    def is_dataset_from_hierarchical_classification(
        dm_categories: dm.CategoriesInfo,
        dm_infos: dict[str, Any],
    ) -> bool:
        """
        Check if given dm_dataset is exported from hierarchical classification

        :param dm_categories: Categories of Datumaro dataset obejct
        :param dm_infos: Infos of Datumaro dataset obejct
        :return: True if dm_dataset is exported from hierarchical classification project
        """
        project_type = ImportUtils.get_exported_project_type(dm_infos)
        if project_type != GetiProjectType.CLASSIFICATION:
            return False

        label_cat: dm.LabelCategories = dm_categories[dm.AnnotationType.label]
        dm_label_groups: list[dm.LabelCategories.LabelGroup] = label_cat.label_groups

        has_tree_structure = any(len(cate_item.parent) > 0 for cate_item in label_cat.items)

        is_multi_label_classification = ImportUtils.is_dataset_from_multi_label_classification(dm_categories, dm_infos)

        return has_tree_structure or (len(dm_label_groups) > 1 and not is_multi_label_classification)

    @staticmethod
    def _create_import_error_details(parsing_errors: list[Exception]) -> ImportErrorDetail:
        """
        Create import error details data object and initialize it with the number of parsing errors
        encountered when parsing dataset

        :param parsing_errors: list of parsing exceptions
        :return: ImportErrorDetail object initialized with number of parsing errors
        """
        n_annotation_parse_errors = 0
        n_item_parse_error = 0

        # remove duplication
        unique_errors: list[Exception] = []
        for error in parsing_errors:
            if error not in unique_errors:
                unique_errors.append(error)

        for parse_error in unique_errors:
            if isinstance(parse_error, AnnotationImportError):
                n_annotation_parse_errors += 1
            elif isinstance(parse_error, ItemImportError):
                n_item_parse_error += 1
            else:
                logger.warning(
                    "Encountered unknown parsing error of type %s",
                    str(type(parse_error)),
                )
        return ImportErrorDetail(
            n_item_parsing_errors=n_item_parse_error, n_annotation_parsing_errors=n_annotation_parse_errors
        )

    @staticmethod
    def _get_label_name_to_group(label_groups: list[dm.LabelCategories.LabelGroup]) -> dict[str, str]:
        """
        Get a mapping between label names and label group names

        :param label_groups: label groups within a specific dataset
        :return: dictionary containing the mapping between label names and label group names
        """
        label_name_to_group = {}
        for label_group in label_groups:
            for idx, label_name in enumerate(label_group.labels):
                suffix = f"_{idx}" if label_group.group_type != "exclusive" else ""
                label_name_to_group[label_name] = label_group.name + suffix
        return label_name_to_group

    @staticmethod
    def _validate_annotations(
        item: dm.DatasetItem,
        label_categories: dm.LabelCategories,
        label_name_to_group: dict[str, str],
    ) -> tuple[dict[str, int], bool]:
        """
        Validate each dataset item whether to have no annotation or multiple annotations

        :param item: dataset item
        :param label_categories: label categories within a dataset
        :param label_name_to_group: mapping between label names and label group names
        :return: number of label, bbox, mask annotations within a item and multi-label flag
        """
        number_of_labels: dict[str, int] = defaultdict(lambda: 0)
        multi_label_flag: bool = False

        occupied_groups = set()
        for ann in item.annotations:
            if ann.type == dm.AnnotationType.label:
                label_group = label_name_to_group.get(label_categories[ann.label].name, "")
                if label_group in occupied_groups:
                    multi_label_flag = True
                occupied_groups.add(label_group)
                number_of_labels["label"] += 1
            elif ann.type == dm.AnnotationType.bbox:
                number_of_labels["bbox"] += 1
            elif ann.type in [dm.AnnotationType.mask, dm.AnnotationType.polygon, dm.AnnotationType.ellipse]:
                number_of_labels["mask"] += 1

        return number_of_labels, multi_label_flag

    @classmethod
    def _validate_dataset(
        cls,
        dm_dataset: dm.Dataset,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict[str, Any]:
        """
        Validate datumaro dataset using a given validator and collecting errors with types of interest

        :param dm_dataset: datumaro dataset to validate
        :param possible_domains: possible task types to validate
        :param progress_callback: An optional callback function that takes two integers
                                  (current progress, total) and returns None. It is called
                                  to update the progress of the operation.
        :return: list of relevant errors in dataset
        """

        # [TODO] update Datumaro validator to generate a report for multiple tasks and specific anomaly types
        # Temporarily implement the custom validator for ["MissingAnnotation", "MultiLabelAnnotations"]
        # in ["CLS", "DET", "SEG"]
        label_cat = dm_dataset.categories()[dm.AnnotationType.label]
        label_name_to_group = cls._get_label_name_to_group(label_cat.label_groups)

        reports = defaultdict(set)
        total = len(dm_dataset)
        for i, item in enumerate(dm_dataset):
            if progress_callback:
                progress_callback(i, total)

            if not isinstance(item.media, dm.Image | dm.VideoFrame | dm.Video) or (
                isinstance(item.media, dm.Video)
                and (item.attributes.get("has_empty_label", False) or item.annotations)  # video annotation range
            ):
                continue
            number_of_labels, multi_label_flag = cls._validate_annotations(item, label_cat, label_name_to_group)
            if multi_label_flag:
                reports["items_multiple_annotation_cls"].add((item.id, item.subset))
            if number_of_labels["label"] == 0:
                reports["items_missing_annotation_cls"].add((item.id, item.subset))
            if number_of_labels["bbox"] == 0:
                reports["items_missing_annotation_det"].add((item.id, item.subset))
            if number_of_labels["mask"] == 0:
                reports["items_missing_annotation_seg"].add((item.id, item.subset))

        return reports

    @classmethod
    def collect_validation_warnings(
        cls,
        dm_dataset: dm.Dataset,
        possible_domains: set[Domain],
        parsing_errors: list[Exception],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> ImportErrorDetail:
        """
        Collect number of non-actionable errors (warnings) in dataset using different validators
        for supported task types in dataset, skip classification since classificaiton errors
        were collected earlier

        :param dm_dataset: datumaro dataset to validate for warnings
        :param possible_domains: list of possible domains in dataset
        :param parsing_errors: warnings obtained during dataset parsing
        :param progress_callback: An optional callback function that takes two integers
                                  (current progress, total) and returns None. It is called
                                  to update the progress of the operation.
        :return: list of validation warnings
        """

        error_details = cls._create_import_error_details(parsing_errors)
        error_details.n_merged_subsets = max(len(dm_dataset.subsets()) - 1, 0)

        val_report = cls._validate_dataset(dm_dataset, progress_callback)

        if Domain.CLASSIFICATION not in possible_domains:
            error_details.n_classification_missing_ann_errors = 0
        else:
            missing_annotation_items = val_report["items_missing_annotation_cls"]
            multi_label_items = val_report["items_multiple_annotation_cls"]
            for _mapping in dm_dataset.infos().get("CrossProjectMapping", {}):
                mapping = tuple(map(cls.rest_task_type_to_project_type, _mapping))
                if mapping[1] == GetiProjectType.CLASSIFICATION and mapping[0] == GetiProjectType.DETECTION:
                    # detection -> multi-label classification
                    multi_label_items.clear()  # multi-label warning is not valid.
                    missing_annotation_items = val_report["items_missing_annotation_det"]  # no bbox -> no label
                    break
            if len(multi_label_items) > 0:
                dm_infos = {"multi_anns": list(multi_label_items)}
                dm_dataset.transform("project_infos", dst_infos=dm_infos, overwrite=False)
            missing_annotation_items.update(multi_label_items)

            error_details.n_classification_missing_ann_errors = len(missing_annotation_items)
            error_details.n_multi_label_errors = len(multi_label_items)

        if Domain.DETECTION in possible_domains:
            target_key = "items_missing_annotation_det"
            for _mapping in dm_dataset.infos().get("CrossProjectMapping", {}):
                mapping = tuple(map(cls.rest_task_type_to_project_type, _mapping))
                if mapping[1] == GetiProjectType.DETECTION and mapping[0] in [
                    GetiProjectType.ROTATED_DETECTION,
                    GetiProjectType.SEGMENTATION,
                    GetiProjectType.INSTANCE_SEGMENTATION,
                ]:
                    target_key = "items_missing_annotation_seg"
                    break
            error_details.n_detection_missing_ann_errors = len(val_report[target_key])

        if Domain.SEGMENTATION in possible_domains or Domain.INSTANCE_SEGMENTATION in possible_domains:
            error_details.n_segmentation_missing_ann_errors = len(val_report["items_missing_annotation_seg"])

        return error_details

    @classmethod
    def parse_chained_task_labels_from_datumaro(
        cls, dm_infos: dict[str, Any]
    ) -> tuple[tuple[TaskType, tuple[str, ...]], ...]:
        """
        Parse label_names by task_type in a chained project from a dm_dataset

        :param dm_infos: infos of datumaro dataset
        :return: A tuple of (TaskType, tuple of label_names)
        """
        exported_project_type = cls.get_exported_project_type(dm_infos)

        if exported_project_type not in CHAINED_PROJECT_TYPES:
            return ()

        dm_tasktype_labelnames = dm_infos.get("GetiTaskTypeLabels", [])

        tasktype_label_names = []
        for task_type_name, label_names in dm_tasktype_labelnames:
            try:
                task_type = TaskType[task_type_name.upper()]
            except KeyError:
                # due to CVS-133054, task_type name for ROTATED_DETECTION is "detection_oriented"
                if task_type.name.lower() == STR_DETECTION_ORIENTED:
                    task_type = TaskType.ROTATED_DETECTION
                else:
                    error_message = f"The task type '{task_type_name}' in the 'GetiTaskTypeLabels' is not supported."
                    logger.error(error_message)
                    raise ValueError(error_message)
            tasktype_label_names.append((task_type, label_names))

        return tuple(tasktype_label_names)

    @classmethod
    def get_label_to_ann_types(
        cls,
        dm_dataset: dm.Dataset,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict[str, set[dm.AnnotationType]]:
        """
        Get a mapping of label names in dataset to ann_types with which they appear

        :param dm_dataset: datumaro dataset
        :param progress_callback: An optional callback function that takes two integers
                                  (current progress, total) and returns None. It is called
                                  to update the progress of the operation.
        :return: dictionary mapping label names to a set of dm annotation type
        """
        label_cat: dm.LabelCategories = dm_dataset.categories()[dm.AnnotationType.label]

        # label_names = [label_item.name for label_item in label_cat]

        label_idx_to_ann_types = defaultdict(set)
        total = len(dm_dataset)
        for i, dm_item in enumerate(dm_dataset):
            if progress_callback:
                progress_callback(i, total)
            if not isinstance(dm_item.media, dm.Image | dm.VideoFrame):
                continue
            for dm_ann in dm_item.annotations:
                label_id = getattr(dm_ann, "label", None)
                if label_id is not None:
                    label_idx_to_ann_types[label_id].add(dm_ann.type)
                # TODO: need to check if this is needed.
                # for dm_attr_key in dm_ann.attributes:
                #     if dm_attr_key in label_names:
                #         label_id = label_names.index(dm_attr_key)
                #         label_idx_to_ann_types[label_id].add(dm.AnnotationType.label)

        return {label_cat[label_id].name: types for label_id, types in label_idx_to_ann_types.items()}

    @classmethod
    def get_valid_project_labels(  # noqa: C901
        cls,
        project_type: GetiProjectType,
        dm_infos: dict[str, Any],
        dm_categories: dm.CategoriesInfo,
        label_to_ann_types: dict[str, set[dm.AnnotationType]],
        selected_labels: Sequence[str] | None = None,
        include_all_labels: bool | None = False,
    ) -> tuple[str, ...]:
        """
        Find the labels that is valid for the target project_type

        :param project_type: Geti project type
        :param dm_infos: infos of datumaro dataset
        :param dm_categories: Categories of Datumaro dataset obejct
        :param label_to_ann_types: A mapping of label names in dataset to ann_types with which they appear
        :param selected_labels: label_names that a user selected to include in the created project
        :param include_all_labels: If True, ignore selected_labels then include all possible labels for each task_type
        :return: Names of the labels that are valid for the given project type
        """

        def _get_valid_labels_based_on_domain(label_domain: Domain) -> set[str]:
            valid_labels = set()
            for label_name, ann_types in label_to_ann_types.items():
                domains = set()
                for ann_type in ann_types:
                    domains.update(ANNOTATION_TYPE_TO_SUPPORTED_DOMAINS[ann_type])

                if label_domain in domains:
                    valid_labels.add(label_name)

                if (
                    project_type == GetiProjectType.CHAINED_DETECTION_CLASSIFICATION
                    and Domain.CLASSIFICATION in domains
                ):
                    valid_labels.add(label_name)
            return valid_labels

        def _get_keypoint_labels() -> dict[str, list[str]]:
            keypoint_labels: dict[str, list[str]] = {}
            point_cat: dm.PointsCategories = dm_categories.get(dm.AnnotationType.points, None)
            if point_cat:
                label_cat: dm.LabelCategories = dm_categories[dm.AnnotationType.label]
                for label_id, cat in point_cat.items.items():
                    try:
                        label = label_cat[label_id].name
                        keypoint_labels[label] = cat.labels
                    except IndexError:
                        continue
            return keypoint_labels

        if selected_labels is None and not include_all_labels:
            raise ValueError(
                "label_names to be included should be passed by selected_labels."
                "If not, included_all_labels should be True to include all labels"
            )

        if selected_labels is None:
            selected_labels = ()

        exported_project_type = ImportUtils.get_exported_project_type(dm_infos)

        # keep only selected labels with a valid domain for the project type
        label_domain = ImportUtils.project_type_to_label_domain(project_type=project_type)
        if label_domain == Domain.NULL:
            raise ValueError(f"Invalid project type '{project_type}'")
        all_valid_label_names = _get_valid_labels_based_on_domain(label_domain)

        # if the target project_type and the exported project_type are match,
        # restore all labels from the label schema
        if exported_project_type != GetiProjectType.UNKNOWN and (
            project_type == exported_project_type
            or (
                project_type == GetiProjectType.HIERARCHICAL_CLASSIFICATION
                and exported_project_type == GetiProjectType.CLASSIFICATION
            )
        ):
            label_cat: dm.LabelCategories = dm_categories[dm.AnnotationType.label]
            all_valid_label_names.update([dm_label_item.name for dm_label_item in label_cat.items])

        # Since the label_domain only concern for the lastest trainable task,
        # we should search labels for the intermediate tasks even if they are not used for actual annotation.
        if project_type in CHAINED_PROJECT_TYPES:
            chained_task_type_with_labels = ImportUtils.parse_chained_task_labels_from_datumaro(dm_infos)
            for _, label_names in chained_task_type_with_labels[:-1]:
                all_valid_label_names.update(label_names)
        elif project_type == GetiProjectType.KEYPOINT_DETECTION:
            keypoint_labels = _get_keypoint_labels()
            valid_keypoint_labels = []
            for bbox_label, point_labels in keypoint_labels.items():
                try:
                    all_valid_label_names.remove(bbox_label)  # we don't use detection labels in keypoint detection task
                    valid_keypoint_labels.extend(point_labels)
                except KeyError:
                    continue
            all_valid_label_names.update(valid_keypoint_labels)  # add keypoint labels

        # update selected_labels with consideration of valid for the project_type
        if include_all_labels:
            return tuple(all_valid_label_names)

        return tuple(label_name for label_name in selected_labels if label_name in all_valid_label_names)

    @staticmethod
    def parse_errors(
        error_details: ImportErrorDetail,
    ) -> list[dict]:
        """
        Parse validation and parsing errors and warnings and convert them to a user-readable format.

        :param error_details: ImportErrorDetail object with number of errors and warnings
        :return: list of dicts representing errors and warnings
        """

        result = []
        if error_details.n_annotation_parsing_errors > 0:
            result.append(
                {
                    "type": "error",
                    "name": "Annotation parsing error",
                    "description": "Could not parse annotation in uploaded dataset",
                    "resolve_strategy": "Skip annotation",
                    "affected_images": error_details.n_annotation_parsing_errors,
                }
            )
        if error_details.n_item_parsing_errors > 0:
            result.append(
                {
                    "type": "error",
                    "name": "Dataset item parsing error",
                    "description": "Could not parse dataset item in uploaded dataset",
                    "resolve_strategy": "Skip dataset item",
                    "affected_images": error_details.n_item_parsing_errors,
                }
            )
        if error_details.n_multi_label_errors > 0:
            result.append(
                {
                    "type": "error",
                    "name": "Multi label annotation error",
                    "description": "Annotation contains more than one classification label",
                    "resolve_strategy": "Skip annotation",
                    "affected_images": error_details.n_multi_label_errors,
                }
            )
        if error_details.n_classification_missing_ann_errors > 0:
            result.append(
                {
                    "type": "warning",
                    "name": "Missing expected annotation type for classification domain",
                    "description": "Image contains no global label",
                    "affected_images": error_details.n_classification_missing_ann_errors,
                }
            )
        if error_details.n_detection_missing_ann_errors > 0:
            result.append(
                {
                    "type": "warning",
                    "name": "Missing expected annotation type for detection domain",
                    "description": "Image contains no bounding boxes",
                    "affected_images": error_details.n_detection_missing_ann_errors,
                }
            )
        if error_details.n_segmentation_missing_ann_errors > 0:
            result.append(
                {
                    "type": "warning",
                    "name": "Missing expected annotation type for segmentation domain",
                    "description": "Image contains no polygons",
                    "affected_images": error_details.n_segmentation_missing_ann_errors,
                }
            )
        if error_details.n_merged_subsets > 0:
            result.append(
                {
                    "type": "warning",
                    "name": "Subset merging",
                    "description": "The images in the imported dataset could already be assigned to "
                    "training, validation and testing subsets. However, in the current "
                    "version, this information will be lost after the import. The "
                    "images will be assigned to new subsets based on the distribution "
                    "of labels.",
                }
            )
        return result

    @staticmethod
    def task_type_to_rest_api_string(task_type: TaskType) -> str:
        """
        Convert TaskType to task_type string for REST API

        :param task_type: OTX task type identifier
        :return: task name for REST API
        """
        if (
            FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_ANOMALY_REDUCTION)
            and task_type == TaskType.ANOMALY_CLASSIFICATION
        ):
            return "anomaly"
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
        if FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_ANOMALY_REDUCTION):
            exceptions[GetiProjectType.ANOMALY_CLASSIFICATION] = "anomaly"
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
    def get_trainable_tasks_of_project_type(
        project_type: GetiProjectType,
    ) -> list[TaskType]:
        """
        Get a list of trainable_tasks for a project

        :param project_type: target geti project_type
        :return: a list of trainable task_types for the project
        """
        mapper = {
            GetiProjectType.CLASSIFICATION: [TaskType.CLASSIFICATION],
            GetiProjectType.DETECTION: [TaskType.DETECTION],
            GetiProjectType.SEGMENTATION: [TaskType.SEGMENTATION],
            GetiProjectType.ANOMALY_CLASSIFICATION: [TaskType.ANOMALY_CLASSIFICATION],
            GetiProjectType.ANOMALY_DETECTION: [TaskType.ANOMALY_DETECTION],
            GetiProjectType.ANOMALY_SEGMENTATION: [TaskType.ANOMALY_SEGMENTATION],
            GetiProjectType.INSTANCE_SEGMENTATION: [TaskType.INSTANCE_SEGMENTATION],
            GetiProjectType.ROTATED_DETECTION: [TaskType.ROTATED_DETECTION],
            GetiProjectType.CHAINED_DETECTION_CLASSIFICATION: [
                TaskType.DETECTION,
                TaskType.CLASSIFICATION,
            ],
            GetiProjectType.CHAINED_DETECTION_SEGMENTATION: [
                TaskType.DETECTION,
                TaskType.SEGMENTATION,
            ],
        }
        if FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_KEYPOINT_DETECTION):
            mapper[GetiProjectType.KEYPOINT_DETECTION] = [TaskType.KEYPOINT_DETECTION]

        if project_type not in mapper:
            logger.warning(f"Can't find mapping from {project_type.name.lower()} to TaskTypes")

        return mapper.get(project_type, [])

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

    @staticmethod
    def project_type_to_label_domain(project_type: GetiProjectType) -> Domain:
        """
        Get an label domain of interest by project_type

        :param project_type: project_type
        :return: label domain related to the project_type
        """
        mapper = {
            GetiProjectType.UNKNOWN: Domain.NULL,
            GetiProjectType.CLASSIFICATION: Domain.CLASSIFICATION,
            GetiProjectType.HIERARCHICAL_CLASSIFICATION: Domain.CLASSIFICATION,
            GetiProjectType.DETECTION: Domain.DETECTION,
            GetiProjectType.SEGMENTATION: Domain.SEGMENTATION,
            GetiProjectType.ANOMALY_CLASSIFICATION: Domain.ANOMALY_CLASSIFICATION,
            GetiProjectType.ANOMALY_DETECTION: Domain.ANOMALY_DETECTION,
            GetiProjectType.ANOMALY_SEGMENTATION: Domain.ANOMALY_SEGMENTATION,
            GetiProjectType.INSTANCE_SEGMENTATION: Domain.INSTANCE_SEGMENTATION,
            GetiProjectType.ROTATED_DETECTION: Domain.ROTATED_DETECTION,
            # For CHAINED_DETECTION_CLSSIFICATION project, we interest in bbox annotations in dm_dataset
            GetiProjectType.CHAINED_DETECTION_CLASSIFICATION: Domain.DETECTION,
            # For CHAINED_DETECTION_SEGMENTATION project, we interest in bbox, polygon, and ellipse annotations
            # Note that Domain.SEGMENTATION includes all of them.
            GetiProjectType.CHAINED_DETECTION_SEGMENTATION: Domain.SEGMENTATION,
        }

        if FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_KEYPOINT_DETECTION):
            mapper[GetiProjectType.KEYPOINT_DETECTION] = Domain.KEYPOINT_DETECTION

        return mapper.get(project_type, Domain.NULL)

    @staticmethod
    def get_new_dataset_name(project: Project) -> str:
        """
        Checks to make sure that no new dataset is made with duplicate names

        :param project: project to check the dataset storage names
        """
        dataset_name = "Testing set"
        dataset_storages = project.get_dataset_storages()
        names = [dataset_storage.name for dataset_storage in dataset_storages]
        i = 1
        while dataset_name in names:
            names.remove(dataset_name)
            dataset_name = f"Testing set {i}"
            i += 1

        return dataset_name

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
