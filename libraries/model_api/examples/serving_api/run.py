#!/usr/bin/env python3
#
# Copyright (C) 2020-2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

import sys

import cv2
from model_api.models import DetectionModel


def main():
    if len(sys.argv) != 2:
        usage_message = f"Usage: {sys.argv[0]} <path_to_image>"
        raise RuntimeError(usage_message)

    image = cv2.imread(sys.argv[1])
    if image is None:
        error_message = f"Failed to read the image: {sys.argv[1]}"
        raise RuntimeError(error_message)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    # Create Object Detection model specifying the OVMS server URL
    model = DetectionModel.create_model(
        "localhost:8000/v2/models/ssd-card-detection",
        model_type="ssd",
    )
    detections = model(image)
    print(f"Detection results: {detections}")


if __name__ == "__main__":
    main()
