// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
