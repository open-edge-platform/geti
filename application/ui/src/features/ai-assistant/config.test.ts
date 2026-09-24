// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
    ANTHROPIC_DEFAULT_MODEL,
    ANTHROPIC_MODEL_GROUPS,
    groupModelIds,
    OPENAI_DEFAULT_MODEL,
    OPENAI_MODEL_GROUPS,
    OPENAI_MODELS,
} from './config';

it('offers current vision models grouped by family', () => {
    expect(OPENAI_DEFAULT_MODEL).toBe('gpt-6-sol');
    expect(ANTHROPIC_DEFAULT_MODEL).toBe('claude-sonnet-5');
    expect(OPENAI_MODELS).toContain('gpt-6-astra');
    expect(OPENAI_MODEL_GROUPS.at(-1)?.label).toBe('Legacy API models');
    expect(ANTHROPIC_MODEL_GROUPS[0].models).toContain('claude-opus-5-5');
});

it('groups native app model IDs into readable families', () => {
    expect(groupModelIds(['gpt-6-sol', 'gpt-5.6-sol', 'other-model'])).toEqual([
        { label: 'GPT-6', models: ['gpt-6-sol'] },
        { label: 'GPT-5.6', models: ['gpt-5.6-sol'] },
        { label: 'Other models', models: ['other-model'] },
    ]);
});
