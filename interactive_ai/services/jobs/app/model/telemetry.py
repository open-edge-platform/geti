# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Telemetry module
"""

from dataclasses import dataclass


@dataclass
class Telemetry:
    """
    Telemetry

    context                 opentelemetry context
    """

    context: str = ""
