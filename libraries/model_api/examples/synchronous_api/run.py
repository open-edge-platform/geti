#!/usr/bin/env python3
#
# Copyright (C) 2020-2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

import sys

import cv2
from model_api.models import Model


def main():
    if len(sys.argv) != 2:
        usage_message = f"Usage: {sys.argv[0]} <path_to_image>"
        raise RuntimeError(usage_message)

    image = cv2.cvtColor(cv2.imread(sys.argv[1]), cv2.COLOR_BGR2RGB)
    if image is None:
        error_message = f"Failed to read the image: {sys.argv[1]}"
        raise RuntimeError(error_message)

    # Create Image Classification model
    classification_model = Model.create_model("data/otx_models/cls_efficient_b0_cars.xml")
    classifications = classification_model(image)
    print(f"Classification results: {classifications}")

    detection_model = Model.create_model("data/otx_models/ssd-card-detection.xml")
    detections = detection_model(image)
    print(f"Detection results: {detections}")


if __name__ == "__main__":
    main()
