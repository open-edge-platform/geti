# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import abc
import copy
import logging
from typing import Any, NamedTuple

import datumaro as dm
from datumaro.components.annotation import GroupType
from datumaro.components.dataset_base import DatasetInfo
from datumaro.components.transformer import ItemTransform
from geti_types import ProjectIdentifier
from iai_core.entities.model_template import TaskType
from iai_core.entities.project import Project
from jobs_common.features.feature_flag_provider import FeatureFlag, FeatureFlagProvider
from jobs_common_extras.datumaro_conversion.definitions import GetiProjectType

from job.utils.datumaro_parser import DatumaroProjectParser
from job.utils.exceptions import ResearvedLabelException, UnsupportedMappingException
from job.utils.import_utils import ImportUtils

logger = logging.getLogger(__name__)

# TODO: Refactoring and re-design.
# Whole design of CrossProjectMapper will be changed while refactoring.
# Currently, this is just for adding functionality.


class LabelInfo(NamedTuple):
    info: DatasetInfo
    categories: dm.CategoriesInfo
    label_to_ann_types: dict[str, set[dm.AnnotationType]]


class CrossProjectConverterBase(metaclass=abc.ABCMeta):
    """This interface represents the cross-project mapper."""

    def convert_annotation_type(self, dm_dataset: dm.Dataset) -> None:
        """Convert annotations according to dst project type."""
        # no transform basically

    def get_converted_label_info(
        self,
        dm_infos: dict[str, Any],
        dm_categories: dm.CategoriesInfo,
        dst: GetiProjectType,
        label_to_ann_types: dict[str, set[dm.AnnotationType]] = {},
    ) -> LabelInfo:
        """label-to-ann_types mapping and update it if needed."""
        infos = copy.deepcopy(dm_infos)
        infos["GetiProjectTask"] = ImportUtils.project_type_to_rest_api_string(dst)
        catetories = copy.deepcopy(dm_categories)
        label_cat: dm.LabelCategories = catetories[dm.AnnotationType.label]
        if label_cat.label_groups:
            label_cat.label_groups = []  # ignore label_groups to generate correct group name for new task
        return LabelInfo(infos, catetories, copy.deepcopy(label_to_ann_types))

    def apply_converted_label_info(self, dm_dataset: dm.Dataset, dst: GetiProjectType) -> None:
        label_info = self.get_converted_label_info(
            dm_infos=dm_dataset.infos(), dm_categories=dm_dataset.categories(), dst=dst
        )
        dm_dataset.transform("project_labels", dst_labels=label_info.categories[dm.AnnotationType.label])
        dm_dataset.transform("project_infos", dst_infos=label_info.info, overwrite=False)


class CrossProjectConverterDetToRot(CrossProjectConverterBase):
    def convert_annotation_type(self, dm_dataset: dm.Dataset) -> None:
        """Ignore(remove) existing polygons and convert bboxes to polygons."""
        dm_dataset.filter("/item/annotation[type!='polygon']", filter_annotations=True)
        dm_dataset.transform("boxes_to_polygons")

    def get_converted_label_info(
        self,
        dm_infos: dict[str, Any],
        dm_categories: dm.CategoriesInfo,
        dst: GetiProjectType,
        label_to_ann_types: dict[str, set[dm.AnnotationType]] = {},
    ) -> LabelInfo:
        """Update label_to_ann_types mapping from detection to rotated detection."""
        label_info = super().get_converted_label_info(
            dm_infos=dm_infos,
            dm_categories=dm_categories,
            dst=dst,
            label_to_ann_types=label_to_ann_types,
        )
        if label_to_ann_types:
            for _, ann_types in label_info.label_to_ann_types.items():
                if dm.AnnotationType.bbox in ann_types:
                    ann_types.remove(dm.AnnotationType.bbox)
                    ann_types.add(dm.AnnotationType.polygon)
                else:
                    ann_types.remove(dm.AnnotationType.polygon)
        return label_info


