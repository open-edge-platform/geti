// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { PolygonProps } from '../annotation/shapes/shape.interface';
import { getFormattedPoints } from '../utils';

const CIRCLE_STROKE_COLOR = 'var(--energy-blue-shade)';

export const PolygonDraw = ({
    shape,
    styles,
    indicatorRadius,
    className = '',
    ariaLabel = '',
}: PolygonProps): JSX.Element => {
    const points = useMemo((): string => getFormattedPoints(shape.points), [shape]);

    return (
        <g>
            <circle
                r={indicatorRadius}
                cx={shape.points[0].x}
                cy={shape.points[0].y}
                fill='transparent'
                stroke={CIRCLE_STROKE_COLOR}
            />
            <polyline aria-label={ariaLabel} points={points} {...styles} className={className} />;
        </g>
    );
};
