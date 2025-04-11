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

import { CSSProperties } from 'react';

import { Rotation } from '../../../../../../assets/icons';
import { Anchor } from '../../anchor.component';

interface RotationAnchorProps {
    zoom: number;
    x: number;
    y: number;
    angle: number;
    moveAnchorTo: (x: number, y: number) => void;
    cursor?: CSSProperties['cursor'];
    label: string;
    isRotating: boolean;
    onComplete: () => void;
}

export const RotationAnchor = ({
    x,
    y,
    angle,
    moveAnchorTo,
    label,
    onComplete,
    zoom,
    isRotating,
    cursor,
}: RotationAnchorProps): JSX.Element => {
    const anchorSize = 14 / zoom;

    return (
        <g fillOpacity={1.0} transform={`rotate(${angle})`} transform-origin={`${x}px ${y}px`}>
            <Anchor
                size={anchorSize}
                moveAnchorTo={moveAnchorTo}
                onComplete={onComplete}
                label={label}
                x={x}
                y={y}
                zoom={zoom}
                cursor={cursor ? cursor : 'default'}
            >
                {!isRotating && (
                    <Rotation
                        x={x - anchorSize / 2}
                        y={y - anchorSize / 2}
                        width={anchorSize}
                        height={anchorSize}
                        strokeWidth={1}
                    />
                )}
            </Anchor>
        </g>
    );
};
