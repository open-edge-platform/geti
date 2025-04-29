# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, NamedTuple

import datumaro as dm
import numpy as np
import pytest
from datumaro.components.annotation import GroupType, LabelCategories
from jobs_common.features.feature_flag_provider import FeatureFlag, FeatureFlagProvider
from jobs_common_extras.datumaro_conversion.definitions import GetiProjectType
from sc_sdk.entities.label import Domain

from job.utils.constants import MIN_IMAGE_SIZE

LabelDefinition = int
PointsDefinition = tuple[int, ...]
AnnotationDefinition = list[tuple[str, LabelDefinition | PointsDefinition]]
DatasetDefinition = dict[str, AnnotationDefinition]


@pytest.fixture
def fxt_bbox_dataset_definition():
    return {"item1": [("bbox", 2), ("bbox", 1)], "item2": [("bbox", 0), ("bbox", 3)]}


@pytest.fixture
def fxt_polygon_dataset_definition():
    return {
        "item1": [("polygon", 2)],
        "item2": [("polygon", 0), ("polygon", 3)],
    }


@pytest.fixture
def fxt_polygon_and_ellipse_dataset_definition(fxt_polygon_dataset_definition):
    fxt_polygon_dataset_definition["item3"] = [("ellipse", 1)]
    return fxt_polygon_dataset_definition


@pytest.fixture
def fxt_polygon_coco_dataset_definition():
    return {
        "item1": [("bbox", 0), ("polygon", 0)],
        "item2": [("bbox", 3), ("polygon", 3)],
    }


@pytest.fixture
def fxt_global_labels_dataset_definition():
    return {"item1": [("label", 1)], "item2": [("label", 0)], "item3": [("label", 2)]}


@pytest.fixture
def fxt_anomaly_classification_dataset_definition():
    return {"item1": [("label", 1)], "item2": [("label", 0)], "item3": [("label", 0)]}


@pytest.fixture
def fxt_anomaly_detection_dataset_definition():
    return {
        "item1": [("label", 1), ("bbox", 1)],
        "item2": [("label", 1), ("bbox", 1), ("bbox", 1)],
        "item3": [("label", 0)],
    }


@pytest.fixture
def fxt_anomaly_segmentation_dataset_definition():
    return {
        "item1": [("label", 1), ("polygon", 1)],
        "item2": [("label", 1), ("polygon", 1), ("ellipse", 1)],
        "item3": [("label", 0)],
    }


@pytest.fixture
def fxt_multi_label_dataset_definition():
    return {
        "item1": [("label", 1), ("label", 3)],
        "item2": [("label", 0)],
        "item3": [("label", 2)],
    }


@pytest.fixture
def fxt_rotated_detection_dataset_definition():
    return {
        "item1": [("polygon", 0), ("polygon", 1)],
        "item2": [("polygon", 0)],
    }


@pytest.fixture
def fxt_bbox_polygon_dataset_definition():
    return {"item1": [("bbox", 2), ("bbox", 1), ("polygon", 1)]}


@pytest.fixture
def fxt_single_points_dataset_definition():
    return {
        "item1": [("points", (2, 2, 2, 2))],
        "item2": [("points", (0, 1, 2, 2))],
        "item3": [("points", (2, 2, 1, 2))],
    }


@pytest.fixture
def fxt_dataset_labels():
    return [
        {"name": "cat", "color": "#d46156ff"},
        {"name": "dog", "color": "#cd5dfbff"},
        {"name": "truck", "color": "#59eb19ff"},
        {"name": "bus", "color": "#e09281ff"},
    ]


@pytest.fixture
def fxt_anomaly_dataset_labels():
    return [
        {"name": "Normal", "color": "#d46156ff"},
        {"name": "Anomalous", "color": "#cd5dfbff", "is_anomalous": True},
    ]


@pytest.fixture
def fxt_points_dataset_labels():
    return [
        {"name": "p1", "color": "#d46156ff"},
        {"name": "p2", "color": "#cd5dfbff"},
        {"name": "p3", "color": "#59eb19ff"},
        {"name": "p4", "color": "#e09281ff"},
    ]


