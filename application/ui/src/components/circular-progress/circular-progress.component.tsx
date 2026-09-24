// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { type ColorValue } from '@geti-ui/ui';

const CHECK_MARK_SIZE = 50;
const CHECK_MARK_COLOR = 'var(--energy-blue-shade)';

type CircularProgressProps = {
    percentage: number;
    size?: number;
    labelFontSize?: number;
    strokeWidth?: number;
    labelFontColor?: ColorValue;
    backStrokeColor?: ColorValue;
    color?: ColorValue;
};

export const CircularProgress = ({
    percentage,
    size = 50,
    strokeWidth = 4,
    labelFontSize = 10,
    labelFontColor = 'gray-600',
    backStrokeColor = 'gray-100',
    color = 'blue-400',
}: CircularProgressProps) => {
    const progress = Math.floor(Math.max(0, Math.min(100, percentage)));
    const isComplete = progress >= 100;

    const viewBox = `0 0 ${size} ${size}`;
    const radius = (size - strokeWidth) / 2;
    const circumference = radius * Math.PI * 2;
    const dash = (progress * circumference) / 100;

    return (
        <svg width={size} height={size} viewBox={viewBox} aria-label='progress circular loader'>
            <circle
                fill='none'
                stroke={`var(--spectrum-global-color-${backStrokeColor})`}
                cx={size / 2}
                cy={size / 2}
                r={radius}
                strokeWidth={`${strokeWidth}px`}
            />
            <circle
                fill='none'
                stroke={isComplete ? CHECK_MARK_COLOR : `var(--spectrum-global-color-${color})`}
                cx={size / 2}
                cy={size / 2}
                r={radius}
                strokeWidth={`${strokeWidth}px`}
                transform={`rotate(-90 ${size / 2} ${size / 2})`}
                strokeDasharray={`${[dash, circumference - dash]}`}
                strokeLinecap='square'
                style={{ transition: 'all 0.5s' }}
            />
            <text
                fill={isComplete ? CHECK_MARK_COLOR : `var(--spectrum-global-color-${labelFontColor})`}
                fontSize={isComplete ? `${CHECK_MARK_SIZE}px` : `${labelFontSize}px`}
                dy={isComplete ? `${CHECK_MARK_SIZE / 2.5}px` : `${labelFontSize / 2}px`}
                textAnchor='middle'
                x='50%'
                y='50%'
            >
                {isComplete ? '✓' : `${progress}%`}
            </text>
        </svg>
    );
};
