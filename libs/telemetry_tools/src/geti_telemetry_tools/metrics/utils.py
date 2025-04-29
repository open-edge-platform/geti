# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Utils for Geti telemetry metrics"""

import logging
import os
from collections.abc import Callable
from typing import Protocol

from opentelemetry.metrics import CallbackOptions, Observation

logger = logging.getLogger(__name__)


def convert_bytes(num_bytes: int, unit: str) -> float:
    """
    Convert the given number of bytes to the given bytes-multiple unit

    :param num_bytes: Number of bytes
    :param unit: Bytes-multiple unit (e.g. MB)
    :return: Number of bytes expressed in the requested unit
    """
    supported_units = ("B", "KB", "MB", "GB", "TB")
    unit = unit.strip().upper()
    try:
        conversion_factor = 1024 ** supported_units.index(unit)
    except ValueError:
        logger.exception(
            "Unsupported unit `%s` for bytes conversion. Defaulting to bytes.",
            unit,
        )
        conversion_factor = 1
    return num_bytes / conversion_factor


def convert_pixels(num_pixels: int, unit: str) -> float:
    """
    Convert the given number of pixels to the given pixel-multiple unit

    :param num_pixels: Number of pixels
    :param unit: Pixel-multiple unit (e.g. MP)
    :return: Number of pixels expressed in the requested unit
    """
    supported_units = ("P", "KP", "MP", "GP")
    unit = unit.strip().upper()
    try:
        conversion_factor = 1000 ** supported_units.index(unit)
    except ValueError:
        logger.exception(
            "Unsupported unit `%s` for pixel conversion. Defaulting to pixels.",
            unit,
        )
        conversion_factor = 1
    return num_pixels / conversion_factor


class ElectionManager(Protocol):
    def stand_for_election(self, subject: str, resource: str, validity_in_seconds: int) -> bool:
        pass


def if_elected_publisher_for_metric(
    metric_name: str, validity_in_seconds: int, election_manager_cls: type[ElectionManager]
) -> Callable[[Callable[[CallbackOptions], list[Observation]]], Callable[[CallbackOptions], list[Observation]]]:
    """
    Decorate async metric callback function with a leadership election protocol

    The callback will only report the metric if the pod is selected as the leader among all pods within a replica set.
    """

    def inside_decorator(
        fn: Callable[[CallbackOptions], list[Observation]],
    ) -> Callable[[CallbackOptions], list[Observation]]:
        pod_id = os.environ.get("HOSTNAME", None)
        if not pod_id:
            logger.warning("Could not determine the pod id, setting the pod id to 'pod_id_unknown'")
            pod_id = "pod_id_unknown"

        def decorated_fn(callback_options: CallbackOptions) -> list[Observation]:
            is_elected_publisher = election_manager_cls().stand_for_election(
                subject=pod_id,
                resource=metric_name,
                validity_in_seconds=validity_in_seconds,
            )

            if not is_elected_publisher:
                return []
            return fn(callback_options)

        return decorated_fn

    return inside_decorator
