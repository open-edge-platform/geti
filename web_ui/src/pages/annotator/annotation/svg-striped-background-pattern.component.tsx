// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { Annotation } from '../../../core/annotations/annotation.interface';
import { transformToClipperShape } from '../tools/utils';

export const SvgStripedBackgroundPattern = ({
    annotation,
    id,
    color,
}: {
    annotation: Annotation;
    id: string;
    color: string;
}) => {
    const shapePerimeter = useMemo(() => {
        const clipperShape = transformToClipperShape(annotation.shape);

        return Math.abs(clipperShape.totalPerimeter());
    }, [annotation.shape]);

    const width = shapePerimeter * 0.01;
    const strokeWidth = width / 2;
    const twentyPercent = width * 0.2;
    const thirtyPercent = width * 0.3;
    const fourtyPercent = width * 0.4;
    const eightyPercent = width * 0.8;
    const ninetyPercent = width * 0.9;

    const topRightLine = {
        x1: twentyPercent,
        y1: thirtyPercent * -1,
        x2: width + fourtyPercent,
        y2: ninetyPercent,
    };
    const bottomLeftLine = {
        x1: thirtyPercent * -1,
        y1: twentyPercent,
        x2: eightyPercent,
        y2: width + thirtyPercent,
    };

    return (
        <defs>
            <pattern id={id} patternUnits='userSpaceOnUse' width={width} height={width}>
                <line {...topRightLine} stroke={color} strokeWidth={strokeWidth}></line>
                <line {...bottomLeftLine} stroke={color} strokeWidth={strokeWidth}></line>
            </pattern>
        </defs>
    );
};
