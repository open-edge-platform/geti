// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isEmpty, negate } from 'lodash-es';

import { Point } from '../../../../core/annotations/shapes.interface';
import { isDifferent } from '../../../../shared/utils';
import { PolygonMode } from './polygon-tool.enum';

export const ERASER_FIELD_DEFAULT_RADIUS = 5;
export const START_POINT_FIELD_DEFAULT_RADIUS = 6;
export const START_POINT_FIELD_FOCUS_RADIUS = 8;

export const removeEmptySegments =
    (...newSegments: Point[][]) =>
    (prevSegments: Point[][]): Point[][] => {
        const validSegments = newSegments.filter(negate(isEmpty));

        return isEmpty(validSegments) ? [...prevSegments] : [...prevSegments, ...validSegments];
    };

export const deleteSegments =
    (intersectionPoint: Point) =>
    (segments: Point[][]): Point[][] => {
        return segments
            .map((segment: Point[]) => segment.filter((point: Point) => isDifferent(point, intersectionPoint)))
            .filter(negate(isEmpty));
    };

export const isCloseMode = (mode: PolygonMode | null) => {
    if (mode == null) {
        return false;
    }

    return [PolygonMode.PolygonClose, PolygonMode.LassoClose, PolygonMode.MagneticLassoClose].includes(mode);
};
