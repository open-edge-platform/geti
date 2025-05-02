# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from iai_core.entities.color import Color
from iai_core.entities.label import Domain, Label
from iai_core.entities.label_schema import LabelSchema
from iai_core.repos import LabelRepo

COLOR = "color"
DOMAIN = "domain"
EXCLUDE_LABELS = "exclude_labels"
GROUP = "group"
HOTKEY = "hotkey"
ID_ = "id"
IS_EMPTY = "is_empty"
LEVEL = "level"
NAME = "name"
PARENT = "parent"
PARENT_ID = "parent_id"
SHOW_TO_USER = "show_to_user"
TASK_ID = "task_id"
IS_ANOMALOUS = "is_anomalous"


class LabelRESTViews:
    @staticmethod
    def label_to_rest(label: Label, label_schema: LabelSchema) -> dict:
        """
        Converts label to dict according to rest contract. The rest representation of a
        label includes label group and label parent, we need the label's full label
        schema to retrieve the group and parent.

        :param label: label object to convert
        :param label_schema: full (non-view) label schema containing label
        :return: label dictionary
        """
        label_group = label_schema.get_group_containing_label(label)
        parent = label_schema.get_parent(label)

        return {
            ID_: str(label.id_),
            NAME: label.name,
            IS_ANOMALOUS: label.is_anomalous,
            COLOR: label.color.hex_str,
            HOTKEY: label.hotkey,
            IS_EMPTY: label.is_empty,
            GROUP: label_group.name if label_group is not None else "",
            PARENT_ID: None if parent is None else str(parent.id_),
        }

    @staticmethod
    def label_from_rest(label_dict: dict, domain: Domain) -> Label:
        """
        Convert label dictionary to label object. The label domain is a label attribute
        not present in the label rest representation, rather it is deduced from the
        task_type and thus needs to be supplied as an additional parameter here.

        :param label_dict: dict of rest representation of label
        :param domain: label domain
        :return: label object
        """
        name = label_dict[NAME]
        color_str = label_dict.get(COLOR)
        color = Color.from_hex_str(color_str) if color_str is not None else None
        hotkey = label_dict.get(HOTKEY, "")
        is_empty = label_dict.get(IS_EMPTY, False)
        id_ = label_dict.get(ID_)
        ephemeral = False
        if id_ is None:
            id_ = LabelRepo.generate_id()
            ephemeral = True
        return Label(
            name=name,
            domain=domain,
            color=color,
            hotkey=hotkey,
            is_empty=is_empty,
            id_=id_,
            ephemeral=ephemeral,
        )