@pytest.fixture
def fxt_mixed_labels_dataset_definition():
    return {
        "item1": [("bbox", 2), ("bbox", 1), ("polygon", 0)],
        "item2": [("label", 0), ("bbox", 3), ("bbox", 0), ("polygon", 1)],
        "item3": [("label", 0), ("polygon", 2)],
        "item4": [("label", 2)],
    }


@pytest.fixture
def fxt_mask_voc_dataset_definition():
    return {
        "item1": [("mask", 2)],
        "item2": [("mask", 1)],
        "item3": [("mask", 3)],
    }


def _make_dataset_item(
    item_id: str,
    shapes_and_labels: Sequence[tuple[str, Any]],
    subset: str = dm.DEFAULT_SUBSET_NAME,
) -> dm.DatasetItem:
    """
    Generate a dm dataset item given its id, shapes and relative labels.

    :param item_id: identifier of the item
    :param shapes_and_labels: List of pairs (shape_type, label), each representing an
        annotation. Shape type is a string with values in ("bbox", "polygon", "label"),
        while the label can be anything (usually an integer).
    :param subset: Subset name of the item
    :return: dm dataset item
    """
    annotations: list[dm.Annotation] = []
    group_offset = 10
    default_mask = np.zeros((MIN_IMAGE_SIZE, MIN_IMAGE_SIZE))
    default_mask[5:10, 5:10] = 1
    for shape_type, label in shapes_and_labels:
        if shape_type is None or label is None:
            continue
        if shape_type == "bbox":
            shape = dm.Bbox(1, 2, 5, 6, label=label, group=len(annotations) + group_offset)
        elif shape_type == "polygon":
            shape = dm.Polygon([1, 1, 5, 1, 5, 5], label=label, group=len(annotations) + group_offset)
        elif shape_type == "label":
            shape = dm.Label(label=label)
        elif shape_type == "ellipse":
            shape = dm.Ellipse(5, 6, 7, 9, label=label, group=len(annotations) + group_offset)
        elif shape_type == "mask":
            shape = dm.Mask(image=default_mask, label=label, group=len(annotations) + group_offset)
        elif shape_type == "points":
            # label in points means visibility. Its label is always 0.
            points = [i for i in label for _ in range(2)]
            shape = dm.Points(points=points, visibility=list(label), label=0, group=len(annotations) + group_offset)
        else:
            raise ValueError("shape_type not in supported types: [bbox, polygon, label, ellipse, mask]")
        annotations.append(shape)
    dataset_item = dm.DatasetItem(
        id=item_id,
        subset=subset,
        media=dm.Image.from_numpy(
            np.ones((MIN_IMAGE_SIZE, MIN_IMAGE_SIZE, 3)), ext=".jpg", size=(MIN_IMAGE_SIZE, MIN_IMAGE_SIZE)
        ),
        annotations=annotations,
    )
    return dataset_item


@pytest.fixture
def fxt_dm_dataset_item_generator() -> Callable[[str, str | None, Any], dm.DatasetItem]:
    """
    Generate a dm dataset item with one annotation, given its id, shape type and label
    """

    def _get_dataset_item(item_id: str, shape_type: str | None, label: Any) -> dm.DatasetItem:
        shapes_and_labels: tuple[tuple[str, Any], ...]
        if shape_type is None or label is None:
            shapes_and_labels = ()
        else:
            shapes_and_labels = ((shape_type, label),)
        return _make_dataset_item(item_id=item_id, shapes_and_labels=shapes_and_labels)

    return _get_dataset_item


