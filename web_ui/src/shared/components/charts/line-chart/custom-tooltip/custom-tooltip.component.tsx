// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
