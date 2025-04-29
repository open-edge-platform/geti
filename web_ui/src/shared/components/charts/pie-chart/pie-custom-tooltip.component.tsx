// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