@pytest.fixture
def fxt_dm_dataset_generator() -> Callable[
    [Sequence[str] | dm.CategoriesInfo, Mapping[str, Sequence[tuple[str, Any]]]], dm.Dataset
]:
    """
    Generates dm dataset from a dataset definition and list of labels
    Dataset definitions map item names to list of tuples of annotation type and label index.
    """

    def _get_dataset(
        labels: Sequence[str] | dm.CategoriesInfo,
        dataset_definition: Mapping[str, Sequence[tuple[str, Any]]],
        subsets: Sequence[str] = (dm.DEFAULT_SUBSET_NAME,),
    ) -> dm.Dataset:
        dataset_items = []
        has_mask = False
        has_points = False
        for item_name, shape_type_to_label in dataset_definition.items():
            for subset in subsets:
                dataset_items.append(
                    _make_dataset_item(
                        item_id=item_name,
                        shapes_and_labels=shape_type_to_label,
                        subset=subset,
                    )
                )
            for shape_type, _ in shape_type_to_label:
                if shape_type == "mask":
                    has_mask = True
                elif shape_type == "points":
                    has_points = True

        if has_mask:
            categories: Sequence[str] | dm.CategoriesInfo = {
                dm.AnnotationType.label: dm.LabelCategories.from_iterable(labels),
                dm.AnnotationType.mask: dm.MaskCategories.generate(len(labels)),
            }
        elif has_points:
            # labels in points means point labels for the 1st label('object').
            categories = {
                dm.AnnotationType.label: dm.LabelCategories.from_iterable(["object"]),  # detection label
                dm.AnnotationType.points: dm.PointsCategories.from_iterable(
                    [(0, list(labels), {(1, i + 1) for i in range(1, len(labels))})]
                ),
            }
        else:
            categories = labels

        return dm.Dataset.from_iterable(
            dataset_items,
            categories=categories,
        )

    return _get_dataset


@pytest.fixture
def fxt_datumaro_bbox_polygon_dataset(
    fxt_dm_dataset_generator, fxt_dataset_labels, fxt_bbox_polygon_dataset_definition
):
    label_names = [label["name"] for label in fxt_dataset_labels]
    return fxt_dm_dataset_generator(label_names, fxt_bbox_polygon_dataset_definition)


@pytest.fixture
def fxt_dm_categories_generator() -> Callable[[str, str, Sequence[str]], LabelCategories]:
    def _get_categories(
        global_parent_name: str,
        global_group_name: str,
        label_names: Sequence[str],
    ) -> LabelCategories:
        label_categories = LabelCategories()

        for label_name in label_names:
            label_categories.add(label_name, parent=global_parent_name)
        if len(global_parent_name) > 0:
            label_categories.add(global_parent_name)
        label_categories.add_label_group(name=global_group_name, labels=label_names, group_type=GroupType.EXCLUSIVE)

        return label_categories

    return _get_categories


class WarningMissinAnn(NamedTuple):
    type: str
    name: str
    description: str
    affected_images: int


def _warning_missing_ann_cls(affected_images: int):
    return WarningMissinAnn(
        "warning",
        "Missing expected annotation type for classification domain",
        "Image contains no global label",
        affected_images,
    )


def _warning_missing_ann_det(affected_images: int):
    return WarningMissinAnn(
        "warning",
        "Missing expected annotation type for detection domain",
        "Image contains no bounding boxes",
        affected_images,
    )


def _warning_missing_ann_seg(affected_images: int):
    return WarningMissinAnn(
        "warning",
        "Missing expected annotation type for segmentation domain",
        "Image contains no polygons",
        affected_images,
    )


def warning_missing_ann(domain: Domain, affected_images: int = 0):
    if domain == Domain.CLASSIFICATION:
        return _warning_missing_ann_cls(affected_images)
    if domain == Domain.DETECTION:
        return _warning_missing_ann_det(affected_images)
    if domain in [Domain.SEGMENTATION, Domain.INSTANCE_SEGMENTATION]:
        return _warning_missing_ann_seg(affected_images)
    return None


def _warning_subset_merging():
    return (
        "warning",
        "Subset merging",
        "The images in the imported dataset could already be assigned to "
        "training, validation and testing subsets. However, in the current "
        "version, this information will be lost after the import. The "
        "images will be assigned to new subsets based on the distribution "
        "of labels.",
    )


