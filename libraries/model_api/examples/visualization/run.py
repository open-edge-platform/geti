"""Visualization Example."""

# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
from argparse import Namespace

import numpy as np
from model_api.models import Model
from model_api.visualizer import Visualizer
from PIL import Image


def main(args: Namespace):
    image = Image.open(args.image)

    model = Model.create_model(args.model)

    predictions = model(np.array(image))
    visualizer = Visualizer()

    if args.output:
        visualizer.save(image=image, result=predictions, path=args.output)
    else:
        visualizer.show(image=image, result=predictions)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=str, required=True)
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--output", type=str, required=False)
    args = parser.parse_args()
    main(args)
