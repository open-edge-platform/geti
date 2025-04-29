// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { getFormattedPoints } from '../../utils';
import { PolygonProps } from './shape.interface';

export const Polygon = ({ shape, styles, ariaLabel }: PolygonProps): JSX.Element => {
    const points = useMemo((): string => getFormattedPoints(shape.points), [shape]);

    return (
        <g>
            <polygon points={points} {...styles} aria-label={ariaLabel} />
        </g>
    );
};
