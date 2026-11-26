#!/usr/bin/env python3
#
# Copyright (C) 2020-2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

import sys

import cv2
from model_api.models import Model


def main():
    if len(sys.argv) != 3:
        usage_message = f"Usage: {sys.argv[0]} <path_to_model> <path_to_image>"
        raise RuntimeError(usage_message)

    image = cv2.cvtColor(cv2.imread(sys.argv[2]), cv2.COLOR_BGR2RGB)
    if image is None:
        error_message = f"Failed to read the image: {sys.argv[2]}"
        raise RuntimeError(error_message)

    model = Model.create_model(sys.argv[1])

    ITERATIONS = 10
    results = {}  # container for results

    def callback(result, userdata):
        print(f"Done! Number: {userdata}")
        results[userdata] = result

    model.set_callback(callback)
    ## Run parallel inference
    for i in range(ITERATIONS):
        model.infer_async(image, user_data=i)

    model.await_all()
    assert len(results) == ITERATIONS

    for i in range(ITERATIONS):
        print(f"Request {i}: {results[i]}")


if __name__ == "__main__":
    main()