def warning_local_annotations_lost():
    return (
        "warning",
        "The local annotations will be lost",
        "Please be aware that local annotations, including bounding boxes and polygons, "
        "are not supported in Anomaly projects and will not be imported.",
    )


def warning_dataset_contain_no_labels():
    return (
        "warning",
        "The dataset does not contain any labels",
        "It is possible to use the dataset if you first create a project with labels, then import the dataset into it.",
    )


@dataclass
class DatasetInfo:
    """
    Data class used to specify informations regarding test dataset
    """

    exported_project_type: GetiProjectType = GetiProjectType.UNKNOWN
    fxt_corresponding_project: str = ""
    label_names: set[str] = field(default_factory=set)
    label_names_by_cross_project: dict[GetiProjectType, set[str]] = field(default_factory=dict)
    label_names_by_ann_based_project: dict[GetiProjectType, set[str]] = field(default_factory=dict)
    warnings: dict[Domain, set[tuple]] = field(default_factory=dict)
    keypoint_structure: dict[str, list] = field(default_factory=dict)
    num_items: int = 0


_test_dataset_id__datumaro = {
    "fxt_datumaro_dataset_single_cls_id": DatasetInfo(
        exported_project_type=GetiProjectType.CLASSIFICATION,
        fxt_corresponding_project="fxt_annotated_classification_project",
        label_names={"label0", "label1", "label2"},
        label_names_by_ann_based_project={  # label
            GetiProjectType.CLASSIFICATION: {"label0", "label1", "label2"},
        },
        warnings={
            Domain.CLASSIFICATION: {_warning_missing_ann_cls(1)},
        },
        num_items=4,
    ),
    "fxt_datumaro_dataset_multi_label_id": DatasetInfo(
        exported_project_type=GetiProjectType.CLASSIFICATION,
        fxt_corresponding_project="fxt_annotated_multi_label_project",
        label_names={"label0", "label1"},
        label_names_by_ann_based_project={GetiProjectType.CLASSIFICATION: {"label0", "label1"}},  # label
        warnings={Domain.CLASSIFICATION: {_warning_missing_ann_cls(2)}},
        num_items=4,
    ),
    "fxt_datumaro_dataset_hierarchical_id": DatasetInfo(
        exported_project_type=GetiProjectType.HIERARCHICAL_CLASSIFICATION,
        fxt_corresponding_project="fxt_annotated_hierarchical_classification_project",
        label_names={"non_square", "rectangle", "square", "equilateral", "triangle", "right"},
        label_names_by_ann_based_project={  # label
            GetiProjectType.CLASSIFICATION: {"non_square", "square", "equilateral", "right"},
        },
        num_items=4,
    ),
    "fxt_datumaro_dataset_det_id": DatasetInfo(
        exported_project_type=GetiProjectType.DETECTION,
        fxt_corresponding_project="fxt_annotated_detection_project",
        label_names={"label0", "label1"},
        label_names_by_ann_based_project={GetiProjectType.DETECTION: {"label0", "label1"}},  # bbox
        label_names_by_cross_project={
            GetiProjectType.ROTATED_DETECTION: {"label0", "label1"},
            GetiProjectType.CLASSIFICATION: {"label0", "label1"},
        },
        warnings={
            Domain.DETECTION: {_warning_missing_ann_det(1)},
            Domain.CLASSIFICATION: {_warning_missing_ann_cls(1)},
        },
        num_items=3,
    ),
    "fxt_datumaro_dataset_rotated_detection_id": DatasetInfo(
        exported_project_type=GetiProjectType.ROTATED_DETECTION,
        fxt_corresponding_project="fxt_annotated_rotated_detection_project",
        label_names={"ball", "person"},
        label_names_by_ann_based_project={  # polygon
            GetiProjectType.SEGMENTATION: {"ball", "person"},
            GetiProjectType.INSTANCE_SEGMENTATION: {"ball", "person"},
        },
        label_names_by_cross_project={
            GetiProjectType.DETECTION: {"ball", "person"},
        },
        warnings={
            Domain.DETECTION: {_warning_missing_ann_det(1)},
            Domain.SEGMENTATION: {_warning_missing_ann_seg(1)},
            Domain.INSTANCE_SEGMENTATION: {_warning_missing_ann_seg(1)},
        },
        num_items=4,
    ),
    "fxt_datumaro_dataset_seg_id": DatasetInfo(
        exported_project_type=GetiProjectType.SEGMENTATION,
        fxt_corresponding_project="fxt_annotated_segmentation_project",
        label_names={"label0", "label1"},
        label_names_by_ann_based_project={  # polygon
            GetiProjectType.SEGMENTATION: {"label0", "label1"},
            GetiProjectType.INSTANCE_SEGMENTATION: {"label0", "label1"},
        },
        label_names_by_cross_project={
            GetiProjectType.DETECTION: {"label0", "label1"},
            GetiProjectType.INSTANCE_SEGMENTATION: {"label0", "label1"},
            GetiProjectType.CHAINED_DETECTION_SEGMENTATION: {"label0", "label1", "detection label"},
        },
        warnings={
            Domain.DETECTION: {_warning_missing_ann_det(1)},
            Domain.SEGMENTATION: {_warning_missing_ann_seg(1)},
            Domain.INSTANCE_SEGMENTATION: {_warning_missing_ann_seg(1)},
        },
        num_items=3,
    ),
    "fxt_datumaro_dataset_ins_seg_id": DatasetInfo(
        exported_project_type=GetiProjectType.INSTANCE_SEGMENTATION,
        fxt_corresponding_project="fxt_annotated_instance_segmentation_project",
        label_names={"label0", "label1"},
        label_names_by_ann_based_project={  # polygon
            GetiProjectType.SEGMENTATION: {"label0", "label1"},
            GetiProjectType.INSTANCE_SEGMENTATION: {"label0", "label1"},
        },
        label_names_by_cross_project={
            GetiProjectType.DETECTION: {"label0", "label1"},
            GetiProjectType.SEGMENTATION: {"label0", "label1"},
            GetiProjectType.CHAINED_DETECTION_SEGMENTATION: {"label0", "label1", "detection label"},
        },
        warnings={
            Domain.DETECTION: {_warning_missing_ann_det(1)},
            Domain.SEGMENTATION: {_warning_missing_ann_seg(1)},
            Domain.INSTANCE_SEGMENTATION: {_warning_missing_ann_seg(1)},
        },
        num_items=3,
    ),
    "fxt_datumaro_dataset_anomaly_cls_id": DatasetInfo(
        exported_project_type=GetiProjectType.ANOMALY_CLASSIFICATION,
        fxt_corresponding_project="fxt_annotated_anomaly_cls_project",
        label_names={"Anomalous", "Normal"},
        label_names_by_ann_based_project={  # label
            GetiProjectType.CLASSIFICATION: {"Anomalous", "Normal"},
        },
        label_names_by_cross_project={
            GetiProjectType.CLASSIFICATION: {"Anomalous", "Normal"},
        },
        num_items=6,
    ),
    "fxt_datumaro_dataset_anomaly_det_id": DatasetInfo(
        exported_project_type=GetiProjectType.ANOMALY_DETECTION,
        fxt_corresponding_project="fxt_annotated_anomaly_det_project",
        label_names={"Anomalous", "Normal"},
        label_names_by_ann_based_project={  # label, bbox
            GetiProjectType.CLASSIFICATION: {"Anomalous", "Normal"},
            GetiProjectType.DETECTION: {"Anomalous"},
        },
        label_names_by_cross_project={
            GetiProjectType.CLASSIFICATION: {"Anomalous", "Normal"},
            GetiProjectType.ANOMALY_CLASSIFICATION: {"Anomalous", "Normal"},
        },
        warnings={
            Domain.DETECTION: {_warning_missing_ann_det(4)},
        },
        num_items=6,
    ),
    "fxt_datumaro_dataset_anomaly_seg_id": DatasetInfo(
        exported_project_type=GetiProjectType.ANOMALY_SEGMENTATION,
        fxt_corresponding_project="fxt_annotated_anomaly_seg_project",
        label_names={"Anomalous", "Normal"},
        label_names_by_ann_based_project={  # label, polygon
            GetiProjectType.CLASSIFICATION: {"Anomalous", "Normal"},
            GetiProjectType.SEGMENTATION: {"Anomalous"},
            GetiProjectType.INSTANCE_SEGMENTATION: {"Anomalous"},
        },
        label_names_by_cross_project={
            GetiProjectType.CLASSIFICATION: {"Anomalous", "Normal"},
            GetiProjectType.ANOMALY_CLASSIFICATION: {"Anomalous", "Normal"},
            GetiProjectType.ANOMALY_DETECTION: {"Anomalous", "Normal"},
        },
        warnings={
            Domain.SEGMENTATION: {_warning_missing_ann_seg(4)},
            Domain.INSTANCE_SEGMENTATION: {_warning_missing_ann_seg(4)},
        },
        num_items=6,
    ),
    "fxt_datumaro_dataset_chained_det_cls_id": DatasetInfo(
        exported_project_type=GetiProjectType.CHAINED_DETECTION_CLASSIFICATION,
        fxt_corresponding_project="fxt_annotated_chained_det_cls_project",
        label_names={"det", "a", "b"},
        label_names_by_ann_based_project={  # bbox
            GetiProjectType.DETECTION: {"det"},
        },
        warnings={
            Domain.DETECTION: {_warning_missing_ann_det(2)},
        },
        num_items=4,
    ),
    "fxt_datumaro_dataset_chained_det_seg_id": DatasetInfo(
        exported_project_type=GetiProjectType.CHAINED_DETECTION_SEGMENTATION,
        fxt_corresponding_project="fxt_annotated_chained_det_seg_project",
        label_names={"det", "label0", "label1", "label2"},
        label_names_by_ann_based_project={  # bbox, polygon
            GetiProjectType.DETECTION: {"det"},
            GetiProjectType.SEGMENTATION: {
                "det",  # CVS-126710: bbox should not be ignored for seg and ins_seg.
                "label1",
                "label2",
            },  # 'label0' exists only in the category information.
            GetiProjectType.INSTANCE_SEGMENTATION: {
                "det",  # CVS-126710: bbox should not be ignored for seg and ins_seg.
                "label1",
                "label2",
            },  # 'label0' exists only in the category information.
        },
        label_names_by_cross_project={
            GetiProjectType.DETECTION: {"label0", "label1", "label2"},
            GetiProjectType.ROTATED_DETECTION: {"label0", "label1", "label2"},
            GetiProjectType.SEGMENTATION: {"label0", "label1", "label2"},
            GetiProjectType.INSTANCE_SEGMENTATION: {"label0", "label1", "label2"},
        },
        warnings={
            Domain.DETECTION: {_warning_missing_ann_det(2)},
            Domain.SEGMENTATION: {_warning_missing_ann_seg(2)},
            Domain.INSTANCE_SEGMENTATION: {_warning_missing_ann_seg(2)},
        },
        num_items=4,
    ),
}

