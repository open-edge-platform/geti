// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useSyncExternalStore } from 'react';

import { DEFAULT_API_MODEL, DEFAULT_CHATGPT_MODEL } from './config';
import type { AiConnection, AiProvider } from './types';

const STORAGE_KEY = 'geti.ai-assistant.connection.v1';

const DEFAULT_CONNECTION: AiConnection = {
    provider: 'api',
    model: DEFAULT_API_MODEL,
    executable: '',
};

const isProvider = (value: unknown): value is AiProvider => value === 'api' || value === 'chatgpt';

const read = (): AiConnection => {
    try {
        const stored: unknown = JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? 'null');

        if (stored === null || typeof stored !== 'object') {
            return DEFAULT_CONNECTION;
        }

        const { provider, model, executable } = stored as Record<string, unknown>;

        return {
            provider: isProvider(provider) ? provider : DEFAULT_CONNECTION.provider,
            model: typeof model === 'string' ? model : DEFAULT_CONNECTION.model,
            executable: typeof executable === 'string' ? executable : '',
        };
    } catch {
        return DEFAULT_CONNECTION;
    }
};

let connection = read();
const listeners = new Set<() => void>();

const subscribe = (listener: () => void) => {
    listeners.add(listener);

    return () => {
        listeners.delete(listener);
    };
};

export const setAiConnection = (update: Partial<AiConnection>): void => {
    connection = { ...connection, ...update };

    try {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(connection));
    } catch {
        // A full or disabled storage must not break the conversation.
    }

    listeners.forEach((listener) => listener());
};

export const setAiProvider = (provider: AiProvider): void => {
    if (connection.provider === provider) return;
    // The two providers do not share a model namespace, so switching also
    // resets the model to that provider's default.
    setAiConnection({
        provider,
        model: provider === 'api' ? DEFAULT_API_MODEL : DEFAULT_CHATGPT_MODEL,
    });
};

export const getAiConnection = (): AiConnection => connection;

export const useAiConnection = (): AiConnection => useSyncExternalStore(subscribe, getAiConnection, getAiConnection);
