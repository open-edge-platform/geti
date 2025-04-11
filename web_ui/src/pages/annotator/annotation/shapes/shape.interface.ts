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

import { SVGProps } from 'react';

import {
    Circle as CircleShape,
    Polygon as PolygonShape,
    Pose as PoseShape,
    Rect as RectangleShape,
    RotatedRect as RotatedRectangleShape,
} from '../../../../core/annotations/shapes.interface';

interface ShapeStyle<T> {
    styles?: SVGProps<T>;
    className?: string;
}

export interface RectangleProps extends ShapeStyle<SVGRectElement> {
    ariaLabel?: string;
    shape: RectangleShape;
}

export interface RotatedRectangleProps extends ShapeStyle<SVGRectElement> {
    ariaLabel?: string;
    shape: RotatedRectangleShape;
}

export interface CircleProps extends ShapeStyle<SVGCircleElement> {
    ariaLabel?: string;
    shape: CircleShape;
}

export interface PolygonProps extends ShapeStyle<SVGPolygonElement> {
    shape: PolygonShape;
    ariaLabel?: string;
    indicatorRadius?: number;
}

export interface KeypointProps extends ShapeStyle<SVGCircleElement> {
    shape: PoseShape;
    ariaLabel?: string;
}
