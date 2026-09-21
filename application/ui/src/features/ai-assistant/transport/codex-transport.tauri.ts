// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Channel, invoke } from '@tauri-apps/api/core';
import { open } from '@tauri-apps/plugin-dialog';
import { openUrl } from '@tauri-apps/plugin-opener';

import { getAiConnection } from '../connection';
import type { CodexAccount, CodexLocation, CodexModel, StreamRequest, StreamResult } from '../types';
import { parseCodexResult } from './parse-response';

type CodexEvent = { type: 'login'; url: string };

const newRequestId = (): string => crypto.randomUUID();

// The Rust bridge owns one Codex subprocess. Keep background account/model
// lookups in the same queue as login and chat, including cancelled requests
// until the native operation has actually released its slot.
let nativeQueue: Promise<void> = Promise.resolve();
const enqueue = <T>(action: () => Promise<T>): Promise<T> => {
    const result = nativeQueue.then(action);
    nativeQueue = result.then(
        () => undefined,
        () => undefined
    );
    return result;
};

interface AccountSession {
    executable: string;
    account?: CodexAccount | null;
    status?: Promise<CodexAccount | null>;
    authentication?: Promise<void>;
    authenticationOperation?: 'login' | 'logout';
}
let accountSession: AccountSession | undefined;
const sessionForCurrentExecutable = (): AccountSession => {
    const { executable } = getAiConnection();
    if (accountSession?.executable !== executable) accountSession = { executable };
    return accountSession;
};

const responses = new Map<string, { cancelled: boolean; started: boolean; reject: (error: Error) => void }>();

const asRecord = (value: unknown): Record<string, unknown> =>
    typeof value === 'object' && value !== null ? (value as Record<string, unknown>) : {};

/** Rust command errors arrive as strings; callers expect JavaScript Errors. */
const invokeCodex = async <T>(command: string, args?: Record<string, unknown>): Promise<T> => {
    try {
        return await invoke<T>(command, args);
    } catch (reason: unknown) {
        throw reason instanceof Error
            ? reason
            : new Error(typeof reason === 'string' ? reason : 'The ChatGPT operation failed.');
    }
};

const run = (operation: string, body: unknown, onEvent: Channel<CodexEvent>, executable: string): Promise<unknown> => {
    return enqueue(() =>
        invokeCodex('codex_operation', {
            requestId: newRequestId(),
            operation,
            executable: executable || null,
            body,
            onEvent,
        })
    );
};

const readAccount = async (executable: string): Promise<CodexAccount | null> => {
    const result = asRecord(await run('status', null, new Channel<CodexEvent>(), executable));
    const account = asRecord(result.account ?? result);

    const email = typeof account.email === 'string' ? account.email : null;
    const plan = typeof account.planType === 'string' ? account.planType : null;

    if (
        email === null &&
        account.type !== 'chatgpt' &&
        account.authenticated !== true &&
        result.authenticated !== true
    ) {
        return null;
    }

    return { email, plan };
};

/** Share probes and retain a confirmed account for this app session. No tokens are cached here. */
export const codexStatus = async (forceRefresh = false): Promise<CodexAccount | null> => {
    const session = sessionForCurrentExecutable();
    await session.authentication;
    if (session.status) return session.status;
    if (!forceRefresh && session.account !== undefined) return session.account;
    const pending = readAccount(session.executable)
        .then((account) => {
            session.account = account;
            return account;
        })
        .finally(() => {
            if (session.status === pending) session.status = undefined;
        });
    session.status = pending;
    return pending;
};

const authenticate = (operation: 'login' | 'logout', channel: Channel<CodexEvent>): Promise<void> => {
    const session = sessionForCurrentExecutable();
    if (session.authentication && session.authenticationOperation === operation) return session.authentication;
    const pending = run(operation, null, channel, session.executable)
        .then(() => {
            session.account = operation === 'logout' ? null : undefined;
        })
        .finally(() => {
            if (session.authentication === pending) session.authentication = undefined;
        });
    session.authentication = pending;
    session.authenticationOperation = operation;
    return pending;
};

/** The executable the shell auto-detects, plus every folder it looked in. */
export const codexLocate = (): Promise<CodexLocation> => invokeCodex<CodexLocation>('codex_locate');

/** Plain-text report about the Codex install and the last operation's protocol traffic. */
export const codexDiagnostics = (): Promise<string> =>
    invokeCodex<string>('codex_diagnostics', { executable: getAiConnection().executable || null });

/** Resolves to `null` when the user dismisses the file picker. */
export const pickCodexBinary = async (): Promise<string | null> => {
    const selected = await open({
        multiple: false,
        directory: false,
        title: 'Select the ChatGPT (Codex) executable',
        filters: [{ name: 'Executable', extensions: ['exe', 'cmd', 'bat'] }],
    });

    return typeof selected === 'string' ? selected : null;
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

    await authenticate('login', channel);
};

export const codexLogout = async (): Promise<void> => {
    await authenticate('logout', new Channel<CodexEvent>());
};

/** Models the signed-in account may use, text+image capable ones first. */
export const codexModels = async (): Promise<CodexModel[]> => {
    const result = asRecord(await run('models', null, new Channel<CodexEvent>(), getAiConnection().executable));
    const entries = Array.isArray(result.data) ? result.data : [];

    return entries
        .map((entry) => {
            const model = asRecord(entry);
            const id = typeof model.model === 'string' ? model.model : typeof model.id === 'string' ? model.id : '';
            const label = typeof model.displayName === 'string' && model.displayName !== '' ? model.displayName : id;

            return { id, label };
        })
        .filter((model) => model.id !== '');
};

export const codexRespond = async (request: StreamRequest): Promise<StreamResult> => {
    const channel = new Channel<CodexEvent>();

    const executable = getAiConnection().executable || null;
    let rejectCancellation!: (error: Error) => void;
    const cancellation = new Promise<never>((_resolve, reject) => {
        rejectCancellation = reject;
    });
    const state = { cancelled: false, started: false, reject: rejectCancellation };
    responses.set(request.requestId, state);
    const pending = enqueue(async () => {
        if (state.cancelled) throw new Error('Stopped.');
        state.started = true;
        return invokeCodex('codex_operation', {
            requestId: request.requestId,
            operation: 'response',
            executable,
            body: {
                model: request.model === '' ? null : request.model,
                instructions: request.instructions,
                input: request.input,
                tools: request.tools,
            },
            onEvent: channel,
        });
    }).finally(() => responses.delete(request.requestId));
    const result = await Promise.race([pending, cancellation]);

    const parsed = parseCodexResult(result);

    // Codex answers a turn in one piece rather than token by token, so the
    // caller gets a single delta instead of a stream.
    if (parsed.text !== '') {
        request.onDelta(parsed.text);
    }

    return parsed;
};

export const codexCancel = (requestId: string): void => {
    const state = responses.get(requestId);
    if (!state || state.cancelled) return;
    state.cancelled = true;
    state.reject(new Error('Stopped.'));
    // Queued work never entered Rust, so no early-cancellation record is needed.
    if (!state.started) return;
    void invokeCodex('codex_cancel', { requestId }).catch((error: unknown) => {
        console.error('[assistant] failed to cancel the ChatGPT request', error);
    });
};
