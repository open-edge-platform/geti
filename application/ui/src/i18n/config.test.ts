// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { resolveLanguage } from './config';

describe('resolveLanguage', () => {
    it.each([
        ['zh', 'zh-CN'],
        ['zh-Hans', 'zh-CN'],
        ['zh-Hans-CN', 'zh-CN'],
        ['zh-SG', 'zh-CN'],
        ['zh-Hans-SG', 'zh-CN'],
        ['zh-MY', 'zh-CN'],
        ['zh-Hant', 'zh-TW'],
        ['zh-Hant-TW', 'zh-TW'],
        ['zh-Hant-HK', 'zh-HK'],
        ['zh-Hant-MO', 'zh-MO'],
    ])('merges %s via Intl.Locale maximize to %s', (input, expected) => {
        expect(resolveLanguage(input)).toBe(expected);
    });
});
