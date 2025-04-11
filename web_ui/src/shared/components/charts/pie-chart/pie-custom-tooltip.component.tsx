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

import { Flex, Heading, Text, View } from '@adobe/react-spectrum';
import { useNumberFormatter } from 'react-aria';

interface PieChartProps {
    data: {
        name: string | null;
        value: number;
        fill: string;
    }[];
}

interface PieCustomTooltipProps {
    payload?: PieChartProps['data'];
    active?: boolean;
    total: number;
}

export const PieCustomTooltip = (props: PieCustomTooltipProps): JSX.Element | null => {
    const { active, payload, total } = props;
    const formatter = useNumberFormatter({ maximumFractionDigits: 2 });

    if (active && payload && payload.length) {
        const [item] = payload;
        const formattedNumberOfItem = formatter.format(Math.round(item.value * 100) / total);
        return (
            <View
                backgroundColor={'gray-400'}
                paddingY={'size-150'}
                paddingX={'size-200'}
                borderWidth={'thin'}
                borderRadius={'small'}
                borderColor={'gray-400'}
            >
                <Flex direction={'column'}>
                    <Heading margin={0}>{item.name}</Heading>
                    <Text>{formattedNumberOfItem}% of objects</Text>
                    <Text>{formatter.format(item.value)} objects</Text>
                </Flex>
            </View>
        );
    }
    return null;
};
