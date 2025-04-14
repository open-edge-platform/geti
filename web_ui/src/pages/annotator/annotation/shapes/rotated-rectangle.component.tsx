// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { RotatedRectangleProps } from './shape.interface';

export const RotatedRectangle = ({ shape, styles, className = '', ariaLabel }: RotatedRectangleProps): JSX.Element => {
    const { x, y, width, height, angle } = shape;

    return (
        <rect
            x={x - width / 2}
            y={y - height / 2}
            width={width}
            height={height}
            transform={`rotate(${angle})`}
            transform-origin={`${x}px ${y}px`}
            {...styles}
            className={className}
            aria-label={ariaLabel}
        />
    );
};
