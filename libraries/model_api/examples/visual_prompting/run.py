#!/usr/bin/env python3
#
# Copyright (C) 2020-2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

import argparse
import colorsys
from itertools import starmap

import cv2
import numpy as np
from model_api.models import Model, Prompt, SAMVisualPrompter


def get_colors(n: int):
    HSV_tuples = [(x / n, 0.5, 0.5) for x in range(n)]
    RGB_tuples = starmap(colorsys.hsv_to_rgb, HSV_tuples)
    return (np.array(list(RGB_tuples)) * 255).astype(np.uint8)


def main():
    parser = argparse.ArgumentParser(description="SAM sample script")
    parser.add_argument("image", type=str)
    parser.add_argument("encoder_path", type=str)
    parser.add_argument("decoder_path", type=str)
    parser.add_argument("prompts", nargs="+", type=int)
    args = parser.parse_args()

    image = cv2.cvtColor(cv2.imread(args.image), cv2.COLOR_BGR2RGB)
    if image is None:
        error_message = f"Failed to read the image: {args.image}"
        raise RuntimeError(error_message)

    encoder = Model.create_model(args.encoder_path)
    decoder = Model.create_model(args.decoder_path)
    sam_prompter = SAMVisualPrompter(encoder, decoder)

    all_prompts = []
    for i, p in enumerate(np.array(args.prompts).reshape(-1, 2)):
        all_prompts.append(Prompt(p, i))

    result = sam_prompter(image, points=all_prompts)

    colors = get_colors(len(all_prompts))

    for i in range(len(result.upscaled_masks)):
        print(f"Prompt {i}, mask score {result.best_iou[i]:.3f}")
        masked_img = np.where(result.processed_mask[i][..., None], colors[i], image)
        image = cv2.addWeighted(image, 0.2, masked_img, 0.8, 0)

    cv2.imwrite("sam_result.jpg", cv2.cvtColor(image, cv2.COLOR_RGB2BGR))


if __name__ == "__main__":
    main()