class CrossProjectConverterDetToCls(CrossProjectConverterBase):
    """
    Detection to multi-label classification
    """

    class BboxToLabel(ItemTransform):
        def transform_item(self, item: dm.DatasetItem) -> dm.DatasetItem | None:
            annotations = []
            for ann in item.annotations:
                if isinstance(ann, dm.Bbox) and getattr(ann, "label") is not None:
                    annotations.append(dm.Label(label=ann.label))
            return self.wrap_item(item, annotations=annotations)

    def convert_annotation_type(self, dm_dataset: dm.Dataset) -> None:
        """Convert bbox to label and filter out other annotations."""
        # assume that the dataset categories are updated already.
        dm_dataset.transform(self.BboxToLabel)

    def get_converted_label_info(
        self,
        dm_infos: dict[str, Any],
        dm_categories: dm.CategoriesInfo,
        dst: GetiProjectType,
        label_to_ann_types: dict[str, set[dm.AnnotationType]] = {},
    ) -> LabelInfo:
        """Update label_to_ann_types mapping from segmentation to detection."""
        label_info = super().get_converted_label_info(
            dm_infos=dm_infos,
            dm_categories=dm_categories,
            dst=dst,
            label_to_ann_types=label_to_ann_types,
        )

        # make label_groups for multi-label classification
        label_cat: dm.LabelCategories = label_info.categories[dm.AnnotationType.label]
        for label in label_cat:
            label_cat.add_label_group(
                name=f"Classification Task Labels for '{label.name}'",
                labels=[label.name],
                group_type=GroupType.EXCLUSIVE,
            )

        # convert bbox to label and ignore all other annotation types
        if label_to_ann_types:
            for label, ann_types in label_info.label_to_ann_types.items():
                if dm.AnnotationType.bbox in ann_types:
                    label_info.label_to_ann_types[label] = {dm.AnnotationType.label}
                else:
                    ann_types.clear()
        return label_info


class CrossProjectConverterSegToDet(CrossProjectConverterBase):
    _SHAPES = {
        dm.AnnotationType.polygon,
        dm.AnnotationType.ellipse,
        dm.AnnotationType.mask,
        dm.AnnotationType.polyline,
        dm.AnnotationType.points,
    }

    def convert_annotation_type(self, dm_dataset: dm.Dataset) -> None:
        """Convert ellipse, mask, polygon to (surrounding) bbox."""
        dm_dataset.transform("shapes_to_boxes")

    def get_converted_label_info(
        self,
        dm_infos: dict[str, Any],
        dm_categories: dm.CategoriesInfo,
        dst: GetiProjectType,
        label_to_ann_types: dict[str, set[dm.AnnotationType]] = {},
    ) -> LabelInfo:
        """Update label_to_ann_types mapping from segmentation to detection."""
        label_info = super().get_converted_label_info(
            dm_infos=dm_infos,
            dm_categories=dm_categories,
            dst=dst,
            label_to_ann_types=label_to_ann_types,
        )
        if label_to_ann_types:
            for _, ann_types in label_info.label_to_ann_types.items():
                intersection = self._SHAPES & ann_types
                if intersection:
                    for type in intersection:
                        ann_types.remove(type)
                    ann_types.add(dm.AnnotationType.bbox)
        return label_info


class CrossProjectConverterRotToDet(CrossProjectConverterSegToDet):
    _SHAPES = {
        dm.AnnotationType.polygon,
    }


class CrossProjectConverterAnomalyDetSegToCls(CrossProjectConverterBase):
    def convert_annotation_type(self, dm_dataset: dm.Dataset) -> None:
        """Ignore(remove) existing non-label annotations."""
        dm_dataset.filter("/item/annotation[type=='label']", filter_annotations=True)


