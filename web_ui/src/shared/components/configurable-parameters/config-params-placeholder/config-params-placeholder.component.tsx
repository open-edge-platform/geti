// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex } from '@adobe/react-spectrum';

import { Skeleton } from '../../skeleton/skeleton.component';

export const ConfigParamsPlaceholder = (): JSX.Element => {
    return (
        <Flex width={'100%'} height={'100%'} gap={32} data-testid={'config-params-placeholder-id'}>
            <Flex flex={1} direction='column' gap={16}>
                <Skeleton UNSAFE_style={{ height: 50, width: '40%' }} />
                <Skeleton UNSAFE_style={{ height: 50, width: '40%' }} />
                <Skeleton UNSAFE_style={{ height: 50, width: '40%' }} />
            </Flex>
            <div
                style={{
                    width: 1,
                    background: 'var(--spectrum-global-color-gray-200)',
                    height: 400,
                    alignSelf: 'flex-start',
                }}
            />
            <Flex flex={2} direction='column' gap={20}>
                <Skeleton UNSAFE_style={{ height: 100, width: '100%' }} />
                <Skeleton UNSAFE_style={{ height: 100, width: '100%' }} />
                <Skeleton UNSAFE_style={{ height: 100, width: '100%' }} />
            </Flex>
        </Flex>
    );
};
