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
