// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { StreamRequest } from '../types';
import { streamResponseInBrowser } from './openai-browser-transport';

const request: StreamRequest = {
    requestId: 'request-1',
    model: 'gpt-4.1',
    instructions: 'Annotate.',
    input: [],
    tools: [],
    onDelta: vi.fn(),
};

it('explains opaque browser failures from the OpenAI API', async () => {
    localStorage.setItem('geti.ai-assistant.credential.openai-api-key', 'sk-test');
    vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new TypeError('Failed to fetch'));

    await expect(streamResponseInBrowser(request)).rejects.toThrow(
        'Verify the API key and API billing, or use the Anthropic API or Windows app.'
    );
});
