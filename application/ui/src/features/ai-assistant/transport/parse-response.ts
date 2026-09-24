// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { FunctionCall, StreamResult } from '../types';

/** Message shown when a desktop-only transport is reached from the web build. */
export const DESKTOP_ONLY_MESSAGE = 'The Geti assistant is only available in the desktop application.';

const asRecord = (value: unknown): Record<string, unknown> =>
    typeof value === 'object' && value !== null ? (value as Record<string, unknown>) : {};

/**
 * Extracts the assistant text and the requested function calls from a completed
 * OpenAI Responses API payload.
 */
export const parseCompletedResponse = (response: unknown): StreamResult => {
    const output = asRecord(response).output;
    const items = Array.isArray(output) ? output : [];

    const texts: string[] = [];
    const functionCalls: FunctionCall[] = [];

    items.forEach((rawItem) => {
        const item = asRecord(rawItem);

        if (item.type === 'function_call') {
            functionCalls.push({
                callId: String(item.call_id ?? ''),
                name: String(item.name ?? ''),
                arguments: typeof item.arguments === 'string' ? item.arguments : '{}',
            });
            return;
        }

        if (item.type !== 'message' || !Array.isArray(item.content)) {
            return;
        }

        item.content.forEach((rawPart) => {
            const part = asRecord(rawPart);

            if (part.type === 'output_text' && typeof part.text === 'string') {
                texts.push(part.text);
            }
        });
    });

    return { text: texts.join(''), functionCalls: functionCalls.filter((call) => call.name !== '') };
};

/**
 * Normalises the `{ text, calls }` structured output of the ChatGPT (Codex)
 * transport into the same shape the API transport returns.
 */
export const parseCodexResult = (result: unknown): StreamResult => {
    const payload = asRecord(result);
    const calls = Array.isArray(payload.calls) ? payload.calls : [];

    return {
        text: typeof payload.text === 'string' ? payload.text : '',
        functionCalls: calls
            .map((rawCall, index): FunctionCall => {
                const call = asRecord(rawCall);

                return {
                    // Codex does not mint call ids; the transcript only needs
                    // them to pair a call with its output within one turn.
                    callId: `codex_${index}`,
                    name: String(call.name ?? ''),
                    arguments: typeof call.arguments === 'string' ? call.arguments : '{}',
                };
            })
            .filter((call) => call.name !== ''),
    };
};
