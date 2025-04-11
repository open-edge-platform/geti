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
