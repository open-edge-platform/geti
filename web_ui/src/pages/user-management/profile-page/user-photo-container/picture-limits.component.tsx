// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
