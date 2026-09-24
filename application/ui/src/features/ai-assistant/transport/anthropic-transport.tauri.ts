// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Channel, invoke } from '@tauri-apps/api/core';

import { hasSecureAiBackend } from '../platform';
import type { StreamRequest, StreamResult } from '../types';
import {
    AnthropicAssembler,
    buildAnthropicBody,
    cancelAnthropicInBrowser,
    streamAnthropicInBrowser,
} from './anthropic-browser-transport';

type NativeEvent = { type: 'sse'; data: string } | { type: 'failed'; message: string } | { type: 'cancelled' };

const streamViaTauri = async (request: StreamRequest): Promise<StreamResult> => {
    const channel = new Channel<NativeEvent>();
    const assembler = new AnthropicAssembler(request.onDelta);
    let failure: string | null = null;
    channel.onmessage = (event) => {
        if (event.type === 'sse') {
            try {
                assembler.accept(event.data);
            } catch {
                failure = 'Anthropic returned an invalid stream event.';
            }
        } else if (event.type === 'failed') {
            failure = event.message;
        } else {
            failure = 'Stopped.';
        }
    };
    await invoke('anthropic_messages_stream', {
        requestId: request.requestId,
        body: buildAnthropicBody(request),
        onEvent: channel,
    });
    if (failure !== null) throw new Error(failure);
    if (assembler.error !== null) throw new Error(assembler.error);
    if (!assembler.done) throw new Error('Anthropic did not return a completed response.');
    return assembler.result();
};

const cancelViaTauri = (requestId: string): void => {
    void invoke('anthropic_cancel', { requestId }).catch((error: unknown) => {
        console.error('[assistant] failed to cancel the Anthropic request', error);
    });
};

export const streamAnthropicResponse = (request: StreamRequest): Promise<StreamResult> =>
    hasSecureAiBackend() ? streamViaTauri(request) : streamAnthropicInBrowser(request);

export const cancelAnthropicResponse = (requestId: string): void =>
    hasSecureAiBackend() ? cancelViaTauri(requestId) : cancelAnthropicInBrowser(requestId);
