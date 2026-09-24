// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { StreamRequest, StreamResult } from '../types';
import { readStoredKey } from './key-service';
import { parseCompletedResponse } from './parse-response';
import { consumeSse } from './sse';

const OPENAI_RESPONSES_URL = 'https://api.openai.com/v1/responses';
const controllers = new Map<string, AbortController>();

const asRecord = (value: unknown): Record<string, unknown> =>
    typeof value === 'object' && value !== null ? (value as Record<string, unknown>) : {};

const errorMessage = async (response: Response): Promise<string> => {
    const body = await response.json().catch(() => null);
    const error = asRecord(asRecord(body).error);
    const message = typeof error.message === 'string' ? error.message : `OpenAI request failed (${response.status}).`;
    return message.replace(/sk-[A-Za-z0-9_-]+/g, '***');
};

export const streamResponseInBrowser = async (request: StreamRequest): Promise<StreamResult> => {
    const key = readStoredKey('openai-api-key');
    if (key === null || key.trim() === '') throw new Error('Add an OpenAI API key to continue.');

    const controller = new AbortController();
    controllers.set(request.requestId, controller);
    let completed: unknown = null;
    let failure: string | null = null;

    try {
        const response = await fetch(OPENAI_RESPONSES_URL, {
            method: 'POST',
            signal: controller.signal,
            headers: {
                authorization: `Bearer ${key.trim()}`,
                'content-type': 'application/json',
                accept: 'text/event-stream',
            },
            body: JSON.stringify({
                model: request.model,
                instructions: request.instructions,
                input: request.input,
                tools: request.tools,
                stream: true,
                store: false,
            }),
        });

        if (!response.ok) throw new Error(await errorMessage(response));
        if (response.body === null) throw new Error('OpenAI ended the response unexpectedly.');

        await consumeSse(response.body, (payload) => {
            if (payload === '[DONE]') return;
            const event = asRecord(JSON.parse(payload));
            if (event.type === 'response.output_text.delta' && typeof event.delta === 'string') {
                request.onDelta(event.delta);
            } else if (event.type === 'response.completed') {
                completed = event.response;
            } else if (event.type === 'response.failed' || event.type === 'error') {
                const error = asRecord(event.error ?? asRecord(event.response).error);
                failure = typeof error.message === 'string' ? error.message : 'OpenAI could not complete the response.';
            }
        });

        if (failure !== null) throw new Error(failure);
        if (completed === null) throw new Error('OpenAI did not return a completed response.');
        return parseCompletedResponse(completed);
    } catch (error) {
        if (controller.signal.aborted) throw new Error('Stopped.');
        throw error;
    } finally {
        controllers.delete(request.requestId);
    }
};

export const cancelResponseInBrowser = (requestId: string): void => controllers.get(requestId)?.abort();
