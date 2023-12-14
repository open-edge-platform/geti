#!/usr/bin/env python3
"""
 Copyright (c) 2021-2023 Intel Corporation

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

from pathlib import Path

from setuptools import find_packages, setup

SETUP_DIR = Path(__file__).resolve().parent

setup(
    name="openvino_model_api",
    version="0.1.9",
    description="Model API: model wrappers and pipelines for inference with OpenVINO",
    author="Intel(R) Corporation",
    url="https://github.com/openvinotoolkit/model_api",
    packages=find_packages(SETUP_DIR),
    package_dir={"openvino": str(SETUP_DIR / "openvino")},
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
    ],
    license="OSI Approved :: Apache Software License",
    python_requires=">=3.7",
    install_requires=(SETUP_DIR / "requirements.txt").read_text(),
    extras_require={
        "ovms": (SETUP_DIR / "requirements_ovms.txt").read_text(),
        "tests": [
            "httpx",
            "pytest",
            "openvino-dev[onnx,pytorch,tensorflow2]",
            "ultralytics>=8.0.114,<=8.0.205",
            "onnx",
            "onnxruntime",
        ],
    },
    long_description=(SETUP_DIR.parents[1] / "README.md").read_text(),
    long_description_content_type="text/markdown",
)
