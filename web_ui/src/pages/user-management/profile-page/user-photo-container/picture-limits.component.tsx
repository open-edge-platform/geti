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

import { Content, ContextualHelp, Flex, Text, View } from '@adobe/react-spectrum';
import { useNumberFormatter } from 'react-aria';

import { getFileSize } from '../../../../shared/utils';
import { USER_PHOTO_VALIDATION_RULES } from './utils';

const PictureLimitTooltip = (): JSX.Element => {
    const formatter = useNumberFormatter({ notation: 'compact' });

    return (
        <Flex direction={'column'} gap={'size-200'} data-testid={'picture-limits-id'}>
            <Flex direction={'column'}>
                <Text>Dimension:</Text>
                <Text>
                    Min - {USER_PHOTO_VALIDATION_RULES.MIN_WIDTH} x {USER_PHOTO_VALIDATION_RULES.MIN_HEIGHT}
                </Text>
                <Text>
                    Max - {formatter.format(USER_PHOTO_VALIDATION_RULES.MAX_WIDTH)} x{' '}
                    {formatter.format(USER_PHOTO_VALIDATION_RULES.MAX_HEIGHT)}
                </Text>
            </Flex>
            <Flex direction={'column'}>
                <Text>Size:</Text>
                <Text>Max - {getFileSize(USER_PHOTO_VALIDATION_RULES.MAX_SIZE, { base: 2, standard: 'jedec' })}</Text>
            </Flex>
        </Flex>
    );
};

export const PictureLimits = (): JSX.Element => {
    return (
        <View width={'max-content'} marginTop={'size-200'}>
            <Flex alignItems={'center'} gap={'size-100'}>
                <Text>Picture limits</Text>
                <ContextualHelp variant={'info'} placement={'bottom right'}>
                    <Content>
                        <PictureLimitTooltip />
                    </Content>
                </ContextualHelp>
            </Flex>
        </View>
    );
};
