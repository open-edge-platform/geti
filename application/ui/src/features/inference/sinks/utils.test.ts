// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createI18nInstance } from '@/i18n';

import { formatRateLimit } from './utils';

describe('formatRateLimit', () => {
    const { t } = createI18nInstance({ lng: 'en' });

    it('returns "Not set" for nullish or non-positive values', () => {
        expect(formatRateLimit(undefined, t)).toBe('Not set');
        expect(formatRateLimit(null, t)).toBe('Not set');
        expect(formatRateLimit(0, t)).toBe('Not set');
        expect(formatRateLimit(Number.NaN, t)).toBe('Not set');
    });

    it('formats singular sample and second labels', () => {
        expect(formatRateLimit(1, t)).toBe('1 sample every 1 second');
    });

    it('formats plural samples for rates above one', () => {
        expect(formatRateLimit(2, t)).toBe('2 samples every 1 second');
    });

    it('formats rates below one as canonical ratio', () => {
        expect(formatRateLimit(0.5, t)).toBe('1 sample every 2 seconds');
    });
});
