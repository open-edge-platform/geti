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

import { CSSProperties, ReactNode } from 'react';

import { Anchor as InternalAnchor } from './anchor.component';
import { ResizeAnchorType } from './resize-anchor.enum';

export const ANCHOR_SIZE = 8;

interface ResizeAnchorProps {
    zoom: number;
    x: number;
    y: number;
    moveAnchorTo: (x: number, y: number) => void;
    cursor?: CSSProperties['cursor'];
    label: string;
    onStart?: () => void;
    onComplete: () => void;
    type?: ResizeAnchorType;
    fill?: string;
    angle?: number;
    stroke?: string;
    strokeWidth?: number;
    Anchor?: ReactNode;
}

interface DefaultCircleProps {
    zoom: number;
    x: number;
    y: number;
    fill?: string;
    stroke?: string;
    strokeWidth?: number;
}

const DefaultCircle = ({ x, y, zoom, fill, stroke, strokeWidth = 1 }: DefaultCircleProps) => {
    return <circle cx={x} cy={y} r={ANCHOR_SIZE / zoom / 2} {...{ fill, stroke, strokeWidth: strokeWidth / zoom }} />;
};

export const ResizeAnchor = ({
    x,
    y,
    zoom,
    onStart,
    onComplete,
    moveAnchorTo,
    label,
    fill = 'white',
    type = ResizeAnchorType.SQUARE,
    angle = 0,
    cursor = 'all-scroll',
    stroke = 'var(--energy-blue)',
    strokeWidth = 1,
    Anchor = <DefaultCircle x={x} y={y} zoom={zoom} fill={fill} stroke={stroke} strokeWidth={strokeWidth} />,
}: ResizeAnchorProps): JSX.Element => {
    const size = ANCHOR_SIZE / zoom;

    // We render both a visual anchor and an invisible anchor that has a larger
    // clicking area than the visible one
    const visualAnchorProps = {
        fill,
        stroke,
        strokeWidth: strokeWidth / zoom,
    };

    return (
        <InternalAnchor
            size={size}
            label={label}
            x={x}
            y={y}
            zoom={zoom}
            fill={fill}
            cursor={cursor ? cursor : 'default'}
            onStart={onStart}
            onComplete={onComplete}
            moveAnchorTo={moveAnchorTo}
        >
            {type === ResizeAnchorType.SQUARE ? (
                <g fillOpacity={1.0} transform={`rotate(${angle})`} transform-origin={`${x}px ${y}px`}>
                    <rect x={x - size / 2} y={y - size / 2} width={size} height={size} {...visualAnchorProps} />
                </g>
            ) : (
                Anchor
            )}
        </InternalAnchor>
    );
};
