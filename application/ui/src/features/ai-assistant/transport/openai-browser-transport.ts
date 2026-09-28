// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { i18n } from '@/i18n';

import { AssistantConnectionError, AssistantStoppedError, type StreamRequest, type StreamResult } from '../types';
import { readStoredKey } from './key-service';
import { parseCompletedResponse } from './parse-response';
import { redactSecrets } from './redact';
import { consumeSse } from './sse';

const OPENAI_RESPONSES_URL = 'https://api.openai.com/v1/responses';
const OPENAI_MODELS_URL = 'https://api.openai.com/v1/models';
const KEY_VALIDATION_TIMEOUT_MS = 30_000;
const controllers = new Map<string, AbortController>();
let validatedKey: string | null = null;

const asRecord = (value: unknown): Record<string, unknown> =>
    typeof value === 'object' && value !== null ? (value as Record<string, unknown>) : {};

const errorMessage = async (response: Response): Promise<string> => {
    const body = await response.json().catch(() => null);
    const error = asRecord(asRecord(body).error);
    const message = typeof error.message === 'string' ? error.message : `OpenAI request failed (${response.status}).`;
    return redactSecrets(message);
};

const validateKey = async (key: string, signal: AbortSignal): Promise<void> => {
    if (validatedKey === key) return;

    const validation = new AbortController();
    const onOuterAbort = (): void => validation.abort();
    signal.addEventListener('abort', onOuterAbort, { once: true });

    let timer: ReturnType<typeof setTimeout> | undefined;
    try {
        const timeout = new Promise<never>((_resolve, reject) => {
            timer = setTimeout(() => {
                validation.abort();
                reject(new DOMException('The key check timed out.', 'TimeoutError'));
            }, KEY_VALIDATION_TIMEOUT_MS);
        });
        const response = await Promise.race([
            fetch(OPENAI_MODELS_URL, {
                headers: { authorization: `Bearer ${key}` },
                signal: validation.signal,
            }),
            timeout,
        ]);
        if (!response.ok) throw new AssistantConnectionError(await errorMessage(response));
        validatedKey = key;
    } finally {
        if (timer !== undefined) clearTimeout(timer);
        signal.removeEventListener('abort', onOuterAbort);
    }
};

export const streamResponseInBrowser = async (request: StreamRequest): Promise<StreamResult> => {
    const key = readStoredKey('openai-api-key');
    if (key === null || key.trim() === '') {
        throw new AssistantConnectionError(i18n.t('assistant.addOpenAiKey'));
    }
    const normalizedKey = key.trim();

    // The controller is registered before the key check so a Stop pressed
    // during validation also cancels the (paid) request that follows it.
    const controller = new AbortController();
    controllers.set(request.requestId, controller);
    let completed: unknown = null;
    let failure: string | null = null;
    let incompleteReason: string | null = null;

    try {
        try {
            await validateKey(normalizedKey, controller.signal);
        } catch (error) {
            if (controller.signal.aborted) throw new AssistantStoppedError();
            if (error instanceof AssistantConnectionError) throw error;
            throw new AssistantConnectionError(i18n.t('assistant.openAiKeyCheckFailed'));
        }

        const response = await fetch(OPENAI_RESPONSES_URL, {
            method: 'POST',
            signal: controller.signal,
            headers: {
                authorization: `Bearer ${normalizedKey}`,
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
        if (response.body === null) throw new Error(i18n.t('assistant.openAiEnded'));

        await consumeSse(response.body, (payload) => {
            if (payload === '[DONE]') return;
            let event: Record<string, unknown>;
            try {
                event = asRecord(JSON.parse(payload));
            } catch {
                // One malformed event must not discard the whole response.
                return;
            }
            if (event.type === 'response.output_text.delta' && typeof event.delta === 'string') {
                request.onDelta(event.delta);
            } else if (event.type === 'response.completed') {
                completed = event.response;
            } else if (event.type === 'response.incomplete') {
                const result = asRecord(event.response);
                incompleteReason =
                    typeof result.incomplete_reason === 'string' ? result.incomplete_reason : 'unknown reason';
            } else if (event.type === 'response.failed' || event.type === 'error') {
                const error = asRecord(event.error ?? asRecord(event.response).error);
                failure =
                    typeof error.message === 'string' ? error.message : i18n.t('assistant.openAiCouldNotComplete');
            }
        });

        if (failure !== null) throw new Error(redactSecrets(failure));
        if (completed === null) {
            if (incompleteReason !== null) {
                throw new Error(i18n.t('assistant.openAiEndedEarly', { reason: incompleteReason }));
            }
            throw new Error(i18n.t('assistant.openAiIncomplete'));
        }
        return parseCompletedResponse(completed);
    } catch (error) {
        if (controller.signal.aborted) throw new AssistantStoppedError();
        if (error instanceof TypeError) {
            // TypeError covers network failures, DNS and CSP blocks alike, so the
            // message must not blame the key or billing.
            throw new AssistantConnectionError(i18n.t('assistant.openAiUnreachable'));
        }
        throw error;
    } finally {
        controllers.delete(request.requestId);
    }
};

export const cancelResponseInBrowser = (requestId: string): void => controllers.get(requestId)?.abort();
