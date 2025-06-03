# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module implements label-related mappers for conversion between SC and Datumaro"""

from dataclasses import dataclass

import datumaro as dm
from datumaro.components.annotation import GroupType as DmGroupType
from geti_types import ID
from iai_core.entities.color import Color
from iai_core.entities.keypoint_structure import KeypointStructure
from iai_core.entities.label import Label
from iai_core.entities.label_schema import LabelGroupType, LabelSchema

from jobs_common_extras.datumaro_conversion.mappers.datetime_mapper import DatetimeMapper
from jobs_common_extras.datumaro_conversion.mappers.id_mapper import IDMapper


class LabelGroupsMapper:
    """Mapping LabelGroup between Datumaro and SC"""

    forward_mapping = {
        LabelGroupType.EXCLUSIVE: DmGroupType.EXCLUSIVE,
        LabelGroupType.EMPTY_LABEL: DmGroupType.RESTRICTED,
    }
    backward_mapping = {v: k for k, v in forward_mapping.items()}

    @classmethod
    def update(
        cls,
        label_categories: dm.LabelCategories,
        label_schema: LabelSchema,
        include_empty: bool,
    ) -> dm.LabelCategories:
        """Update SC LabelGroups info to Datumaro LabelCategories"""
        label_groups = label_schema.get_groups(include_empty)
        for label_group in label_groups:
            dm_group_name = label_group.name
            dm_group_type = cls.forward_mapping[label_group.group_type]
            dm_child_names = [sc_label.name for sc_label in label_group.labels]

            # When a group contains at least one valid label,
            # the group is necessary to be exported
            label_categories.add_label_group(
                name=dm_group_name,
                labels=dm_child_names,
                group_type=dm_group_type,
            )

        return label_categories


class LabelTreeMapper:
    """Mapping LabelTree between Datumaro and SC"""

    empty_key = "__empty__"
    anomalous_key = "__anomalous__"
    label_name_key = "__name__"
    hotkey_key = "__hotkey__"
    color_key = "__color__"

    @classmethod
    def forward(  # noqa: C901
        cls, label_schema: LabelSchema, include_empty: bool = False, keypoint_structure: KeypointStructure | None = None
    ) -> tuple[dm.LabelCategories, dm.PointsCategories]:
        """Convert SC label list and their tree info to Datumaro LabelCategories"""
        # labels = label_schema.get_labels(include_empty=include_empty)
        labels = []
        for group in label_schema._groups:
            for label in group.labels:
                if (include_empty or not label.is_empty) and label.id_ not in label_schema.deleted_label_ids:
                    labels.append(label)

        parent_map: dict[Label, Label] = {}
        for label in labels:
            parent = label_schema.get_parent(label)
            if parent is not None:
                parent_map[label] = parent

        label_cat = dm.LabelCategories()
        point_cat = dm.PointsCategories()
        joints = []
        positions = []
        if keypoint_structure:
            label_id_to_idx = {label.id_: idx for idx, label in enumerate(labels)}
            for edge in keypoint_structure._edges:
                node_1 = label_id_to_idx[edge.node_1]
                node_2 = label_id_to_idx[edge.node_2]
                joints.append([node_1, node_2])
            for position in keypoint_structure._positions:
                positions.extend([position.x, position.y])
        point_cat.add(label_id=0, labels=[str(label.id_) for label in labels], joints=joints, positions=positions)

        for label in labels:
            parent = parent_map.get(label)

            attributes = set()

            attributes.add(cls.label_name_key + label.name)
            attributes.add(cls.hotkey_key + label.hotkey)
            attributes.add(cls.color_key + label.color.hex_str)
            attributes.add(label.domain.name)
            if label.is_empty:
                attributes.add(cls.empty_key)
            if label.is_anomalous:
                attributes.add(cls.anomalous_key)

            label_cat.add(
                name=str(label.id_),
                parent=str(parent.id_) if parent else None,
                attributes=attributes,
            )

        return label_cat, point_cat

    @classmethod
    def get_label_name(cls, cat: dm.LabelCategories.Category) -> str:
        for attr in cat.attributes:
            if attr.startswith(cls.label_name_key):
                return attr.removeprefix(cls.label_name_key)

        return ""


@dataclass
class DmLabelSchemaInfo:
    """Data class to construct LabelSchema"""

    label_schema_id: ID
    label_cat: dm.LabelCategories
    mask_cat: dm.MaskCategories | None
    point_cat: dm.PointsCategories | None


class LabelSchemaMapper:
    """Mapping LabelSchema between Datumaro and SC"""

    @staticmethod
    def forward(
        label_schema: LabelSchema, include_empty: bool = False, keypoint_structure: KeypointStructure | None = None
    ) -> DmLabelSchemaInfo:
        """Convert SC LabelSchema to DmLabelSchemaInfo"""

        label_schema_id = label_schema.id_
        label_cat, point_cat = LabelTreeMapper.forward(label_schema, include_empty, keypoint_structure)
        label_cat = LabelGroupsMapper.update(label_cat, label_schema, include_empty)

        mask_cat = dm.MaskCategories(
            colormap={idx: label.color.rgb_tuple for idx, label in enumerate(label_schema.get_labels(include_empty))}
        )

        return DmLabelSchemaInfo(
            label_schema_id=label_schema_id,
            label_cat=label_cat,
            mask_cat=mask_cat,
            point_cat=point_cat,
        )


class ColorMapper:
    """This class maps a `Color` entity to a serialized dictionary, and vice versa."""

    @staticmethod
    def forward(instance: Color) -> dict:
        """Serializes to dict."""

        return {
            "red": instance.red,
            "green": instance.green,
            "blue": instance.blue,
            "alpha": instance.alpha,
        }


class LabelMapper:
    """This class maps a `Label` entity to a serialized dictionary, and vice versa."""

    @staticmethod
    def forward(
        instance: Label,
    ) -> dict:
        """Serializes to dict."""

        return {
            "_id": IDMapper().forward(instance.id_),
            "name": instance.name,
            "color": ColorMapper().forward(instance.color),
            "hotkey": instance.hotkey,
            "domain": str(instance.domain),
            "creation_date": DatetimeMapper.forward(instance.creation_date),
            "is_empty": instance.is_empty,
            "is_anomalous": instance.is_anomalous,
        }
