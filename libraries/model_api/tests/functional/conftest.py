#
# Copyright (C) 2020-2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
import contextlib
import json
import sys
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _force_cpu_fp32_inference(monkeypatch):
    """Pin CPU inference precision to f32 so reference comparisons are hardware-independent.

    OpenVINO's CPU plugin enables bf16 inference by default on AMX-capable CPUs
    (e.g. the Sapphire Rapids GitHub-hosted runners). bf16 diverges from the f32
    reference values the functional tests compare against, producing shifted
    bounding boxes, different contour/object counts, etc. The references are not
    portable across bf16 implementations (AVX512 vs AMX vs emulation), so instead
    of updating them we force f32 everywhere, matching how the references were
    generated and how most developer machines already run.

    ``create_model`` builds its ``openvino.Core`` internally via ``create_core``,
    so we wrap ``create_core`` in every module that imported it (the adapter
    module, the model module, and the test module) to set the precision hint.
    """
    from model_api.adapters import openvino_adapter as ov_adapter

    original_create_core = ov_adapter.create_core

    def create_core_fp32():
        core = original_create_core()
        with contextlib.suppress(Exception):
            core.set_property("CPU", {"INFERENCE_PRECISION_HINT": "f32"})
        return core

    for module in list(sys.modules.values()):
        if getattr(module, "create_core", None) is original_create_core:
            monkeypatch.setattr(module, "create_core", create_core_fp32)


def pytest_addoption(parser):
    parser.addoption("--data", action="store", help="data folder with dataset")
    parser.addoption(
        "--model_data",
        action="store",
        default="public_scope.json",
        help="path to model data JSON file for test parameterization",
    )
    parser.addoption(
        "--device",
        action="store",
        default="CPU",
        help="device to run tests on (in case of OpenvinoAdapter)",
    )
    parser.addoption(
        "--dump",
        action="store_true",
        default=False,
        help="whether to dump results into json file",
    )
    parser.addoption(
        "--results-dir",
        action="store",
        default="",
        help="directory to store inference result",
    )
    parser.addoption(
        "--only-model-type",
        action="store",
        default="",
        help="select model type to run tests on (and all that inherit from it)",
    )


def pytest_configure(config):
    config.test_results = []


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    result = outcome.get_result()

    if result.when == "call":
        test_results = item.config.test_results

        if not test_results:
            return

        with Path("test_scope.json").open("w") as outfile:
            json.dump(test_results, outfile, indent=4)


@pytest.fixture(scope="session")
def data(pytestconfig):
    return pytestconfig.getoption("data")
