// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Channel, invoke } from '@tauri-apps/api/core';
import { openUrl } from '@tauri-apps/plugin-opener';

import { getAiConnection } from '../connection';
import type { CodexAccount, CodexModel, StreamRequest, StreamResult } from '../types';
import { parseCodexResult } from './parse-response';

type CodexEvent = { type: 'login'; url: string };

const newRequestId = (): string => crypto.randomUUID();

const asRecord = (value: unknown): Record<string, unknown> =>
    typeof value === 'object' && value !== null ? (value as Record<string, unknown>) : {};

const run = (operation: string, body: unknown, onEvent: Channel<CodexEvent>): Promise<unknown> => {
    return invoke('codex_operation', {
        requestId: newRequestId(),
        operation,
        executable: getAiConnection().executable || null,
        body,
        onEvent,
    });
};

/** Resolves to `null` when no ChatGPT account is signed in. */
export const codexStatus = async (): Promise<CodexAccount | null> => {
    const result = asRecord(await run('status', null, new Channel<CodexEvent>()));
    const account = asRecord(result.account ?? result);

    const email = typeof account.email === 'string' ? account.email : null;
    const plan = typeof account.planType === 'string' ? account.planType : null;

    if (email === null && account.authenticated !== true && result.authenticated !== true) {
        return null;
    }

    return { email, plan };
};

export const codexLogin = async (onUrl: (url: string) => void): Promise<void> => {
    const channel = new Channel<CodexEvent>();

    channel.onmessage = (event) => {
        if (event.type !== 'login') {
            return;
        }

        onUrl(event.url);
        // Rejects when the URL is missing from the `opener:allow-open-url`
        // allowlist in src-tauri/capabilities/default.json.
        void openUrl(event.url).catch((error: unknown) => {
            console.error('[assistant] failed to open the ChatGPT sign-in page', error);
        });
    };

    await run('login', null, channel);
};

export const codexLogout = async (): Promise<void> => {
    await run('logout', null, new Channel<CodexEvent>());
};

/** Models the signed-in account may use, text+image capable ones first. */
export const codexModels = async (): Promise<CodexModel[]> => {
    const result = asRecord(await run('models', null, new Channel<CodexEvent>()));
    const entries = Array.isArray(result.data) ? result.data : [];

    return entries
        .map((entry) => {
            const model = asRecord(entry);
            const id = typeof model.id === 'string' ? model.id : typeof model.model === 'string' ? model.model : '';
            const label = typeof model.displayName === 'string' && model.displayName !== '' ? model.displayName : id;

            return { id, label };
        })
        .filter((model) => model.id !== '');
};

export const codexRespond = async (request: StreamRequest): Promise<StreamResult> => {
    const channel = new Channel<CodexEvent>();

    const result = await invoke('codex_operation', {
        requestId: request.requestId,
        operation: 'response',
        executable: getAiConnection().executable || null,
        body: {
            model: request.model === '' ? null : request.model,
            instructions: request.instructions,
            input: request.input,
            tools: request.tools,
        },
        onEvent: channel,
    });

    const parsed = parseCodexResult(result);

    // Codex answers a turn in one piece rather than token by token, so the
    // caller gets a single delta instead of a stream.
    if (parsed.text !== '') {
        request.onDelta(parsed.text);
    }

    return parsed;
};

export const codexCancel = (requestId: string): void => {
    void invoke('codex_cancel', { requestId }).catch((error: unknown) => {
        console.error('[assistant] failed to cancel the ChatGPT request', error);
    });
};
