// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { i18n, type TranslateFn } from '@/i18n';
import dayjs from 'dayjs';

// Kept in a fixed, locale-independent format because it also feeds app-owned ARIA labels.
export const formatFilterDate = (date: string): string => dayjs(date).format('DD/MM/YYYY HH:mm');

export const formatDateTime = (
    dateString: string | null | undefined,
    fallback = '-',
    locale = i18n.resolvedLanguage ?? i18n.language
): string => {
    if (!dateString) return fallback;

    const date = dayjs(dateString);

    return date.isValid()
        ? new Intl.DateTimeFormat(locale, {
              day: '2-digit',
              month: 'short',
              year: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
          }).format(date.toDate())
        : fallback;
};

export const formatDateRangeStart = (date: string, t: TranslateFn): string =>
    t('dataset.filters.dateRange.from', { date: formatDateTime(date) });

export const formatDateRangeEnd = (date: string, t: TranslateFn): string =>
    t('dataset.filters.dateRange.to', { date: formatDateTime(date) });

export const formatTrainingDateTime = (
    dateString: string | null | undefined,
    locale = i18n.resolvedLanguage ?? i18n.language
): string => {
    if (!dateString) return '-';

    const date = dayjs(dateString);

    if (!date.isValid()) return '-';

    const dateLabel = new Intl.DateTimeFormat(locale, {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
    }).format(date.toDate());
    const timeLabel = new Intl.DateTimeFormat(locale, { hour: '2-digit', minute: '2-digit' }).format(date.toDate());

    return `${dateLabel}\n${timeLabel}`;
};
