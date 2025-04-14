// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
