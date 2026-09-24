// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createI18nInstance } from '@/i18n';

import {
    formatDateRangeEnd,
    formatDateRangeStart,
    formatDateTime,
    formatFilterDate,
    formatTrainingDateTime,
} from './date-utils';

// Dates are formatted in the local timezone, so the inputs are built from local time components
const localISOString = (year: number, month: number, day: number, hours = 0, minutes = 0) =>
    new Date(year, month - 1, day, hours, minutes).toISOString();

describe('date-utils', () => {
    const { t } = createI18nInstance({ lng: 'en' });

    describe('formatFilterDate', () => {
        it('keeps a fixed 24 hour format for app-owned ARIA labels', () => {
            expect(formatFilterDate(localISOString(2026, 12, 31, 23, 59))).toBe('31/12/2026 23:59');
        });
    });

    describe('formatDateRangeStart', () => {
        it('formats the start of a range in the active language', () => {
            expect(formatDateRangeStart(localISOString(2026, 1, 1), t)).toBe('From Jan 01, 2026, 12:00 AM');
        });
    });

    describe('formatDateRangeEnd', () => {
        it('formats the end of a range in the active language', () => {
            expect(formatDateRangeEnd(localISOString(2026, 1, 31, 23, 59), t)).toBe('To Jan 31, 2026, 11:59 PM');
        });
    });

    describe('formatDateTime', () => {
        it('formats a date and time', () => {
            expect(formatDateTime(localISOString(2025, 10, 1, 11, 7), '-', 'en-US')).toBe('Oct 01, 2025, 11:07 AM');
        });

        it('localizes month names and the time convention', () => {
            expect(formatDateTime(localISOString(2025, 10, 1, 23, 7), '-', 'fr-FR')).toBe('01 oct. 2025, 23:07');
        });

        it.each([null, undefined, ''])('returns the fallback for %p', (date) => {
            expect(formatDateTime(date)).toBe('-');
        });

        it('returns the fallback for an unparsable date', () => {
            expect(formatDateTime('not a date')).toBe('-');
        });

        it('returns a custom fallback', () => {
            expect(formatDateTime(null, 'N/A')).toBe('N/A');
        });
    });

    describe('formatTrainingDateTime', () => {
        it('puts the time on a second line', () => {
            expect(formatTrainingDateTime(localISOString(2025, 10, 1, 11, 7), 'en-US')).toBe('Oct 01, 2025\n11:07 AM');
        });

        it('localizes both lines', () => {
            expect(formatTrainingDateTime(localISOString(2025, 10, 1, 23, 7), 'fr-FR')).toBe('01 oct. 2025\n23:07');
        });

        it.each([null, undefined, '', 'not a date'])('returns a placeholder for %p', (date) => {
            expect(formatTrainingDateTime(date)).toBe('-');
        });
    });
});
