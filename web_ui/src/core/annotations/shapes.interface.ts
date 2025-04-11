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

import { Label } from '../labels/label.interface';
import { ShapeType } from './shapetype.enum';

export interface Point {
    x: number;
    y: number;
}

export interface Rect {
    readonly shapeType: ShapeType.Rect;
    readonly x: number;
    readonly y: number;
    readonly width: number;
    readonly height: number;
}

export interface Circle {
    readonly shapeType: ShapeType.Circle;
    readonly x: number;
    readonly y: number;
    readonly r: number;
}

export interface Polygon {
    readonly shapeType: ShapeType.Polygon;
    readonly points: Point[];
}

export interface RotatedRect {
    readonly shapeType: ShapeType.RotatedRect;
    readonly x: number;
    readonly y: number;
    readonly width: number;
    readonly height: number;
    readonly angle: number; //degrees
}

export interface KeypointNode extends Point {
    readonly label: Label;
    readonly isVisible: boolean;
}

export interface Pose {
    readonly shapeType: ShapeType.Pose;
    readonly points: KeypointNode[];
}

export type Shape = Rect | RotatedRect | Circle | Polygon | Pose;
