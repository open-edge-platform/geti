// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { AnnotationDTO, Label } from '@/api/types';

export type RegionOfInterest = {
    x: number;
    y: number;
    width: number;
    height: number;
};

export type AnnotationLabelRef = {
    id: string;
    probability?: number;
};

export interface AnnotationLabel extends Label {
    probability?: number;
}

export interface Annotation extends Omit<AnnotationDTO, 'labels' | 'confidences'> {
    id: string;
    labels: AnnotationLabelRef[];
}

export type ClipperPoint = {
    X: number;
    Y: number;
};

export type { Shape, Point, Rect, Polygon } from '@/api/types';
