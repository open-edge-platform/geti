// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
