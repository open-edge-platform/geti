#
# Copyright (C) 2020-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

import pytest


def pytest_addoption(parser):
    """Add custom command-line options for integration tests."""
    parser.addoption(
        "--model-path",
        action="store",
        default=None,
        help="Path to model file or directory (local path or hf://repo/model). Optional.",
    )
    parser.addoption(
        "--device",
        action="store",
        default="AUTO",
        help="Inference device (e.g., CPU, GPU, AUTO). Defaults to AUTO.",
    )
    parser.addoption(
        "--author",
        action="store",
        default="OpenVINO",
        help="Hugging Face Hub author/organization name. Defaults to OpenVINO.",
    )
    parser.addoption(
        "--collection",
        action="store",
        default="vision",
        help="Hugging Face Hub collection name. Defaults to vision.",
    )


@pytest.fixture(scope="session")
def model_path(pytestconfig):
    """Fixture to get the model path from command-line argument.

    Returns:
        Optional[str]: Model path or None if not provided
    """
    return pytestconfig.getoption("model_path")


@pytest.fixture(scope="session")
def device(pytestconfig):
    """Fixture to get the device from command-line argument.

    Returns:
        str: Inference device (defaults to "AUTO")
    """
    return pytestconfig.getoption("device")


@pytest.fixture(scope="session")
def author(pytestconfig):
    """Fixture to get the Hugging Face Hub author from command-line argument.

    Returns:
        Optional[str]: Author/organization name or None if not provided
    """
    return pytestconfig.getoption("author")


@pytest.fixture(scope="session")
def collection(pytestconfig):
    """Fixture to get the Hugging Face Hub collection from command-line argument.

    Returns:
        Optional[str]: Collection name or None if not provided
    """
    return pytestconfig.getoption("collection")
