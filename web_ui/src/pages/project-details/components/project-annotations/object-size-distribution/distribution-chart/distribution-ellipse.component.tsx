// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { SVGProps } from 'react';

interface DistributionEllipseProps extends SVGProps<SVGEllipseElement> {
    maxXValue: number;
    maxYValue: number;
}

export const DistributionEllipse = (props: DistributionEllipseProps): JSX.Element => {
    const { maxXValue, maxYValue, height, width, cx, cy, rx, ry, x, y, ...rest } = props;
    const castedHeight = Number(height);
    const castedWidth = Number(width);
    const castedRx = Number(rx);
    const castedRy = Number(ry);
    const xRatio = castedWidth / maxXValue;
    const yRatio = castedHeight / maxYValue;
    const newCx = Number(cx) * xRatio + Number(x);
    const newCy = Number(y) + castedHeight - Number(cy) * yRatio;
    const finalRx = (castedRx / 2) * xRatio;
    const finalRy = (castedRy / 2) * yRatio;

    return (
        <ellipse
            {...rest}
            cx={newCx}
            cy={newCy}
            rx={finalRx}
            ry={finalRy}
            fill={'none'}
            stroke={'#8E9099'}
            strokeDasharray={'5,5'}
        />
    );
};