VOC_LABELS = {
    "aeroplane",
    "bicycle",
    "boat",
    "bottle",
    "car",
    "cat",
    "chair",
    "cow",
    "diningtable",
    "dog",
    "hand",
    "head",
    "person",
    "pottedplant",
    "sheep",
    "sofa",
    "train",
    "tvmonitor",
}
ROBO_LABELS = {"Platelets", "RBC", "WBC"}

_test_dataset_id__public = {
    "fxt_coco_dataset_id": DatasetInfo(
        label_names_by_ann_based_project={  # bbox
            GetiProjectType.DETECTION: {"car", "person"},
        },
        num_items=11,
    ),
    "fxt_voc_dataset_id": DatasetInfo(
        # bbox
        label_names_by_ann_based_project={
            GetiProjectType.DETECTION: VOC_LABELS,
        },
        warnings={Domain.NULL: {_warning_subset_merging()}},
        num_items=30,
    ),
    "fxt_roboflow_coco_dataset_id": DatasetInfo(
        label_names_by_ann_based_project={  # bbox
            GetiProjectType.DETECTION: ROBO_LABELS,
        },
        warnings={Domain.NULL: {_warning_subset_merging()}},
        num_items=30,
    ),
    "fxt_roboflow_voc_dataset_id": DatasetInfo(
        label_names_by_ann_based_project={  # bbox
            GetiProjectType.DETECTION: ROBO_LABELS,
        },
        warnings={Domain.NULL: {_warning_subset_merging()}},
        num_items=30,
    ),
    "fxt_roboflow_yolo_dataset_id": DatasetInfo(
        label_names_by_ann_based_project={  # bbox
            GetiProjectType.DETECTION: ROBO_LABELS,
        },
        warnings={Domain.NULL: {_warning_subset_merging()}},
        num_items=30,
    ),
}

