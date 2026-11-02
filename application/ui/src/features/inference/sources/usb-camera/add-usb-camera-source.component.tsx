// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from '@/i18n';

import { AddSource } from '../deprecated/add-source/add-source.component';
import { UsbCamera } from '../deprecated/usb-camera/usb-camera-fields.component';
import { getUsbCameraInitialConfig, usbCameraBodyFormatter } from '../deprecated/usb-camera/utils';
import type { AddSourceProps } from '../types';

export const AddUsbCameraSource = ({ existingNames, onSaved }: AddSourceProps) => {
    const { t } = useTranslation();

    return (
        <AddSource
            onSaved={onSaved}
            config={getUsbCameraInitialConfig(t, existingNames)}
            componentFields={(state) => <UsbCamera defaultState={state} />}
            bodyFormatter={usbCameraBodyFormatter}
        />
    );
};
