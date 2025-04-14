// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CircleProps } from './shape.interface';

export const Circle = ({ shape, styles, ariaLabel, ...rest }: CircleProps): JSX.Element => {
    return <circle cx={shape.x} cy={shape.y} r={shape.r} {...styles} aria-label={ariaLabel} {...rest} />;
};
