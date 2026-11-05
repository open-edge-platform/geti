// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { IPCameraSourceConfig } from '@/api/types';
import type { TranslateFn } from '@/i18n';

import { getUniqueName } from '../utils';

export type IpCameraFormState = Omit<IPCameraSourceConfig, 'id'>;

export const getIpCameraInitialConfig = (t: TranslateFn, existingNames: string[] = []): IpCameraFormState => ({
    name: getUniqueName(t('inference.sources.defaultNames.ipCamera'), existingNames),
    source_type: 'ip_camera',
    stream_url: '',
    auth_required: false,
});
