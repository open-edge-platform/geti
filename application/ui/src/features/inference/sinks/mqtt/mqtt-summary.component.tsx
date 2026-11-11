// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { MqttSinkConfig } from '@/api/types';
import { useTranslation } from '@/i18n';

import { OutputFormatsList } from '../sink-list/sinks-details/output-formats-list.component';
import { formatRateLimit } from '../utils';

interface MqttSummaryProps {
    sink: MqttSinkConfig;
}

export const MqttSummary = ({ sink }: MqttSummaryProps) => {
    const { t } = useTranslation();
    const authRequiredValue = sink.auth_required ? t('common.labels.yes') : t('common.labels.no');

    return (
        <>
            <li>{t('inference.sinks.settings.topic', { value: sink.topic })}</li>
            <li>{t('inference.sinks.settings.rateLimit', { value: formatRateLimit(sink.rate_limit, t) })}</li>
            <li>{t('inference.settings.authRequired', { value: authRequiredValue })}</li>
            <li>{t('inference.sinks.settings.brokerHost', { value: sink.broker_host })}</li>
            <li>{t('inference.sinks.settings.brokerPort', { value: sink.broker_port })}</li>
            <OutputFormatsList outputFormats={sink.output_formats} />
        </>
    );
};
