// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ReactNode, useMemo } from 'react';

import { RegionOfInterest } from '../../../../core/annotations/annotation.interface';
import { Circle as CircleInterface } from '../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { Circle } from '../../annotation/shapes/circle.component';
import { drawingStyles } from '../../tools/utils';

interface CircleSizePreviewProps {
    circleSize: number;
    children: ReactNode;
    roi: RegionOfInterest;
    isCircleSizePreviewVisible: boolean;
}

export const CircleSizePreview = ({
    circleSize,
    roi,
    isCircleSizePreviewVisible,
    children,
}: CircleSizePreviewProps): JSX.Element => {
    const circlePreview = useMemo<CircleInterface>(
        () => ({
            shapeType: ShapeType.Circle,
            x: roi.x + roi.width / 2,
            y: roi.y + roi.height / 2,
            r: circleSize,
        }),
        [roi, circleSize]
    );

    return (
        <>
            {children}
            {isCircleSizePreviewVisible && (
                <Circle shape={circlePreview} styles={drawingStyles(null)} ariaLabel={'Circle size preview'} />
            )}
        </>
    );
};
