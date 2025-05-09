# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import hiyapyco
from importlib import resources

from . import manifests
from .model_manifest import ModelManifest


def parse_manifest(*manifest_sources, relative: bool = True) -> ModelManifest:
    """
    Parse model manifest YAML files and merge them into an Algorithm object.

    This function takes multiple manifest source paths, merges them using hierarchical
    YAML configuration, and converts the merged result into a structured Algorithm model.

    :param manifest_sources: YAML manifest files.
        Files are merged in order, with later files overriding values from earlier files.
    :param relative: If True, the paths are treated as relative to the package where the manifest files are stored.
        If False, they are treated as absolute paths.
    :return: A populated Algorithm object containing the parsed manifest data.
    """
    if relative:
        manifest_sources = [resources.files(manifests).joinpath(path) for path in manifest_sources]
    yaml_manifest = hiyapyco.load(
        *manifest_sources, method=hiyapyco.METHOD_MERGE, interpolate=True, failonmissingfiles=True
    )
    return ModelManifest(**yaml_manifest)
