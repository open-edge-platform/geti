// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect } from 'react';

import { Flex, Heading, Text } from '@adobe/react-spectrum';
import { dimensionValue } from '@react-spectrum/utils';

import { NOTIFICATION_TYPE } from '../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../notification/notification.component';

export const PermissionError = (): JSX.Element => {
    const { addToastNotification } = useNotification();

    useEffect(() => {
        addToastNotification({
            title: 'Camera connection is lost',
            message: 'Please check your device and network settings and try again.',
            type: NOTIFICATION_TYPE.WARNING,
        });
    }, [addToastNotification]);

    return (
        <Flex gridArea={'content'} UNSAFE_style={{ background: 'var(--spectrum-global-color-gray-50)' }}>
            <Flex margin={'size-250'} flexGrow={1} direction={'column'} alignItems={'center'} justifyContent={'center'}>
                <Heading level={2} margin={0} UNSAFE_style={{ fontSize: dimensionValue('size-450') }}>
                    Camera connection is lost
                </Heading>
                <Text>Please check your device and network settings and try again.</Text>
            </Flex>
        </Flex>
    );
};
