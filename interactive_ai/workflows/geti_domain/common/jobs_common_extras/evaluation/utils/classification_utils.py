# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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

from sc_sdk.entities.label_schema import LabelSchema


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
