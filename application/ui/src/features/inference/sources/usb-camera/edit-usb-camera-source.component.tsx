// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { USBCameraSourceConfig } from '@/api/types';

import { EditSource } from '../deprecated/edit-source/edit-source.component';
import { UsbCamera } from '../deprecated/usb-camera/usb-camera-fields.component';
import { usbCameraBodyFormatter } from '../deprecated/usb-camera/utils';
import type { EditSourceProps } from '../types';

export const EditUsbCameraSource = ({
    source,
    isConnected,
    onSaved,
    onBackToList,
}: EditSourceProps<USBCameraSourceConfig>) => (
    <EditSource
        config={source}
        isConnected={isConnected}
        onSaved={onSaved}
        onBackToList={onBackToList}
        componentFields={(state) => <UsbCamera defaultState={state} />}
        bodyFormatter={usbCameraBodyFormatter}
    />
);
