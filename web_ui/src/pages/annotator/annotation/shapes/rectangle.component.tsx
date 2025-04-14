// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { RectangleProps } from './shape.interface';

export const Rectangle = ({ shape, styles, ariaLabel }: RectangleProps): JSX.Element => {
    const { x, y, width, height } = shape;

    return <rect x={x} y={y} width={width} height={height} {...styles} aria-label={ariaLabel} />;
};
