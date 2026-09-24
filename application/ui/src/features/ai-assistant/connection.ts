// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useSyncExternalStore } from 'react';

import { getAiAgent, isAiAgentId, resolveAvailableAgent } from './agents';
import type { AiAgentId, AiConnection, AiVendor } from './types';

const STORAGE_KEY = 'geti.ai-assistant.connection.v2';

interface AgentSettings {
    model: string;
    executable: string;
}

interface ConnectionState {
    agentId: AiAgentId;
    settings: Partial<Record<AiAgentId, AgentSettings>>;
}

const defaultSettings = (agentId: AiAgentId): AgentSettings => ({
    model: getAiAgent(agentId).defaultModel,
    executable: '',
});

const DEFAULT_STATE: ConnectionState = { agentId: 'openai-api', settings: {} };

const read = (): ConnectionState => {
    try {
        if (typeof window === 'undefined') return DEFAULT_STATE;
        const stored: unknown = JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? 'null');
        if (stored === null || typeof stored !== 'object') {
            return DEFAULT_STATE;
        }
        const record = stored as Record<string, unknown>;
        const storedAgentId = isAiAgentId(record.agentId) ? record.agentId : DEFAULT_STATE.agentId;
        const agentId = resolveAvailableAgent(storedAgentId);
        const rawSettings =
            typeof record.settings === 'object' && record.settings !== null
                ? (record.settings as Record<string, unknown>)
                : {};
        const settings: ConnectionState['settings'] = {};
        Object.entries(rawSettings).forEach(([id, value]) => {
            if (!isAiAgentId(id) || typeof value !== 'object' || value === null) return;
            const fields = value as Record<string, unknown>;
            settings[id] = {
                model: typeof fields.model === 'string' ? fields.model : getAiAgent(id).defaultModel,
                executable: typeof fields.executable === 'string' ? fields.executable : '',
            };
        });
        return { agentId, settings };
    } catch {
        return DEFAULT_STATE;
    }
};

let state = read();
const listeners = new Set<() => void>();

const subscribe = (listener: () => void) => {
    listeners.add(listener);

    return () => {
        listeners.delete(listener);
    };
};

const persist = (): void => {
    try {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
        // Storage availability must not break annotation.
    }
    listeners.forEach((listener) => listener());
};

export const getAiConnection = (): AiConnection => {
    const current = state.settings[state.agentId] ?? defaultSettings(state.agentId);
    return { agentId: state.agentId, ...current };
};

export const setAiConnection = (update: Partial<Omit<AiConnection, 'agentId'>>): void => {
    state = {
        ...state,
        settings: {
            ...state.settings,
            [state.agentId]: { ...defaultSettings(state.agentId), ...state.settings[state.agentId], ...update },
        },
    };
    persist();
};

export const setAiAgent = (agentId: AiAgentId): void => {
    const availableId = resolveAvailableAgent(agentId);
    if (state.agentId === availableId) return;
    state = { ...state, agentId: availableId };
    persist();
};

export const setAiVendor = (vendor: AiVendor): void => {
    const preferredMethod = getAiAgent(state.agentId).method;
    const candidates = ['api', 'app'] as const;
    const methodOrder = [preferredMethod, ...candidates.filter((method) => method !== preferredMethod)];
    const next = methodOrder
        .map((method) => `${vendor}-${method}` as AiAgentId)
        .find((agentId) => resolveAvailableAgent(agentId) === agentId);
    if (next !== undefined) setAiAgent(next);
};

export const useAiConnection = (): AiConnection => useSyncExternalStore(subscribe, getAiConnection, getAiConnection);
