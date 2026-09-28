// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { describe, expect, it } from 'vitest';

import { redactSecrets } from './redact';

describe('redactSecrets', () => {
    it('redacts OpenAI and Anthropic key fragments', () => {
        expect(redactSecrets('bad sk-ant-secret key')).toBe('bad *** key');
        expect(redactSecrets('bad sk-secret key')).toBe('bad *** key');
    });

    it('leaves ordinary hyphenated words alone', () => {
        expect(redactSecrets('task-42')).toBe('task-42');
    });
});