_test_dataset_definition = {
    "fxt_global_labels_dataset_definition": DatasetInfo(
        label_names_by_ann_based_project={  # label
            GetiProjectType.CLASSIFICATION: {"cat", "dog", "truck"},
        },
        num_items=3,
    ),
    "fxt_bbox_dataset_definition": DatasetInfo(
        label_names_by_ann_based_project={  # bbox
            GetiProjectType.DETECTION: {"bus", "cat", "dog", "truck"},
        },
        num_items=2,
    ),
    "fxt_polygon_dataset_definition": DatasetInfo(
        label_names_by_ann_based_project={  # polygon
            GetiProjectType.SEGMENTATION: {"bus", "cat", "truck"},
            GetiProjectType.INSTANCE_SEGMENTATION: {"bus", "cat", "truck"},
        },
        num_items=2,
    ),
    "fxt_polygon_and_ellipse_dataset_definition": DatasetInfo(
        label_names_by_ann_based_project={  # polygon, ellipse
            GetiProjectType.SEGMENTATION: {"bus", "cat", "dog", "truck"},
            GetiProjectType.INSTANCE_SEGMENTATION: {"bus", "cat", "dog", "truck"},
        },
        num_items=3,
    ),
    "fxt_bbox_polygon_dataset_definition": DatasetInfo(
        label_names_by_ann_based_project={  # bbox, polygon
            GetiProjectType.DETECTION: {"dog", "truck"},
            # CVS-126710: bbox should not be ignored for seg and ins_seg.
            GetiProjectType.SEGMENTATION: {"dog", "truck"},
            GetiProjectType.INSTANCE_SEGMENTATION: {"dog", "truck"},
        },
        num_items=1,
    ),
    "fxt_mask_voc_dataset_definition": DatasetInfo(
        label_names_by_ann_based_project={  # mask
            GetiProjectType.SEGMENTATION: {"bus", "dog", "truck"},
            GetiProjectType.INSTANCE_SEGMENTATION: {"bus", "dog", "truck"},
        },
        num_items=3,
    ),
}


