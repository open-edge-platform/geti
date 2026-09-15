# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
import shutil
import zipfile
from pathlib import Path

import pytest
import requests

logger = logging.getLogger(__name__)

S3_URL = "https://storage.geti.intel.com/test-data/geti/datasets"
OBJECT_NAME = "regression.zip"
PARENT_DIR = Path(__file__).parent
DATASETS_DIR = PARENT_DIR / "regression"


def _download_regression_datasets(dest_dir: Path) -> None:
    """Download and unpack the regression dataset archive from public location."""
    archive = dest_dir / OBJECT_NAME

    if not archive.exists():
        logger.info("Downloading regression datasets from S3: %s", S3_URL)
        response = requests.get(f"{S3_URL}/{OBJECT_NAME}", stream=True)
        with open(archive, "wb") as f:
            shutil.copyfileobj(response.raw, f)

    with zipfile.ZipFile(archive, "r") as zf:
        zf.extractall(dest_dir)


def pytest_configure() -> None:
    """Session-wide hook - download datasets before collection begins.

    Connection failures are tolerated so running the test suite in an
    environment without access to the dataset storage does not abort test
    collection; the data-dependent tests are skipped instead.
    """
    try:
        _download_regression_datasets(PARENT_DIR)
    except requests.exceptions.ConnectionError as error:
        logger.warning("Skipping regression dataset download: %s", error)


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parametrize after datasets are already downloaded."""
    if "archive" in metafunc.fixturenames:
        zip_files = sorted(DATASETS_DIR.glob("*.zip"))
        if not zip_files:
            pytest.skip(
                f"No regression dataset archives in '{DATASETS_DIR}': download skipped (offline) "
                "or the archive structure changed.",
                allow_module_level=True,
            )
        metafunc.parametrize("archive", zip_files, ids=[p.stem for p in zip_files])


def pytest_unconfigure() -> None:
    """Session-wide hook - remove downloaded archive and unpacked files after tests complete."""
    archive = PARENT_DIR / OBJECT_NAME
    if archive.exists():
        archive.unlink()
    if DATASETS_DIR.exists():
        shutil.rmtree(DATASETS_DIR)
