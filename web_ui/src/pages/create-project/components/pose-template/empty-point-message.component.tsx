// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