class CrossProjectConverterSegToDetSeg(CrossProjectConverterBase):
    DEFAULT_DETECTION_LABEL = "detection label"

    class AddBoxesToShapes(ItemTransform):
        def __init__(self, extractor: dm.IDataset, label_id: int):
            super().__init__(extractor)
            self._label_id = label_id

        def transform_item(self, item: dm.DatasetItem) -> dm.DatasetItem | None:
            annotations = copy.deepcopy(item.annotations)
            for ann in item.annotations:
                if hasattr(ann, "get_bbox"):
                    annotations.append(self.convert_shape(ann, self._label_id))
            return self.wrap_item(item, annotations=annotations)

        @staticmethod
        def convert_shape(shape: dm.Annotation, label_id: int) -> dm.Annotation:
            bbox = shape.get_bbox()
            return dm.Bbox(
                *bbox,
                label=label_id,
                z_order=shape.z_order,
                id=shape.id,
                group=shape.group,
            )

    def get_converted_label_info(
        self,
        dm_infos: dict[str, Any],
        dm_categories: dm.CategoriesInfo,
        dst: GetiProjectType,
        label_to_ann_types: dict[str, set[dm.AnnotationType]] = {},
    ) -> LabelInfo:
        """Add default detection label"""
        label_info = super().get_converted_label_info(
            dm_infos=dm_infos,
            dm_categories=dm_categories,
            dst=dst,
            label_to_ann_types=label_to_ann_types,
        )
        label_cat: dm.LabelCategories = label_info.categories[dm.AnnotationType.label]
        segmentation_labels = [cat.name for cat in label_cat]
        detection_label = self.DEFAULT_DETECTION_LABEL
        label_cat.add(name=detection_label)
        if label_to_ann_types:
            if detection_label in label_info.label_to_ann_types:
                raise ResearvedLabelException(
                    f"{detection_label} is reserved label for detection task. "
                    "Cannot import the dataset to chained_detection_segmentation project."
                )
            label_info.label_to_ann_types[detection_label] = {dm.AnnotationType.bbox}
        label_info.info["GetiTaskTypeLabels"] = [
            [
                ImportUtils.task_type_to_rest_api_string(TaskType.DETECTION),
                [detection_label],
            ],
            [
                ImportUtils.task_type_to_rest_api_string(TaskType.SEGMENTATION),
                segmentation_labels,
            ],
        ]

        return label_info

    def convert_annotation_type(self, dm_dataset: dm.Dataset) -> None:
        """Add bbox for each shapes."""
        # assume that the dataset categories are updated already.
        label_cat: dm.LabelCategories = dm_dataset.categories()[dm.AnnotationType.label]
        label_id, _ = label_cat.find(self.DEFAULT_DETECTION_LABEL)
        dm_dataset.transform(self.AddBoxesToShapes, label_id=label_id)


class CrossProjectConverterDetSegToSeg(CrossProjectConverterBase):
    @staticmethod
    def _get_task_to_labels(dm_infos: DatasetInfo) -> dict[TaskType, list[str]]:
        chained_task_type_with_labels = ImportUtils.parse_chained_task_labels_from_datumaro(dm_infos)
        task_to_labels = {}
        for task_type, label_names in chained_task_type_with_labels:
            task_to_labels[task_type] = label_names
        return task_to_labels

    def convert_annotation_type(self, dm_dataset: dm.Dataset) -> None:
        """Drop detection bboxes."""
        # remove annotations for detection
        task_to_labels = self._get_task_to_labels(dm_dataset.infos())
        for label in task_to_labels[TaskType.DETECTION]:
            dm_dataset.filter(f"/item/annotation[label!='{label}']", filter_annotations=True)

    def get_converted_label_info(
        self,
        dm_infos: dict[str, Any],
        dm_categories: dm.CategoriesInfo,
        dst: GetiProjectType,
        label_to_ann_types: dict[str, set[dm.AnnotationType]] = {},
    ) -> LabelInfo:
        """Remove detection labels"""
        label_info = super().get_converted_label_info(
            dm_infos=dm_infos,
            dm_categories=dm_categories,
            dst=dst,
            label_to_ann_types=label_to_ann_types,
        )
        task_to_labels = self._get_task_to_labels(dm_infos)
        segmentation_labels = task_to_labels[TaskType.SEGMENTATION]
        if label_to_ann_types:
            for label in task_to_labels[TaskType.DETECTION]:
                label_info.label_to_ann_types.pop(label, None)
            for label in segmentation_labels:
                if label not in label_info.label_to_ann_types:
                    label_info.label_to_ann_types[label] = {dm.AnnotationType.polygon}
        label_info.info["GetiTaskTypeLabels"] = []  # remove chained info
        label_info.categories[dm.AnnotationType.label] = dm.LabelCategories.from_iterable(segmentation_labels)
        label_info.categories[dm.AnnotationType.mask] = dm.MaskCategories.generate(len(segmentation_labels))
        return label_info


