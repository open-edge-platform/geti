// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createI18nInstance } from '@/i18n';

import { formatRateLimit, toRateLimit } from './utils';

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

describe('toRateLimit', () => {
    it('returns null when samples or seconds are missing', () => {
        expect(toRateLimit(null, null)).toBeNull();
        expect(toRateLimit(null, 1)).toBeNull();
        expect(toRateLimit(1, null)).toBeNull();
    });

    it('returns null for NaN and non-finite values', () => {
        expect(toRateLimit(Number.NaN, 1)).toBeNull();
        expect(toRateLimit(1, Number.NaN)).toBeNull();
        expect(toRateLimit(Number.POSITIVE_INFINITY, 2)).toBeNull();
    });

    it('returns null for non-positive values', () => {
        expect(toRateLimit(0, 2)).toBeNull();
        expect(toRateLimit(-1, 2)).toBeNull();
        expect(toRateLimit(2, 0)).toBeNull();
        expect(toRateLimit(2, -1)).toBeNull();
    });

    it('returns samples per second for valid values', () => {
        expect(toRateLimit(10, 2)).toBe(5);
        expect(toRateLimit(5, 1)).toBe(5);
    });

    it('supports decimal values', () => {
        expect(toRateLimit(0.5, 1)).toBe(0.5);
        expect(toRateLimit(1, 0.5)).toBe(2);
    });
});
