// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Text, View, type ViewProps } from '@geti/ui';
import { isEmpty } from 'lodash-es';

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