class CrossProjectConverterDetSegToDet(CrossProjectConverterDetSegToSeg):
    def convert_annotation_type(self, dm_dataset: dm.Dataset) -> None:
        """
        Drop detection bboxes + convert segmentation shapes to (surrounding) bbox.
        Use labels from segmentation task.
        """
        # remove annotations for detection
        super().convert_annotation_type(dm_dataset)
        # convert shapes to bbox
        dm_dataset.transform("shapes_to_boxes")


class CrossProjectConverterDetSegToRot(CrossProjectConverterDetSegToDet):
    def convert_annotation_type(self, dm_dataset: dm.Dataset) -> None:
        """
        Drop detection bboxes + convert segmentation shapes to (surrounding) bbox, and then convert bboxes to polygons.
        Use labels from segmentation task.
        """
        super().convert_annotation_type(dm_dataset)
        dm_dataset.transform("boxes_to_polygons")


class Mapping(NamedTuple):
    src: GetiProjectType
    dst: GetiProjectType


# The supported cross-project mappings that need annotation type conversion.
SUPPORTED_CROSS_PROJECT_MAPPINGS: dict[GetiProjectType, dict[GetiProjectType, Any]] = {
    GetiProjectType.DETECTION: {
        GetiProjectType.ROTATED_DETECTION: CrossProjectConverterDetToRot,
        GetiProjectType.CLASSIFICATION: CrossProjectConverterDetToCls,
    },
    GetiProjectType.ROTATED_DETECTION: {
        GetiProjectType.DETECTION: CrossProjectConverterRotToDet,
    },
    GetiProjectType.SEGMENTATION: {
        GetiProjectType.DETECTION: CrossProjectConverterSegToDet,
        GetiProjectType.INSTANCE_SEGMENTATION: CrossProjectConverterBase,
        GetiProjectType.CHAINED_DETECTION_SEGMENTATION: CrossProjectConverterSegToDetSeg,
    },
    GetiProjectType.INSTANCE_SEGMENTATION: {
        GetiProjectType.DETECTION: CrossProjectConverterSegToDet,
        GetiProjectType.SEGMENTATION: CrossProjectConverterBase,
        GetiProjectType.CHAINED_DETECTION_SEGMENTATION: CrossProjectConverterSegToDetSeg,
    },
    GetiProjectType.ANOMALY_CLASSIFICATION: {
        GetiProjectType.CLASSIFICATION: CrossProjectConverterBase,
    },
    GetiProjectType.ANOMALY_DETECTION: {
        GetiProjectType.CLASSIFICATION: CrossProjectConverterAnomalyDetSegToCls,
        GetiProjectType.ANOMALY_CLASSIFICATION: CrossProjectConverterAnomalyDetSegToCls,
    },
    GetiProjectType.ANOMALY_SEGMENTATION: {
        GetiProjectType.CLASSIFICATION: CrossProjectConverterAnomalyDetSegToCls,
        GetiProjectType.ANOMALY_CLASSIFICATION: CrossProjectConverterAnomalyDetSegToCls,
        GetiProjectType.ANOMALY_DETECTION: CrossProjectConverterSegToDet,
    },
    GetiProjectType.CHAINED_DETECTION_SEGMENTATION: {
        GetiProjectType.DETECTION: CrossProjectConverterDetSegToDet,
        GetiProjectType.ROTATED_DETECTION: CrossProjectConverterDetSegToRot,
        GetiProjectType.SEGMENTATION: CrossProjectConverterDetSegToSeg,
        GetiProjectType.INSTANCE_SEGMENTATION: CrossProjectConverterDetSegToSeg,
    },
}


