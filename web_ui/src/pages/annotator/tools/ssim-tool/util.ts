// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { RegionOfInterest } from '../../../../core/annotations/annotation.interface';
import { intersectionOverUnion } from '../../../../core/annotations/intersection-over-union';
import { getBoundingBox } from '../../../../core/annotations/math';
import { Rect, Shape } from '../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { isShapeWithinRoi } from '../geometry-utils';
import { SSIMMatch } from './ssim-tool.interface';

export const MAX_NUMBER_ITEMS = 500;
export const SSIM_SUPPORTED_DOMAINS = [
    DOMAIN.DETECTION,
    DOMAIN.DETECTION_ROTATED_BOUNDING_BOX,
    DOMAIN.SEGMENTATION,
    DOMAIN.SEGMENTATION_INSTANCE,
    DOMAIN.ANOMALY_DETECTION,
    DOMAIN.ANOMALY_SEGMENTATION,
];

export const guessNumberOfItemsThreshold = (matches: SSIMMatch[], confidenceThreshold = 0.9): number => {
    const guess = matches.findIndex(({ confidence }) => confidence < confidenceThreshold);
    return guess === -1 ? matches.length : guess;
};

export const filterSSIMResults = (
    roi: RegionOfInterest,
    items: SSIMMatch[],
    template: Rect,
    filter: Rect[],
    maxItems = MAX_NUMBER_ITEMS,
    overlapThreshold = 0.2
): SSIMMatch[] => {
    const collector: SSIMMatch[] = [{ shape: template, confidence: 1 }];
    const filterAsMatches = filter.map((shape) => ({ shape, confidence: 1 }));
    const filteredItems = items.filter(({ shape }) => isShapeWithinRoi(roi, shape));

    for (let i = 0; i < filteredItems.length; i++) {
        const value = filteredItems[i];
        const rectOverlapsWithExisting = [...filterAsMatches, ...collector].find(
            (otherMatch: SSIMMatch) => intersectionOverUnion(otherMatch.shape, value.shape) > overlapThreshold
        );

        if (!rectOverlapsWithExisting) {
            collector.push(value);
        }

        if (collector.length === maxItems) {
            return collector;
        }
    }
    return collector;
};

export const convertToRect = (shape: Shape): Rect => {
    return { shapeType: ShapeType.Rect, ...getBoundingBox(shape) };
};

export const convertRectToShape = (rectangle: Rect, shapeType: ShapeType): Shape => {
    switch (shapeType) {
        case ShapeType.Rect:
            return rectangle;
        case ShapeType.RotatedRect: {
            const { x, y, width, height } = rectangle;
            const rx = width / 2;
            const ry = width / 2;
            return {
                shapeType: ShapeType.RotatedRect,
                angle: 0,
                x: x + rx,
                y: y + ry,
                width,
                height,
            };
        }
        case ShapeType.Circle: {
            const { x, y, width } = rectangle;
            const r = width / 2;
            return {
                shapeType: ShapeType.Circle,
                x: x + r,
                y: y + r,
                r,
            };
        }
        default:
            throw 'Unexpected shape type given to SSIM';
    }
};
