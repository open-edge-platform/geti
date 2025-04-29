// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
