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

interface BrushSizeCursorProps {
    x: number;
    y: number;
    brushSize: number;
    strokeWidth: number;
    fill: string;
    ariaLabel: string;
}

export const BrushSizeCursor = ({
    x,
    y,
    brushSize,
    strokeWidth,
    fill,
    ariaLabel,
}: BrushSizeCursorProps): JSX.Element => {
    return (
        <circle
            cx={x}
            cy={y}
            r={brushSize}
            fill={fill}
            fillOpacity={0.5}
            stroke={'black'}
            strokeWidth={strokeWidth}
            aria-label={ariaLabel}
        />
    );
};
