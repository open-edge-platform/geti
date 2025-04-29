// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, View } from '@adobe/react-spectrum';

export const EMPTY_POINT_MESSAGE = 'Click here to place the first node';

export const EmptyPointMessage = () => {
    return (
        <Flex
            width={'100%'}
            height={'100%'}
            position={'absolute'}
            direction={'column'}
            alignItems={'center'}
            justifyContent={'center'}
            UNSAFE_style={{
                pointerEvents: 'none',
                fontSize: 'var(--spectrum-global-dimension-size-275)',
            }}
        >
            <View backgroundColor={'gray-50'} padding={'size-100'}>
                {EMPTY_POINT_MESSAGE}
            </View>
        </Flex>
    );
};
