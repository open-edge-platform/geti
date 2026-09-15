// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Channel, invoke } from '@tauri-apps/api/core';

import type { StreamRequest, StreamResult } from '../types';
import { parseCompletedResponse } from './parse-response';

/** Mirrors `StreamEvent` in `src-tauri/src/assistant/openai.rs`. */
type StreamEvent =
    | { type: 'delta'; text: string }
    | { type: 'completed'; response: unknown }
    | { type: 'failed'; message: string; status: number | null; code: string | null };

export const streamResponse = async (request: StreamRequest): Promise<StreamResult> => {
    const channel = new Channel<StreamEvent>();

    let completed: unknown = null;
    let failure: string | null = null;

    channel.onmessage = (event) => {
        if (event.type === 'delta') {
            request.onDelta(event.text);
        } else if (event.type === 'completed') {
            completed = event.response;
        } else {
            failure = event.message;
        }
    };

    // The command resolves once the shell has finished draining the SSE stream,
    // so every channel message has already been delivered by this point.
    await invoke('openai_responses_stream', {
        requestId: request.requestId,
        body: {
            model: request.model,
            instructions: request.instructions,
            input: request.input,
            tools: request.tools,
            // Nothing about a user's project should be retained by OpenAI.
            store: false,
        },
        onEvent: channel,
    });

    if (failure !== null) {
        throw new Error(failure);
    }

    if (completed === null) {
        throw new Error('OpenAI did not return a response.');
    }

    return parseCompletedResponse(completed);
};

export const cancelResponse = (requestId: string): void => {
    void invoke('openai_cancel', { requestId }).catch((error: unknown) => {
        console.error('[assistant] failed to cancel the OpenAI request', error);
    });
};
