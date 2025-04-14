// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, CSSProperties } from 'react';

import { RegionOfInterest } from '../../../../core/annotations/annotation.interface';
import { Point } from '../../../../core/annotations/shapes.interface';
import { Label } from '../../../../core/labels/label.interface';
import { StrokeLinecap, StrokeLinejoin } from '../../annotation/shapes/line.component';
import { BrushSizeCursor } from '../watershed-tool/brush-size-cursor.component';

export type Marker = {
    label: Label;
    points: Point[];
    brushSize: number;
    id: number;
};

export interface MarkerToolProps {
    zoom: number;
    label: Label;
    markerId: number;
    brushSize: number;
    ariaLabel?: string;
    roi?: RegionOfInterest;
    styles?: CSSProperties;
    image: ImageData;
    strokeLinecap?: StrokeLinecap;
    strokeLinejoin?: StrokeLinejoin;
    onComplete: (marker: Marker) => void;
    renderCursor?: (props: ComponentProps<typeof BrushSizeCursor>) => JSX.Element;
}
