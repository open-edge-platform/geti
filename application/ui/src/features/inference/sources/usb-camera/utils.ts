// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { USBCameraSourceConfig } from '@/api/types';
import type { TranslateFn } from '@/i18n';

import { getUniqueName } from '../utils';

export interface UsbCameraFormState extends Omit<USBCameraSourceConfig, 'device_id'> {
    device_id: number | null;
}

export const getUsbCameraInitialConfig = (t: TranslateFn, existingNames: string[] = []): UsbCameraFormState => ({
    id: '',
    name: getUniqueName(t('inference.sources.defaultNames.usbCamera'), existingNames),
    source_type: 'usb_camera',
    device_id: null,
});
