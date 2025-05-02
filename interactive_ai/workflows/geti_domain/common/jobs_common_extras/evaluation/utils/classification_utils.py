# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from iai_core.entities.label_schema import LabelSchema


def get_cls_inferencer_configuration(label_schema: LabelSchema) -> dict:
    """
    Get classification inferencer configuration from the label schema.

    :param label_schema: LabelSchema to get the configuration from
    :return: dict representing the configuration for the classification inferencer
    """
    multilabel = len(label_schema.get_groups(False)) > 1 and len(label_schema.get_groups(False)) == len(
        label_schema.get_labels(include_empty=False)
    )
    hierarchical = not multilabel and len(label_schema.get_groups(False)) > 1
    return {
        "multilabel": multilabel,
        "hierarchical": hierarchical,
    }
