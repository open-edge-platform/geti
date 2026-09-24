// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ANTHROPIC_MODELS, OPENAI_MODELS } from './config';
import { hasNativeAssistantApps } from './platform';
import type { AiAgentId, AiConnectionMethod, AiVendor } from './types';

export interface AiAgent {
    id: AiAgentId;
    vendor: AiVendor;
    name: string;
    method: AiConnectionMethod;
    defaultModel: string;
    models: readonly string[];
    credentialAccount?: 'openai-api-key' | 'anthropic-api-key';
}

export const AI_AGENTS: readonly AiAgent[] = [
    {
        id: 'openai-api',
        vendor: 'openai',
        name: 'OpenAI API',
        method: 'api',
        defaultModel: OPENAI_MODELS[0],
        models: OPENAI_MODELS,
        credentialAccount: 'openai-api-key',
    },
    {
        id: 'openai-app',
        vendor: 'openai',
        name: 'ChatGPT app',
        method: 'app',
        defaultModel: '',
        models: [],
    },
    {
        id: 'anthropic-api',
        vendor: 'anthropic',
        name: 'Anthropic API',
        method: 'api',
        defaultModel: ANTHROPIC_MODELS[0],
        models: ANTHROPIC_MODELS,
        credentialAccount: 'anthropic-api-key',
    },
    {
        id: 'anthropic-app',
        vendor: 'anthropic',
        name: 'Claude app',
        method: 'app',
        defaultModel: 'sonnet',
        models: [],
    },
];

const AGENTS_BY_ID = new Map(AI_AGENTS.map((agent) => [agent.id, agent]));

export const getAiAgent = (id: AiAgentId): AiAgent => AGENTS_BY_ID.get(id) ?? AI_AGENTS[0];

export const isAiAgentId = (value: unknown): value is AiAgentId =>
    typeof value === 'string' && AGENTS_BY_ID.has(value as AiAgentId);

export const availableAiAgents = (): readonly AiAgent[] =>
    AI_AGENTS.filter(({ method }) => method === 'api' || hasNativeAssistantApps());

export const availableAgentsForVendor = (vendor: AiVendor): readonly AiAgent[] =>
    availableAiAgents().filter((agent) => agent.vendor === vendor);

export const resolveAvailableAgent = (id: AiAgentId): AiAgentId => {
    const requested = getAiAgent(id);
    if (availableAiAgents().some((agent) => agent.id === id)) return id;
    return availableAgentsForVendor(requested.vendor)[0]?.id ?? 'openai-api';
};
