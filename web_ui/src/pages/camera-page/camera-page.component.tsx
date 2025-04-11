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

import { Flex, Grid, Heading, Text, View } from '@adobe/react-spectrum';

import { NOTIFICATION_TYPE } from '../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../notification/notification.component';
import { getEstimateFreeStorage } from '../../shared/navigator-utils';
import { UserCameraPermission } from '../camera-support/camera.interface';
import { ActionButtons } from './components/action-buttons/action-buttons.component';
import { CameraFactory } from './components/camera-factory.component';
import { useDeviceSettings } from './providers/device-settings-provider.component';
import { hasPermissionsDenied, TOO_LOW_FREE_STORAGE_IN_BYTES, TOO_LOW_FREE_STORAGE_MESSAGE } from './util';

const COLUMNS = ['auto'];
const GRID_AREAS = ['header', 'content'];
const ROWS = ['size-800', 'calc(100% - size-800)'];

const useLowStorage = () => {
    const { addNotification } = useNotification();

    getEstimateFreeStorage().then((estimateFreeStorage) => {
        if (estimateFreeStorage <= TOO_LOW_FREE_STORAGE_IN_BYTES) {
            addNotification({
                message: TOO_LOW_FREE_STORAGE_MESSAGE,
                type: NOTIFICATION_TYPE.WARNING,
                dismiss: { duration: 0 },
            });
        }
    });
};

export const CameraPage = (): JSX.Element => {
    const { userPermissions } = useDeviceSettings();

    useLowStorage();

    const isPermissionDenied = hasPermissionsDenied(userPermissions);
    const isPermissionPending = userPermissions === UserCameraPermission.PENDING;

    return (
        <View padding={'size-250'} backgroundColor={'gray-75'}>
            <Grid areas={GRID_AREAS} rows={ROWS} columns={COLUMNS} height={'calc(100vh - size-500)'}>
                <Flex gridArea={'header'} direction={'row'} justifyContent={'space-between'}>
                    <Flex direction={'column'}>
                        <Heading level={6} UNSAFE_style={{ fontWeight: '700' }} margin={0}>
                            Camera Upload
                        </Heading>
                        <Text>Capture images with your camera</Text>
                    </Flex>
                    <ActionButtons isDisabled={isPermissionDenied || isPermissionPending} />
                </Flex>

                <CameraFactory isPermissionDenied={isPermissionDenied} isPermissionPending={isPermissionPending} />
            </Grid>
        </View>
    );
};
