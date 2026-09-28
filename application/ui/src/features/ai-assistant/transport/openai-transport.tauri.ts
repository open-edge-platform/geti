// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { i18n } from '@/i18n';
import { Channel, invoke } from '@tauri-apps/api/core';

import { hasSecureAiBackend } from '../platform';
import { AssistantStoppedError, type StreamRequest, type StreamResult } from '../types';
import { cancelResponseInBrowser, streamResponseInBrowser } from './openai-browser-transport';
import { parseCompletedResponse } from './parse-response';

/** Mirrors `OpenAiEvent` in `src-tauri/src/assistant/api.rs`. */
type StreamEvent =
    | { type: 'delta'; text: string }
    | { type: 'completed'; response: unknown }
    | { type: 'failed'; message: string; status: number | null; code: string | null }
    | { type: 'cancelled' };

const streamViaTauri = async (request: StreamRequest): Promise<StreamResult> => {
    const channel = new Channel<StreamEvent>();

    let completed: unknown = null;
    let failure: string | null = null;
    let cancelled = false;

    channel.onmessage = (event) => {
        if (event.type === 'delta') {
            request.onDelta(event.text);
        } else if (event.type === 'completed') {
            completed = event.response;
        } else if (event.type === 'failed') {
            failure = event.message;
        } else {
            cancelled = true;
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

    if (cancelled) throw new AssistantStoppedError();
    if (failure !== null) {
        throw new Error(failure);
    }

    if (completed === null) {
        throw new Error(i18n.t('assistant.openAiIncomplete'));
    }

    return parseCompletedResponse(completed);
};

const cancelViaTauri = (requestId: string): void => {
    void invoke('openai_cancel', { requestId }).catch((error: unknown) => {
        console.error('[assistant] failed to cancel the OpenAI request', error);
    });
};

export const streamResponse = (request: StreamRequest): Promise<StreamResult> =>
    hasSecureAiBackend() ? streamViaTauri(request) : streamResponseInBrowser(request);

export const cancelResponse = (requestId: string): void =>
    hasSecureAiBackend() ? cancelViaTauri(requestId) : cancelResponseInBrowser(requestId);
