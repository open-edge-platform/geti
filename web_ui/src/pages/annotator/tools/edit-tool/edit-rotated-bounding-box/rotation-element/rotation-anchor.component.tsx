// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties } from 'react';

import { Rotation } from '@geti/ui/icons';

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
