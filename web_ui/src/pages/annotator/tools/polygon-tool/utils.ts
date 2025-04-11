// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import isEmpty from 'lodash/isEmpty';
import negate from 'lodash/negate';

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
