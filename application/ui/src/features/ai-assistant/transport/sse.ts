// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { i18n } from '@/i18n';

const DEFAULT_IDLE_TIMEOUT_MS = 180_000;
const DEFAULT_MAX_BYTES = 32 * 1024 * 1024;

export interface ConsumeSseOptions {
    /** Abort the stream when no data arrives for this long. */
    idleTimeoutMs?: number;
    /** Abort the stream once this many bytes have been received. */
    maxBytes?: number;
}

/**
 * Reads an SSE stream to completion. Mirrors the limits the desktop shell
 * enforces, so a stalled or oversized provider response can never leave the
 * UI waiting forever.
 */
export const consumeSse = async (
    body: ReadableStream<Uint8Array>,
    onData: (payload: string) => void,
    options: ConsumeSseOptions = {}
): Promise<void> => {
    const idleTimeoutMs = options.idleTimeoutMs ?? DEFAULT_IDLE_TIMEOUT_MS;
    const maxBytes = options.maxBytes ?? DEFAULT_MAX_BYTES;
    const reader = body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let receivedBytes = 0;
    let idleTimer: ReturnType<typeof setTimeout> | undefined;
    let timedOut = false;

    // Per the SSE spec, several `data:` lines of one event form a single
    // field joined with newlines.
    const emitEvent = (event: string): void => {
        const data = event
            .split(/\r?\n/)
            .filter((line) => line.startsWith('data:'))
            .map((line) => line.slice(5).replace(/^ /, ''))
            .join('\n');
        if (data !== '') onData(data);
    };

    const resetIdleTimer = (): void => {
        if (idleTimer !== undefined) clearTimeout(idleTimer);
        idleTimer = setTimeout(() => {
            timedOut = true;
            void reader.cancel().catch(() => undefined);
        }, idleTimeoutMs);
    };

    try {
        for (;;) {
            resetIdleTimer();
            const { done, value } = await reader.read();

            if (value !== undefined) {
                receivedBytes += value.byteLength;
                if (receivedBytes > maxBytes) {
                    throw new Error(i18n.t('assistant.providerResponseTooLarge'));
                }
            }
            buffer += decoder.decode(value ?? new Uint8Array(0), { stream: !done });

            let boundary: RegExpExecArray | null;
            while ((boundary = /\r?\n\r?\n/.exec(buffer)) !== null) {
                emitEvent(buffer.slice(0, boundary.index));
                buffer = buffer.slice(boundary.index + boundary[0].length);
            }

            if (done) break;
        }

        // A final event without the trailing blank line would be silently dropped otherwise.
        if (buffer.trim() !== '') emitEvent(buffer);
    } finally {
        if (idleTimer !== undefined) clearTimeout(idleTimer);
        void reader.cancel().catch(() => undefined);
    }

    if (timedOut) {
        throw new Error(i18n.t('assistant.providerStopped'));
    }
};
