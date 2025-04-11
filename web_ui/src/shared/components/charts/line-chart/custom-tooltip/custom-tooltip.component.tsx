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

import { Flex } from '@adobe/react-spectrum';
import { Text } from '@react-spectrum/text';

import { Point } from '../../../../../core/annotations/shapes.interface';
import { CustomTooltipWrapper } from '../../custom-tooltip-wrapper/custom-tooltip-wrapper.component';

interface CustomTooltipLineChartProps {
    payload?: {
        payload: Point;
    }[];
    active?: boolean;
    xLabel: string;
    yLabel: string;
    formatter: (value: number) => number;
}

export const CustomTooltipLineChart = (props: CustomTooltipLineChartProps): JSX.Element => {
    const { payload, active, xLabel, yLabel, formatter } = props;

    return payload && payload.length && active ? (
        <CustomTooltipWrapper>
            <Flex direction={'column'} rowGap={'size-65'}>
                <Text>
                    {xLabel}: {formatter(payload[0].payload.x)}
                </Text>
                <Text>
                    {yLabel}: {formatter(payload[0].payload.y)}
                </Text>
            </Flex>
        </CustomTooltipWrapper>
    ) : (
        <></>
    );
};
