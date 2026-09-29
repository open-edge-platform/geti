// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createI18nInstance } from '@/i18n';

import { generateUniqueProjectName } from './utils';

describe('generateUniqueProjectName', () => {
    const { t } = createI18nInstance({ lng: 'en' });

    it('returns "Project #1" when list is empty', () => {
        const result = generateUniqueProjectName([], t);
        expect(result).toBe('Project #1');
    });

    it('increments the highest existing project number', () => {
        const result = generateUniqueProjectName(['Project #1', 'Project #2'], t);
        expect(result).toBe('Project #3');
    });

    it('ignores non-matching names', () => {
        const result = generateUniqueProjectName(['Alpha', 'Beta'], t);
        expect(result).toBe('Project #1');
    });

    it('picks the first number that is not taken', () => {
        const result = generateUniqueProjectName(['Project #1', 'Alpha', 'Project #3'], t);
        expect(result).toBe('Project #2');
    });

    it('handles duplicate numbers correctly', () => {
        const result = generateUniqueProjectName(['Project #1', 'Project #2', 'Project #2'], t);
        expect(result).toBe('Project #3');
    });

    it('handles large numbers', () => {
        const existingNames = Array.from({ length: 999 }, (_, index) => `Project #${index + 1}`);
        const result = generateUniqueProjectName(existingNames, t);
        expect(result).toBe('Project #1000');
    });

    it('stays unique when the default name is localized', () => {
        const { t: localizedT } = createI18nInstance({
            lng: 'zh-TW',
            supportedLngs: ['zh-TW'],
            resources: {
                'zh-TW': { translation: { project: { create: { defaultName: '專案 #{{number}}' } } } },
            },
        });

        const result = generateUniqueProjectName(['專案 #1', '專案 #2'], localizedT);
        expect(result).toBe('專案 #3');
    });
});
