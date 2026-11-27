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
from model_api.models import Model, Prompt, SAMLearnableVisualPrompter


def get_colors(n: int):
    HSV_tuples = [(x / n, 0.5, 0.5) for x in range(n)]
    RGB_tuples = starmap(colorsys.hsv_to_rgb, HSV_tuples)
    return (np.array(list(RGB_tuples)) * 255).astype(np.uint8)


def main():
    parser = argparse.ArgumentParser(description="SAM sample script")
    parser.add_argument("image_source", type=str)
    parser.add_argument("image_target", type=str)
    parser.add_argument("encoder_path", type=str)
    parser.add_argument("decoder_path", type=str)
    parser.add_argument("prompts", nargs="+", type=int)
    parser.add_argument("-t", "--threshold", type=float, default=0.65)
    args = parser.parse_args()

    image = cv2.cvtColor(cv2.imread(args.image_source), cv2.COLOR_BGR2RGB)
    if image is None:
        error_message = f"Failed to read the source image: {args.image_source}"
        raise RuntimeError(error_message)

    image_target = cv2.cvtColor(cv2.imread(args.image_target), cv2.COLOR_BGR2RGB)
    if image_target is None:
        error_message = f"Failed to read the target image: {args.image_target}"
        raise RuntimeError(error_message)

    encoder = Model.create_model(args.encoder_path)
    decoder = Model.create_model(args.decoder_path)
    zsl_sam_prompter = SAMLearnableVisualPrompter(
        encoder,
        decoder,
        threshold=args.threshold,
    )

    all_prompts = []
    for i, p in enumerate(np.array(args.prompts).reshape(-1, 2)):
        all_prompts.append(Prompt(p, i))

    zsl_sam_prompter.learn(image, points=all_prompts)

    colors = get_colors(len(all_prompts))

    result = zsl_sam_prompter(image_target)

    for i in result.data:
        masks = result.get_mask(i)
        for j, instance in enumerate(masks.mask):
            prompt_point = masks.points[j].astype(np.int32)
            confidence = float(masks.scores[j])
            masked_img = np.where(instance[..., None], colors[i], image_target)
            image_target = cv2.addWeighted(image_target, 0.2, masked_img, 0.8, 0)
            print(f"Reference point: {prompt_point}, point score: {confidence:.3f}")
            cv2.circle(
                image_target,
                prompt_point,
                radius=0,
                color=(0, 0, 255),
                thickness=5,
            )

    cv2.imwrite("zsl_sam_result.jpg", cv2.cvtColor(image_target, cv2.COLOR_RGB2BGR))


if __name__ == "__main__":
    main()
