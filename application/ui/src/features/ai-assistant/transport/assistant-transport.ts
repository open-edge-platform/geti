// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { getAiConnection } from '../connection';
import type { StreamRequest, StreamResult } from '../types';
import { cancelAnthropicResponse, streamAnthropicResponse } from './anthropic-transport';
import { claudeCancel, claudeRespond } from './claude-transport';
import { codexCancel, codexRespond } from './codex-transport';
import { cancelResponse, streamResponse } from './openai-transport';

export const assistantRespond = (request: StreamRequest): Promise<StreamResult> => {
    switch (getAiConnection().agentId) {
        case 'openai-api':
            return streamResponse(request);
        case 'openai-app':
            return codexRespond(request);
        case 'anthropic-api':
            return streamAnthropicResponse(request);
        case 'anthropic-app':
            return claudeRespond(request);
    }
};

export const cancelAssistantResponse = (requestId: string): void => {
    switch (getAiConnection().agentId) {
        case 'openai-api':
            cancelResponse(requestId);
            return;
        case 'openai-app':
            codexCancel(requestId);
            return;
        case 'anthropic-api':
            cancelAnthropicResponse(requestId);
            return;
        case 'anthropic-app':
            claudeCancel(requestId);
    }
};
