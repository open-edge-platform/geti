// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
