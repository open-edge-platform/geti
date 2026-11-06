// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { WebhookSinkConfig } from '@/api/types';
import { useTranslation } from '@/i18n';

import { OutputFormatsList } from '../sink-list/sinks-details/output-formats-list.component';
import { formatRateLimit } from '../utils';

interface WebhookSummaryProps {
    sink: WebhookSinkConfig;
}

export const WebhookSummary = ({ sink }: WebhookSummaryProps) => {
    const { t } = useTranslation();

    return (
        <>
            <li>{t('inference.sinks.settings.rateLimit', { value: formatRateLimit(sink.rate_limit, t) })}</li>
            <li>{t('inference.sinks.settings.httpMethod', { value: sink.http_method })}</li>
            <li>{t('inference.sinks.settings.timeout', { value: sink.timeout })}</li>
            <li>{t('inference.sinks.settings.webhookUrl', { value: sink.webhook_url })}</li>
            <li>
                {t('inference.sinks.fields.headers')}
                <ul>
                    {Object.entries(sink.headers ?? {}).map(([key, value]) => (
                        <li key={key}>
                            {key}: {value}
                        </li>
                    ))}
                </ul>
            </li>
            <OutputFormatsList outputFormats={sink.output_formats} />
        </>
    );
};
