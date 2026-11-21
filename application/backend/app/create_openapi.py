# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""This script generates an OpenAPI JSON file for the FastAPI application."""

import json
from pathlib import Path

from main import create_app


def create_openapi(target_path: str) -> None:
    """Entry point for creating the OpenAPI specification"""
    # Ensure target directory exists
    output_path = Path(target_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as file:
        json.dump(obj=create_app().openapi(), fp=file, indent=2)
