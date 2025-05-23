# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module implements a mapper for conversion between Geti AnnotationScene and Datumaro annotations"""

from itertools import chain

import datumaro as dm
from geti_types import ID
from iai_core.entities.annotation import Annotation, AnnotationScene
from iai_core.entities.label import Label
from iai_core.entities.label_schema import LabelSchema
from iai_core.entities.shapes import Ellipse, Keypoint, Polygon, Rectangle


class LabelMap:
    """Map Datumaro label index (integer) to Geti Label"""

    def __init__(
        self,
        label_schema: LabelSchema,
        label_categories: dm.LabelCategories,
        point_categories: dm.PointsCategories,
        include_empty: bool = True,
    ) -> None:
        self.include_empty = include_empty
        self.sc_label_lookup = {
            sc_label.id_: sc_label for sc_label in label_schema.get_labels(include_empty=include_empty)
        }
        self.label_map = [self.sc_label_lookup[ID(label.name)] for label in label_categories]
        self.points_label_map = [self.sc_label_lookup[ID(label)] for label in point_categories.items[0].labels]
        self.label_categories = label_categories
        self.point_categories = point_categories

    def __getitem__(self, key: int) -> Label:
        return self.label_map[key]

    def get_dm_label_by_sc_label_id(self, label_id: ID) -> int | None:
        """Get Datumaro label id (int) from the Geti label id (ID). If cannot find, return None."""
        dm_label, _ = self.label_categories.find(str(label_id))
        return dm_label


class AnnotationSceneMapper:
    """Map Geti AnnotationScene to Datumaro annotations"""

    ATTR_KEY_MULTI_LABELED = "multi_label_ids"
    ATTR_KEYPOINT_LABELS = "keypoint_label_ids"

    def __init__(self, label_map: LabelMap) -> None:
        self.label_map = label_map

    def forward(self, instance: AnnotationScene) -> list[dm.Annotation]:
        """
        Convert annotations from Geti to Datumaro.

        Note that for task-chain projects, labels and annotations that belong to another task are removed here.
        Keypoint annotations are handled separately due to the n:1 relation.

        :param instance: The Geti annotation scene
        :return: A list of Datumaro annotations
        """
        dm_anns = []
        sc_keypoint_anns = []
        for sc_ann in instance.annotations:
            if not isinstance(sc_ann.shape, Keypoint):
                # For task-chain, annotations that only contain labels from other tasks will return None and are removed
                dm_ann = self._forward_ann(annotation=sc_ann, width=instance.media_width, height=instance.media_height)
                if dm_ann:
                    dm_anns.append(dm_ann)
            else:
                sc_keypoint_anns.append(sc_ann)

        if sc_keypoint_anns:
            dm_anns.append(
                self._forward_keypoint_ann(
                    annotations=sc_keypoint_anns,
                    width=instance.media_width,
                    height=instance.media_height,
                )
            )

        return dm_anns

    def _forward_ann(self, annotation: Annotation, width: int, height: int) -> dm.Annotation | None:
        """
        Converts Geti -> Datumaro
            - Polygon -> dm.Polygon
            - Full Rectangle -> dm.Label
            - Rectangle -> dm.Bbox
            - Ellipse -> dm.Ellipse

        The Datumaro's label is the first label in the Geti annotation.
        If it is a multi-labeled annotation, the labels are also stored in the dm.Shape's attributes field.
        For task chain projects, we only forward labels that are within the current task, removing labels from other
        tasks. If an annotation contains no labels for the current task at all, we return None.

        :param annotation: The annotation to convert
        :param width: Width of the image
        :param height: Height of the image
        :return: The Datumaro annotation, if it contains labels for the current task, else None
        :raises NotImplementedError: if the shape is not supported
        """
        dm_label_ids = [
            dm_label_id
            for label in annotation.get_labels(include_empty=self.label_map.include_empty)
            if (dm_label_id := self.label_map.get_dm_label_by_sc_label_id(label.id_)) is not None
        ]

        # For task-chain projects, labels from other tasks are removed. If none remain, then the annotation (shape)
        # belongs to another task
        if len(dm_label_ids) == 0:
            return None

        primary_label_id = dm_label_ids[0]
        attributes = {self.ATTR_KEY_MULTI_LABELED: dm_label_ids} if len(dm_label_ids) > 1 else None

        shape = annotation.shape
        if isinstance(shape, Polygon):
            return dm.Polygon(
                points=list(chain.from_iterable((p.x * width, p.y * height) for p in shape.points)),
                label=primary_label_id,
                attributes=attributes,
            )
        if isinstance(shape, Rectangle) and Rectangle.is_full_box(shape):
            return dm.Label(
                label=primary_label_id,
                attributes=attributes,
            )
        if isinstance(shape, Rectangle):
            return dm.Bbox(
                x=shape.x1 * width,
                y=shape.y1 * height,
                w=shape.width * width,
                h=shape.height * height,
                label=primary_label_id,
                attributes=attributes,
            )
        if isinstance(shape, Ellipse):
            return dm.Ellipse(
                x1=shape.x1 * width,
                y1=shape.y1 * height,
                x2=(shape.x1 + shape.width) * width,
                y2=(shape.y1 + shape.height) * height,
                label=primary_label_id,
                attributes=attributes,
            )
        raise NotImplementedError(f"Unsupported conversion to DM of {shape.__class__.__name__} annotation.")

    def _forward_keypoint_ann(self, annotations: list[Annotation], width: int, height: int) -> dm.Annotation:
        """
        Converts only the keypoint annotation to Datumaro format.

        On the Geti side, each individual keypoint is its own annotation with its own label.
        Whereas on the DM side, it is a single annotation containing a list of points, all represented by a label.
        The relation is n:1.
        The (x,y) of the keypoint annotations are converted to dm.Points(points=[x1, y1, x2, y2, ...], )

        Geti_annotations
            - annotation_a
                - shape: Keypoint
                - label: label_a
                - x: x_a
                - y: y_a
                - is_visible: True
            - annotation_b
                - shape: Keypoint
                - label: label_b
                - x: x_b
                - y: y_b
                - is_visible: True
            - annotation_c
                - shape: Keypoint
                - label: label_c
                - x: x_c
                - y: y_c
                - is_visible: False

        DM_annotations
            - annotation
                - shape: dm.Points
                - points: [x_a, y_a, x_b, y_b, x_c, y_c]
                - visibility: [visible, visible, hidden]
                - label: label_a                            <-- Note


        Note: The DM annotation expects a single label to represent its points. This is not present on the Geti side,
        but an example of this would be: label "Person" representing keypoints [head, neck, back, arm_l, arm_r, ...].
        The first Geti label (eg: head) is used for the DM annotation.

        :param annotations: List of keypoint annotations
        :param width: Width of the image
        :param height: Height of the image
        :return: The DM annotation
        """
        points = []
        visibilities = []
        attributes: dict[str, list] = {self.ATTR_KEYPOINT_LABELS: []}

        for ann in annotations:
            shape = ann.shape
            if isinstance(shape, Keypoint):
                points.extend([shape.x * width, shape.y * height])
                visibilities.append(dm.Points.Visibility.visible if shape.is_visible else dm.Points.Visibility.hidden)  # type: ignore
                label_id = self.label_map.get_dm_label_by_sc_label_id(ann.get_labels()[0].id_)
                attributes[self.ATTR_KEYPOINT_LABELS].append(label_id)
            else:
                raise ValueError(f"Unexpected shape of type {ann.shape.type}")

        return dm.Points(points=points, visibility=visibilities, label=0, attributes=attributes)
