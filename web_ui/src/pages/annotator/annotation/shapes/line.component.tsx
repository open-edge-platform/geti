// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties, ReactElement, SVGProps, useMemo } from 'react';

import { Point } from '../../../../core/annotations/shapes.interface';
import { getFormattedPoints } from '../../utils';

export type StrokeLinecap = 'butt' | 'round' | 'square';
export type StrokeLinejoin = 'miter' | 'round' | 'bevel';

interface LineProps {
    color: string;
    points: Point[];
    brushSize?: number;
    ariaLabel?: string;
    strokeLinecap?: StrokeLinecap;
    strokeLinejoin?: StrokeLinejoin;
    style?: CSSProperties;
}

export const Line = ({
    color,
    points,
    ariaLabel,
    brushSize = 4, // Default value: 4px
    strokeLinecap = 'round',
    strokeLinejoin = 'round',
    style,
}: LineProps): ReactElement<SVGProps<SVGPolylineElement>> => {
    const formattedPoints = useMemo((): string => getFormattedPoints(points), [points]);

    const props = {
        points: formattedPoints,
        stroke: color,
        // NOTE: if we set strokeWidth to brushSize, it's 2x smaller that the radius, therefore we need to multiply it.
        strokeWidth: brushSize * 2,
        fill: 'none',
        strokeLinecap,
        strokeLinejoin,
    };

    return <polyline {...props} aria-label={ariaLabel} style={style} />;
};
