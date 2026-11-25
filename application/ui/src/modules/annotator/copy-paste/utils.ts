// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { clampBox } from '@geti-ui/smart-tools/utils';
import polylabel from 'polylabel';

import type {
    Annotation,
    AnnotationLabelRef,
    Point,
    Polygon,
    Rect,
    RegionOfInterest,
    Shape,
} from '../../../shared/types';
import { removeOffLimitPointsPolygon } from '../tools/utils';

type Offset = {
    x: number;
    y: number;
};

type PreparePasteParams = {
    clipboard: Annotation[];
    validLabelIds: string[];
    roi: RegionOfInterest;
    offset: (shape: Rect | Polygon) => Point;
};

type PreparedAnnotation = {
    shape: Shape;
    labels: AnnotationLabelRef[];
};

type PreparePasteResult = {
    annotations: PreparedAnnotation[];
    skipped: { labelMissing: number; outsideImage: number };
};

const CASCADE_STEP_PX = 10;

export const getCascadeStep = (zoomScale: number): number => CASCADE_STEP_PX / zoomScale;

export const getCenterOfShape = (shape: Rect | Polygon): Point => {
    switch (shape.type) {
        case 'polygon': {
            const [x, y] = polylabel([shape.points.map((point) => [point.x, point.y])]);

            return { x, y };
        }
        case 'rectangle':
            return { x: shape.x + shape.width / 2, y: shape.y + shape.height / 2 };
    }
};

export const getTranslateVector = ({ x, y }: Point, width: number, height: number, offset: number): Point => {
    const middleX = width / 2;
    const middleY = height / 2;

    // TOP LEFT QUARTER
    if (x < middleX && y < middleY) {
        return { x: offset, y: offset };
    }

    // TOP RIGHT QUARTER
    if (x > middleX && y < middleY) {
        return { x: -offset, y: offset };
    }

    // BOTTOM RIGHT QUARTER
    if (x > middleX && y > middleY) {
        return { x: -offset, y: -offset };
    }

    // BOTTOM LEFT QUARTER
    return { x: offset, y: -offset };
};

// Annotation state is immutable (edits replace objects), so keeping references is a stable snapshot.
export const toClipboardAnnotations = (annotations: Annotation[]): Annotation[] =>
    annotations.filter(({ shape }) => shape.type !== 'full_image');

const offsetRect = (shape: Rect, { x, y }: Offset): Rect => ({ ...shape, x: shape.x + x, y: shape.y + y });

const offsetPolygon = (shape: Polygon, { x, y }: Offset): Polygon => ({
    ...shape,
    points: shape.points.map((point) => ({ x: point.x + x, y: point.y + y })),
});

const MIN_NUMBER_OF_POLYGON_POINTS = 3;

// Returns `null` when nothing visible is left inside the roi.
const clipToRoi = (shape: Rect | Polygon, roi: RegionOfInterest): Shape | null => {
    if (shape.type === 'rectangle') {
        // `clampBox` mirrors rects that lie beyond the right/bottom edge, so reject non-overlapping ones first.
        const overlaps =
            shape.x < roi.x + roi.width &&
            shape.x + shape.width > roi.x &&
            shape.y < roi.y + roi.height &&
            shape.y + shape.height > roi.y;

        if (!overlaps) return null;

        const clamped = clampBox(shape, roi);

        return clamped.width > 0 && clamped.height > 0 ? { ...shape, ...clamped } : null;
    }

    const isInside = shape.points.every(
        ({ x, y }) => x >= roi.x && x <= roi.x + roi.width && y >= roi.y && y <= roi.y + roi.height
    );
    if (isInside) return shape.points.length >= MIN_NUMBER_OF_POLYGON_POINTS ? shape : null;

    const clipped = removeOffLimitPointsPolygon(shape, roi);

    return clipped.points.length >= MIN_NUMBER_OF_POLYGON_POINTS ? { ...shape, ...clipped } : null;
};

export const preparePaste = ({ clipboard, validLabelIds, roi, offset }: PreparePasteParams): PreparePasteResult => {
    const validIds = new Set(validLabelIds);
    const result: PreparePasteResult = { annotations: [], skipped: { labelMissing: 0, outsideImage: 0 } };

    for (const { shape, labels } of clipboard) {
        if (shape.type === 'full_image') continue;

        if (labels.some(({ id }) => !validIds.has(id))) {
            result.skipped.labelMissing += 1;
            continue;
        }

        const translation = offset(shape);
        const moved = shape.type === 'rectangle' ? offsetRect(shape, translation) : offsetPolygon(shape, translation);
        const clipped = clipToRoi(moved, roi);

        if (clipped === null) {
            result.skipped.outsideImage += 1;
            continue;
        }

        result.annotations.push({ shape: clipped, labels });
    }

    return result;
};
