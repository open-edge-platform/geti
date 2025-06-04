# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

import glob
import logging
import operator
from collections.abc import Generator, Iterable
from functools import reduce
from pathlib import Path
from typing import Any

import yaml

from platform_utils.calculate_resource_multiplier import k8s_cpu_to_millicpus

logger = logging.getLogger(__name__)


def k8s_memory_to_mibibytes(k8s_memory: str) -> int:
    """convert memory return from k8s to mibibytes"""
    memory_suffixes = {
        "Pi": 1024**5,
        "Ti": 1024**4,
        "Gi": 1024**3,
        "Mi": 1024**2,
        "Ki": 1024,
        "P": 1000**5,
        "T": 1000**4,
        "G": 1000**3,
        "M": 1000**2,
        "K": 1000,
        "k": 1000,
    }

    for memory_suffix, multiplier in memory_suffixes.items():
        if memory_suffix in k8s_memory:
            # compute bytes and divide by 1024**2 to return mibibytes
            return int(float(k8s_memory.strip(memory_suffix)) * multiplier // (1024**2))
    raise ValueError(f"Invalid k8s memory value: {k8s_memory}")


def scale_cpu_resource(cpu_resource: str, resource_multiplier: float, minimal_millicpus: int = 100) -> str:  # noqa: D103
    scaled_millicpus = max(
        int(k8s_cpu_to_millicpus(cpu_resource) * resource_multiplier),
        min(k8s_cpu_to_millicpus(cpu_resource), minimal_millicpus),
    )
    return f"{scaled_millicpus}m"


def scale_memory_resource(memory_resource: str, resource_multiplier: float, minimal_mibibytes: int = 128) -> str:  # noqa: D103
    scaled_mibibytes = max(
        int(k8s_memory_to_mibibytes(memory_resource) * resource_multiplier),
        min(k8s_memory_to_mibibytes(memory_resource), minimal_mibibytes),
    )
    return f"{scaled_mibibytes}Mi"


def find_nested_resources(  # noqa: D103
    values_yaml: dict, dict_key_path: str | None = None
) -> Generator[tuple[str, dict], None, None]:
    if not dict_key_path:
        dict_key_path = ""
    for k, v in values_yaml.items():
        if k == "resources" and v is not None:
            # strip leading dot
            yield join_dict_key_path([dict_key_path, k]).lstrip("."), v
        elif isinstance(v, dict):
            yield from find_nested_resources(v, dict_key_path=join_dict_key_path([dict_key_path, k]))
    return


def decode_dict_key_path(dictionary: dict, dict_key_path: str) -> dict:  # noqa: D103
    return reduce(operator.getitem, dict_key_path.split("."), dictionary)


def save_under_dict_key_path(dictionary: dict, dict_key_path: str, value: Any) -> None:  # noqa: D103
    logger.debug(f"Saving {value} under {dict_key_path} path")
    d = dictionary
    for key in dict_key_path.split(".")[:-1]:
        if not d.get(key):
            d[key] = {}
        d = d[key]
    d[dict_key_path.split(".")[-1]] = value


def join_dict_key_path(paths: Iterable[str | None]) -> str:  # noqa: D103
    return ".".join(p for p in paths if p)


def scale_chart_resources(  # noqa: C901, PLR0912
    available_master_resources: dict, charts_directory: str, resource_multiplier: float, values_file_output_path: str
) -> None:
    """
    Method used to scale chart resources based on multiplier.
    Generate proper values file containing those resources.
    """
    total_allocatable_memory = k8s_memory_to_mibibytes(available_master_resources["memory"]) / 1024
    # Some resources might need conditional resource allocation (like resource below)
    # See CVS-67452 for more details.
    logger.debug("Starting resource scaling")
    whitelisted_charts: list[Any] = []
    whitelisted_chart_names = list(map(lambda resource: resource["name"], whitelisted_charts))  # noqa: C417
    values_yamls: list[dict] = []

    yaml_find_path = f"{charts_directory}/**/values.yaml"
    logger.debug(f"Searching for yaml files using specified path: {yaml_find_path}")
    yaml_files_to_scale = glob.glob(yaml_find_path, recursive=True)
    logger.debug(f"Found {len(yaml_files_to_scale)} values.yaml files, corresponding to {yaml_files_to_scale}")
    for values_yaml_file_name in yaml_files_to_scale:
        with open(values_yaml_file_name) as f:
            values = yaml.safe_load(f)
            if values:
                values["_chart_name"] = Path(values_yaml_file_name).parts[-2]
                values_yamls.append(values)

    calculated_resource_yaml: dict = {}
    for values_yaml in values_yamls:
        logger.debug(f"Handling {values_yaml['_chart_name']} resources")
        resource_definitions = list(find_nested_resources(values_yaml))
        chart_name = values_yaml["_chart_name"]

        for resource_dict_key_path, resource_def in resource_definitions:
            cpu_request = resource_def.get("requests", {}).get("cpu")
            cpu_limit = resource_def.get("limits", {}).get("cpu")
            for resource_spec_type, cpu in [("requests", cpu_request), ("limits", cpu_limit)]:
                if cpu:
                    scaled_cpu = scale_cpu_resource(cpu_resource=cpu, resource_multiplier=resource_multiplier)
                    logger.debug(
                        f"Scaled CPU {resource_spec_type} for {chart_name}"
                        f"/{resource_dict_key_path} from {cpu} to {scaled_cpu}"
                    )
                    dict_key_path = join_dict_key_path([chart_name, resource_dict_key_path, resource_spec_type, "cpu"])
                    save_under_dict_key_path(calculated_resource_yaml, dict_key_path, scaled_cpu)

            memory_request = resource_def.get("requests", {}).get("memory")
            memory_limit = resource_def.get("limits", {}).get("memory")
            for resource_spec_type, memory in [("requests", memory_request), ("limits", memory_limit)]:
                if memory:
                    scaled_memory = None
                    if chart_name in whitelisted_chart_names:  # CVS-67452
                        for whitelisted_resource in whitelisted_charts:
                            if (
                                chart_name == whitelisted_resource["name"]
                                and total_allocatable_memory > whitelisted_resource["memory_threshold"]
                            ):
                                logger.debug(f"Scaling whitelisted resource {chart_name}")
                                scaled_memory = scale_memory_resource(
                                    memory_resource=whitelisted_resource["memory_resource"],
                                    resource_multiplier=whitelisted_resource["resource_multiplier"],
                                )
                            else:
                                scaled_memory = scale_memory_resource(
                                    memory_resource=memory, resource_multiplier=resource_multiplier
                                )

                    if not scaled_memory:
                        scaled_memory = scale_memory_resource(
                            memory_resource=memory, resource_multiplier=resource_multiplier
                        )
                    logger.debug(
                        f"Scaled Memory {resource_spec_type} for {chart_name}/"
                        f"{resource_dict_key_path} from {memory} to {scaled_memory}"
                    )
                    dict_key_path = join_dict_key_path(
                        [chart_name, resource_dict_key_path, resource_spec_type, "memory"]
                    )
                    save_under_dict_key_path(calculated_resource_yaml, dict_key_path, scaled_memory)

    with open(values_file_output_path, mode="w") as output_file:
        yaml.safe_dump(calculated_resource_yaml, output_file)
