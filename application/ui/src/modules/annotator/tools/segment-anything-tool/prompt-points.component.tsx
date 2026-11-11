// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { InteractiveAnnotationPoint } from './segment-anything.interface';

// Divided by the zoom scale so points keep their on-screen size while zooming.
const POINT_STYLE = {
    r: 'calc(5px / var(--zoom-scale, 1))',
    strokeWidth: 'calc(1.5px / var(--zoom-scale, 1))',
};

type PromptPointsProps = {
    points: InteractiveAnnotationPoint[];
};

export const PromptPoints = ({ points }: PromptPointsProps) => {
    return (
        <g aria-label='Segment anything prompt points' pointerEvents='none'>
            {points.map((point) => (
                <circle
                    key={`${point.x}:${point.y}`}
                    aria-label={point.positive ? 'Positive point' : 'Negative point'}
                    cx={point.x}
                    cy={point.y}
                    fill={point.positive ? 'var(--moss-tint-1)' : 'var(--coral-shade-1)'}
                    stroke='white'
                    style={POINT_STYLE}
                />
            ))}
        </g>
    );
};
