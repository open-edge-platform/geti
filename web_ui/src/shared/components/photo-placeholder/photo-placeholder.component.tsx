// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex, Text, View } from '@adobe/react-spectrum';
import { ViewProps } from '@react-types/view';
import isEmpty from 'lodash/isEmpty';

import { getDistinctColorBasedOnHash } from '../../../pages/create-project/components/distinct-colors';
import { getForegroundColor, hexaToRGBA } from '../../../pages/utils';

interface PhotoPlaceholderProps {
    name: string;
    email: string;
    width?: ViewProps<5>['height'];
    height?: ViewProps<5>['height'];
    borderRadius?: string;
}

export const PhotoPlaceholder = ({
    name,
    email,
    width = 'size-1600',
    height = 'size-1600',
    borderRadius = '50%',
}: PhotoPlaceholderProps): JSX.Element => {
    const backgroundColor = getDistinctColorBasedOnHash(email);
    const letter = (isEmpty(name.trim()) ? email : name).charAt(0);

    const color = getForegroundColor(
        hexaToRGBA(backgroundColor),
        'var(--spectrum-global-color-gray-50)',
        'var(--spectrum-global-color-gray-900)'
    );

    return (
        <View
            width={width}
            minWidth={width}
            minHeight={height}
            height={height}
            UNSAFE_style={{ backgroundColor, color, borderRadius }}
            data-testid={'placeholder-avatar-id'}
        >
            <Flex height={'100%'} width={'100%'} alignItems={'center'} justifyContent={'center'}>
                <Text data-testid={'placeholder-letter-id'}>{letter.toUpperCase()}</Text>
            </Flex>
        </View>
    );
};
