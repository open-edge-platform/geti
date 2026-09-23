// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createI18nInstance } from '@/i18n';

import { getJobStatusLabel, isInvalidStagedFile } from './util';

describe('getJobStatusLabel', () => {
    const instance = createI18nInstance({
        lng: 'en',
        resources: {
            en: {
                translation: {
                    common: {
                        status: {
                            pending: 'Localized pending',
                            running: 'Localized running',
                            done: 'Localized done',
                            failed: 'Localized failed',
                            cancelled: 'Localized cancelled',
                        },
                        labels: { unknown: 'Localized unknown' },
                    },
                },
            },
        },
    });

    it.each(['PENDING', 'RUNNING', 'DONE', 'FAILED', 'CANCELLED'])('translates %s at call time', (status) => {
        expect(getJobStatusLabel(status, instance.t)).toBe(`Localized ${status.toLowerCase()}`);
    });

    it('uses a translated fallback for unrecognized API states', () => {
        expect(getJobStatusLabel('NEW_STATE', instance.t)).toBe('Localized unknown');
    });
});

describe('isInvalidStagedFile', () => {
    it('returns true when detail starts with "Staged dataset" and ends with "not found"', () => {
        expect(isInvalidStagedFile({ detail: 'Staged dataset with ID abc-123 not found' })).toBe(true);
        expect(isInvalidStagedFile({ detail: 'Staged dataset not found' })).toBe(true);
        expect(isInvalidStagedFile({ detail: 'staged dataset with ID abc-123 not found.' })).toBe(true);
        expect(isInvalidStagedFile({ detail: ' Staged dataset not found ' })).toBe(true);
    });

    it('returns false when detail does not start with "Staged dataset"', () => {
        expect(isInvalidStagedFile({ detail: 'Resource not found' })).toBe(false);
        expect(isInvalidStagedFile({ detail: 'Staged file not found' })).toBe(false);
    });

    it('returns false when detail does not contain "not found"', () => {
        expect(isInvalidStagedFile({ detail: 'Staged dataset with ID abc-123 missing' })).toBe(false);
        expect(isInvalidStagedFile({ detail: 'Staged dataset' })).toBe(false);
    });
});
