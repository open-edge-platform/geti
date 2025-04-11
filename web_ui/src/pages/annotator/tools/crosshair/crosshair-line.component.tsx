// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Point } from '../../../../core/annotations/shapes.interface';

export enum CROSSHAIR_LINE_DIRECTION {
    HORIZONTAL,
    VERTICAL,
}

const DEFAULT_SIZE = 1.0;

interface CrosshairLineProps {
    zoom: number;
    point: Point;
    direction: CROSSHAIR_LINE_DIRECTION;
}

const colors = {
    main: {
        color: 'white',
        opacity: 0.9,
    },
    shade: {
        color: '#000000',
        opacity: 0.12,
    },
};

export const CrosshairLine = ({ zoom, direction, point }: CrosshairLineProps): JSX.Element => {
    const attributes =
        direction === CROSSHAIR_LINE_DIRECTION.HORIZONTAL
            ? {
                  y: point.y,
                  width: '100%',
                  height: DEFAULT_SIZE / zoom,
              }
            : {
                  x: point.x,
                  width: DEFAULT_SIZE / zoom,
                  height: '100%',
              };

    return (
        <rect
            {...attributes}
            fillOpacity={colors.main.opacity}
            fill={colors.main.color}
            stroke={colors.shade.color}
            strokeOpacity={colors.shade.opacity}
            strokeWidth={DEFAULT_SIZE / zoom}
        />
    );
};
