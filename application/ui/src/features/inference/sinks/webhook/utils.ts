// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { WebhookSinkConfig } from '@/api/types';
import type { TranslateFn } from '@/i18n';

export enum WebhookHttpMethod {
    PUT = 'PUT',
    POST = 'POST',
    PATCH = 'PATCH',
}

export type HeaderRow = {
    key: string;
    value: string;
};

// Headers are edited as an array of rows (duplicates and empty keys are possible while typing) and
// converted to the API's object only when the request body is built.
export type WebhookFormState = Omit<WebhookSinkConfig, 'headers'> & {
    headers: HeaderRow[];
};

const BACKEND_DEFAULT_TIMEOUT = 10;

export const headersToRows = (headers: Record<string, string> | null | undefined): HeaderRow[] =>
    Object.entries(headers ?? {}).map(([key, value]) => ({ key, value }));

export const rowsToHeaders = (rows: HeaderRow[]): Record<string, string> =>
    Object.fromEntries(rows.filter(({ key }) => key.trim().length > 0).map(({ key, value }) => [key.trim(), value]));

// Indexes of rows whose (trimmed, non-empty) key already appeared in an earlier row.
export const getDuplicateKeyIndexes = (rows: HeaderRow[]): Set<number> => {
    const seen = new Set<string>();
    const duplicates = new Set<number>();

    rows.forEach(({ key }, index) => {
        const trimmed = key.trim();

        if (trimmed.length === 0) return;

        if (seen.has(trimmed)) {
            duplicates.add(index);
        }

        seen.add(trimmed);
    });

    return duplicates;
};

export const getWebhookInitialConfig = (t: TranslateFn): WebhookFormState => ({
    id: '',
    name: t('inference.sinks.defaultNames.webhook'),
    sink_type: 'webhook',
    webhook_url: '',
    http_method: WebhookHttpMethod.POST,
    timeout: BACKEND_DEFAULT_TIMEOUT,
    headers: [],
    rate_limit: null,
    output_formats: [],
});

export const toWebhookFormState = (sink: WebhookSinkConfig): WebhookFormState => ({
    ...sink,
    headers: headersToRows(sink.headers),
});

export const toWebhookBody = (config: WebhookFormState): Omit<WebhookSinkConfig, 'id' | 'sink_type'> => ({
    name: config.name,
    webhook_url: config.webhook_url,
    http_method: config.http_method,
    timeout: config.timeout,
    headers: rowsToHeaders(config.headers),
    rate_limit: config.rate_limit,
    output_formats: config.output_formats,
});

export const isWebhookConfigValid = ({ webhook_url, headers, output_formats }: WebhookFormState): boolean =>
    webhook_url.trim().length > 0 &&
    output_formats.length > 0 &&
    headers.every(({ key, value }) => key.trim().length > 0 && value.length > 0) &&
    getDuplicateKeyIndexes(headers).size === 0;
