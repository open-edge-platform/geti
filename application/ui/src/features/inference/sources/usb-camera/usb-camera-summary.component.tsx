// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import type { USBCameraSourceConfig } from '@/api/types';
import { useTranslation } from '@/i18n';

interface UsbCameraSummaryProps {
    source: USBCameraSourceConfig;
}

export const UsbCameraSummary = ({ source }: UsbCameraSummaryProps) => {
    const { t } = useTranslation();
    const { data: cameraDevices = [], isLoading } = $api.useQuery('get', '/api/system/devices/camera');
    const device = cameraDevices.find(({ index }) => index === source.device_id);

    if (isLoading) {
        return <li>{t('inference.sources.settings.loading')}</li>;
    }

    const deviceLabel = device
        ? device.name
        : t('inference.sources.settings.unknownDevice', { deviceId: source.device_id });

    return <li>{t('inference.sources.settings.device', { name: deviceLabel })}</li>;
};