class CrossProjectMapper:
    @staticmethod
    def check_if_cross_project_mapping_for_new_project(
        dm_dataset: dm.Dataset,
        label_to_ann_types: dict[str, set[dm.AnnotationType]],
        project_metas_with_labels,  # noqa: ANN001
    ) -> None:
        """
        Check if the dataset can be imported to another type of project,
        and update `project_metas_with_labels`.

        :param dm_dataset: Datumaro dataset
        :param project_metas_with_labels: A list containing a dictionary for
        each supported task with their compatible labels, list of possible domains
        """
        # we do not support cross mapping for the non-geti-exported format dataset
        exported_type = ImportUtils.get_exported_project_type(dm_dataset.infos())
        if exported_type == GetiProjectType.UNKNOWN:
            return

        possible_project_types = [project_meta["project_type"] for project_meta in project_metas_with_labels]

        def exists_in_candidates(project_type: GetiProjectType):
            return any(project_meta["project_type"] == project_type for project_meta in project_metas_with_labels)

        cross_project_mapping = {*()}
        dm_infos = dm_dataset.infos()
        dm_categories = dm_dataset.categories()
        for src, _ in SUPPORTED_CROSS_PROJECT_MAPPINGS.items():
            if src not in possible_project_types:
                continue
            for dst in SUPPORTED_CROSS_PROJECT_MAPPINGS[src]:
                if exists_in_candidates(dst):
                    continue

                if (
                    FeatureFlagProvider.is_enabled(feature_flag=FeatureFlag.FEATURE_FLAG_ANOMALY_REDUCTION)
                    and dst == GetiProjectType.ANOMALY_DETECTION
                ):
                    # all anomaly datasets can be mapped to anomaly cls. or cls. only.
                    continue

                converter = SUPPORTED_CROSS_PROJECT_MAPPINGS[src][dst]
                label_info: LabelInfo = converter().get_converted_label_info(
                    dm_infos, dm_categories, dst, label_to_ann_types
                )
                ## create project_meta
                try:
                    project_parser = DatumaroProjectParser(
                        project_name=f"prepare {ImportUtils.project_type_to_rest_api_string(dst)} project",
                        project_type=dst,
                        dm_infos=label_info.info,
                        dm_categories=label_info.categories,
                        label_to_ann_types=label_info.label_to_ann_types,
                        include_all_labels=True,
                    )
                    project_meta = project_parser.get_project_meta()
                    project_metas_with_labels.append(project_meta)
                    mapping_str = tuple(map(ImportUtils.project_type_to_rest_api_string, (src, dst)))
                    cross_project_mapping.add(mapping_str)
                except Exception as e:
                    logger.warning(
                        "dm_dataset is not suitable to be parsed as "
                        f"{ImportUtils.project_type_to_rest_api_string(dst)}: {e}"
                    )

        # Leave cross-project mapping information to dm_dataset for annotation type conversion.
        # Conversion will be done when importing the prepared dataset.
        if cross_project_mapping:
            dm_infos = {"CrossProjectMapping": list(cross_project_mapping)}
            dm_dataset.transform("project_infos", dst_infos=dm_infos, overwrite=False)

    @staticmethod
    def check_if_cross_project_mapping_for_existing_project(
        dm_dataset: dm.Dataset,
        label_to_ann_types: dict[str, set[dm.AnnotationType]],
        project_type: GetiProjectType,
        project_identifier: ProjectIdentifier,
    ) -> tuple[str, ...]:
        """
        Check if the dataset can be imported to specific type of project,
        and return compatible labels.

        :param dm_dataset: Datumaro dataset
        :param label_to_ann_types: Dictionary from label to datumaro annotation types.
        :param project_type: Geti Project Type to import.
        :param project_idendifier: Identifier of the project.
        :return label_names: Compatible labels to given project type.
        """
        # we do not support cross mapping for the non-geti-exported format dataset
        dm_infos = dm_dataset.infos()
        exported_type = ImportUtils.get_exported_project_type(dm_infos)  # src
        if exported_type == GetiProjectType.UNKNOWN:
            return ()

        cross_project_mapping: tuple | None = None
        # find source project type
        label_names = ()
        mapping = Mapping(exported_type, project_type)
        converter = SUPPORTED_CROSS_PROJECT_MAPPINGS.get(mapping.src, {}).get(mapping.dst)
        if converter is not None:
            label_info: LabelInfo = converter().get_converted_label_info(
                dm_infos, dm_dataset.categories(), mapping.dst, label_to_ann_types
            )
            # check if this is a 'detection->multi-label cls.' case
            if mapping.src == GetiProjectType.DETECTION and mapping.dst == GetiProjectType.CLASSIFICATION:
                # we don't support 'detection' to 's-cls / h-cls'.
                is_hierarchical, is_multi_labels = ImportUtils.is_task_hierarhical_or_multi_labels(
                    project_identifier=project_identifier
                )
                if is_hierarchical or not is_multi_labels:
                    return label_names  # empty label_names

            label_names = ImportUtils.get_valid_project_labels(
                project_type=project_type,
                dm_infos=label_info.info,
                dm_categories=label_info.categories,
                label_to_ann_types=label_info.label_to_ann_types,
                include_all_labels=True,
            )
            if label_names:  # cross-mapping case
                cross_project_mapping = tuple(map(ImportUtils.project_type_to_rest_api_string, mapping))

        # Leave cross-project mapping information to dm_dataset for annotation type conversion.
        # Conversion will be done when importing the prepared dataset.
        if cross_project_mapping:
            dm_infos = {"CrossProjectMapping": [cross_project_mapping]}
            dm_dataset.transform("project_infos", dst_infos=dm_infos, overwrite=False)

        return label_names

    @staticmethod
    def convert_annotation_type_for_cross_project(
        dm_dataset: dm.Dataset,
        project_type: GetiProjectType,
    ) -> None:
        """
        For cross-project mapping case, convert annotation type according to the project_type.

        :param dm_dataset: Datumaro dataset
        :param project_type: Geti project type
        """
        # we do not support cross mapping for the non-geti-exported format dataset
        dm_infos = dm_dataset.infos()
        exported_type = ImportUtils.get_exported_project_type(dm_infos)
        if exported_type == GetiProjectType.UNKNOWN:
            return

        mapping = Mapping(exported_type, project_type)
        # We saved mappings as 'tuple' but, json converts 'tuple' to 'list'.
        mapping_str = list(map(ImportUtils.project_type_to_rest_api_string, mapping))
        if "CrossProjectMapping" in dm_infos and mapping_str in dm_infos["CrossProjectMapping"]:
            converter = SUPPORTED_CROSS_PROJECT_MAPPINGS.get(mapping.src, {}).get(mapping.dst)
            if converter is not None:
                if mapping.dst == GetiProjectType.CHAINED_DETECTION_SEGMENTATION:
                    converter().apply_converted_label_info(dm_dataset, mapping.dst)
                    converter().convert_annotation_type(dm_dataset)
                else:
                    converter().convert_annotation_type(dm_dataset)
                    converter().apply_converted_label_info(dm_dataset, mapping.dst)
            else:
                logger.exception(f"cross-project mapping for {mapping} isn't supported.")
                raise UnsupportedMappingException(
                    f"Failed to import `{mapping_str[0]}` dataset to "
                    f"`{mapping_str[1]}` project: unsupported cross-project mapping"
                )

    @staticmethod
    def is_cross_mapping_case_for_geti_exported_dataset(
        dm_categories: dm.CategoriesInfo, dm_infos: dict[str, Any], project: Project
    ) -> bool:
        project_type = ImportUtils.get_project_type(project=project)
        exported_type = ImportUtils.get_exported_project_type(dm_infos)
        if exported_type == GetiProjectType.UNKNOWN:
            return False

        if project_type != exported_type and not (
            project_type == GetiProjectType.HIERARCHICAL_CLASSIFICATION
            and exported_type == GetiProjectType.CLASSIFICATION
        ):
            # we do not support cross-project mapping here.
            return True

        if project_type in [
            GetiProjectType.CLASSIFICATION,
            GetiProjectType.HIERARCHICAL_CLASSIFICATION,
        ]:
            # we do not support cross-project mapping among
            # single-label, multi-label, and hierarchical classification.
            is_dataset_hierarchical = ImportUtils.is_dataset_from_hierarchical_classification(
                dm_categories=dm_categories, dm_infos=dm_infos
            )

            is_task_hierarchical, is_task_multi_labels = ImportUtils.is_task_hierarhical_or_multi_labels(
                project_identifier=project.identifier
            )
            if is_task_hierarchical:
                return not is_dataset_hierarchical

            # Here, task is multi or single labels classification
            return (
                is_dataset_hierarchical
                or ImportUtils.is_dataset_from_multi_label_classification(
                    dm_categories=dm_categories, dm_infos=dm_infos
                )
                != is_task_multi_labels
            )

        return False
