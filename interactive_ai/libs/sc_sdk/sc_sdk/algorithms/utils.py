# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os

import hiyapyco

from sc_sdk.algorithms.models.algorithm import Algorithm

# base manifest folder: interactive_ai/supported_models/manifests
MODEL_MANIFEST_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../supported_models/manifests"))


def parse_manifest(*manifest_sources) -> Algorithm:
    """
    Parse model manifest YAML files and merge them into an Algorithm object.

    This function takes multiple manifest source paths, merges them using hierarchical
    YAML configuration, and converts the merged result into a structured Algorithm model.

    :param manifest_sources: YAML manifest files.
        Files are merged in order, with later files overriding values from earlier files.
    :return: A populated Algorithm object containing the parsed manifest data.
    """
    yaml_manifest = hiyapyco.load(
        *manifest_sources, method=hiyapyco.METHOD_MERGE, interpolate=True, failonmissingfiles=True
    )
    return Algorithm(**yaml_manifest)
