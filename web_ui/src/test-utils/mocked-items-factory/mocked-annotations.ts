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

import { Annotation } from '../../core/annotations/annotation.interface';
import { Circle, Polygon, Rect, RotatedRect } from '../../core/annotations/shapes.interface';
import { ShapeType } from '../../core/annotations/shapetype.enum';
import { labelFromUser } from '../../core/annotations/utils';
import { getMockedLabel } from './mocked-labels';

const mockedRectAnnotation: Annotation = {
    id: 'test-rect',
    labels: [],
    shape: { shapeType: ShapeType.Rect, x: 0, y: 10, width: 100, height: 110 } as Rect,
    zIndex: 0,
    isSelected: false,
    isHidden: false,
    isLocked: false,
};

const mockedRotatedRectAnnotation: Annotation = {
    id: 'test-rotated-rect',
    labels: [],
    shape: { shapeType: ShapeType.RotatedRect, x: 0, y: 10, width: 100, height: 110, angle: 45 } as RotatedRect,
    zIndex: 0,
    isSelected: false,
    isHidden: false,
    isLocked: false,
};

const mockedCircleAnnotation: Annotation = {
    id: 'test-circle',
    labels: [],
    shape: { shapeType: ShapeType.Circle, x: 0, y: 10, r: 33 } as Circle,
    zIndex: 0,
    isSelected: false,
    isHidden: false,
    isLocked: false,
};

const mockedPolygonAnnotation: Annotation = {
    id: 'test-polygon',
    labels: [],
    shape: {
        shapeType: ShapeType.Polygon,
        points: [
            { x: 0, y: 0 },
            { x: 10, y: 0 },
            { x: 10, y: 10 },
        ],
    } as Polygon,
    zIndex: 0,
    isSelected: false,
    isHidden: false,
    isLocked: false,
};

const mockedKeypointAnnotation: Annotation = {
    id: 'test-keypoint',
    labels: [],
    shape: {
        shapeType: ShapeType.Pose,
        points: [
            {
                label: labelFromUser(getMockedLabel({})),
                x: 10,
                y: 0,
                isVisible: true,
            },
        ],
    },
    zIndex: 0,
    isSelected: false,
    isHidden: false,
    isLocked: false,
};

export const getMockedAnnotation = (
    annotation: Partial<Annotation>,
    shapeType: ShapeType = ShapeType.Rect
): Annotation => {
    switch (shapeType) {
        case ShapeType.Rect: {
            return { ...mockedRectAnnotation, ...annotation };
        }

        case ShapeType.RotatedRect: {
            return { ...mockedRotatedRectAnnotation, ...annotation };
        }

        case ShapeType.Circle: {
            return { ...mockedCircleAnnotation, ...annotation };
        }

        case ShapeType.Polygon: {
            return { ...mockedPolygonAnnotation, ...annotation };
        }
        case ShapeType.Pose: {
            return { ...mockedKeypointAnnotation, ...annotation };
        }
    }
};