@pytest.fixture(scope="function", params=_test_dataset_id__datumaro.keys())
def fxt_dataset_id__datumaro(request: pytest.FixtureRequest):
    """Parametrize dataset_id of datumaro datset"""
    return request.getfixturevalue(request.param), _test_dataset_id__datumaro[request.param]


@pytest.fixture(scope="function", params=_test_dataset_id__public.keys())
def fxt_dataset_id__public(request: pytest.FixtureRequest):
    """Parametrize dataset_id of public datset"""
    return request.getfixturevalue(request.param), _test_dataset_id__public[request.param]


@pytest.fixture(scope="function", params=_test_dataset_definition.keys())
def fxt_dataset_definition(request: pytest.FixtureRequest):
    """Parametrize dataset definitions for import test"""
    return request.getfixturevalue(request.param), _test_dataset_definition[request.param]


@pytest.fixture(
    scope="function", params=[info.fxt_corresponding_project for info in _test_dataset_id__datumaro.values()]
)
def fxt_project(request: pytest.FixtureRequest):
    return request.param, request.getfixturevalue(request.param)


def get_dataset_info(fxt_dataset_id_str: str) -> DatasetInfo:
    # temporal until keypoint detection is fully supported
    if fxt_dataset_id_str == "fxt_dataumaro_dataset_keypoint_id":
        if FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_KEYPOINT_DETECTION):
            keypoint_labels = {
                "nose",  # 1
                "left_eye",  # 2
                "right_eye",  # 3
                "left_ear",  # 4
                "right_ear",  # 5
                "left_shoulder",  # 6
                "right_shoulder",  # 7
                "left_elbow",  # 8
                "right_elbow",  # 9
                "left_wrist",  # 10
                "right_wrist",  # 11
                "left_hip",  # 12
                "right_hip",  # 13
                "left_knee",  # 14
                "right_knee",  # 15
                "left_ankle",  # 16
                "right_ankle",  # 17
            }
            keypoint_structure = {
                "edges": [
                    {"nodes": ["left_shoulder", "left_hip"]},  # [6,12]
                    {"nodes": ["left_ear", "left_shoulder"]},  # [4,6]
                    {"nodes": ["left_hip", "right_hip"]},  # [12,13]
                    {"nodes": ["right_ear", "right_shoulder"]},  # [5,7]
                    {"nodes": ["right_ankle", "right_knee"]},  # [17,15]
                    {"nodes": ["right_elbow", "right_wrist"]},  # [9,11]
                    {"nodes": ["nose", "right_eye"]},  # [1,3]
                    {"nodes": ["left_shoulder", "left_elbow"]},  # [6,8]
                    {"nodes": ["right_shoulder", "right_hip"]},  # [7,13]
                    {"nodes": ["left_knee", "left_hip"]},  # [14,12]
                    {"nodes": ["left_eye", "left_ear"]},  # [2,4]
                    {"nodes": ["nose", "left_eye"]},  # [1,2]
                    {"nodes": ["right_knee", "right_hip"]},  # [15,13]
                    {"nodes": ["right_shoulder", "right_elbow"]},  # [7,9]
                    {"nodes": ["left_shoulder", "right_shoulder"]},  # [6,7]
                    {"nodes": ["right_eye", "right_ear"]},  # [3,5]
                    {"nodes": ["left_elbow", "left_wrist"]},  # [8,10]
                    {"nodes": ["left_eye", "right_eye"]},  # [2,3]
                    {"nodes": ["left_ankle", "left_knee"]},  # [16,14]
                ],
                "positions": [],  # TODO CVS-156570
            }
            return DatasetInfo(
                exported_project_type=GetiProjectType.KEYPOINT_DETECTION,
                label_names=keypoint_labels,
                label_names_by_ann_based_project={  # bbox, points
                    GetiProjectType.DETECTION: {"person"},
                    GetiProjectType.KEYPOINT_DETECTION: keypoint_labels,
                },
                keypoint_structure=keypoint_structure,
                num_items=4,
            )
        return DatasetInfo(
            exported_project_type=GetiProjectType.UNKNOWN,
            label_names=set(),  # empty: it should be handled as if it's not exported from Geti.
            label_names_by_ann_based_project={  # bbox
                GetiProjectType.DETECTION: {"person"},
            },
            num_items=4,
        )

    dataset_info = _test_dataset_id__public.get(fxt_dataset_id_str, None)

    if dataset_info is None:
        dataset_info = _test_dataset_id__datumaro.get(fxt_dataset_id_str, None)

    if dataset_info is None:
        raise ValueError(f"The dataset {fxt_dataset_id_str} is not found.")

    return dataset_info
