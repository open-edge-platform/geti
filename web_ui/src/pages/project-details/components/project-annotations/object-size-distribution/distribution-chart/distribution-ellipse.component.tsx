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
