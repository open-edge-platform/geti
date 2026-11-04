// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { IPCameraSourceConfig } from '@/api/types';
import { useTranslation } from '@/i18n';

interface IpCameraSummaryProps {
    source: IPCameraSourceConfig;
}

export const IpCameraSummary = ({ source }: IpCameraSummaryProps) => {
    const { t } = useTranslation();
    const authRequiredValue = source.auth_required ? t('common.labels.yes') : t('common.labels.no');

    return (
        <>
            <li>{t('inference.sources.settings.streamUrl', { url: source.stream_url })}</li>
            <li>{t('inference.settings.authRequired', { value: authRequiredValue })}</li>
        </>
    );
};
