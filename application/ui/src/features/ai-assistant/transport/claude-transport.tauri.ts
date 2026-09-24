// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { invoke } from '@tauri-apps/api/core';
import { open } from '@tauri-apps/plugin-dialog';

import { getAiConnection } from '../connection';
import type { AssistantAccount, CodexLocation, StreamRequest, StreamResult } from '../types';
import { parseCodexResult } from './parse-response';

const asRecord = (value: unknown): Record<string, unknown> =>
    typeof value === 'object' && value !== null ? (value as Record<string, unknown>) : {};

const invokeClaude = async <T>(command: string, args?: Record<string, unknown>): Promise<T> => {
    try {
        return await invoke<T>(command, args);
    } catch (reason: unknown) {
        throw reason instanceof Error
            ? reason
            : new Error(typeof reason === 'string' ? reason : 'The Claude operation failed.');
    }
};

const runClaudeOperation = (
    operation: string,
    body: unknown = null,
    requestId: string = crypto.randomUUID()
): Promise<unknown> =>
    invokeClaude('claude_operation', {
        requestId,
        operation,
        executable: getAiConnection().executable || null,
        body,
    });

export const claudeStatus = async (): Promise<AssistantAccount | null> => {
    const result = asRecord(await runClaudeOperation('status'));
    const account = asRecord(result.account ?? result);
    if (result.connected !== true && account.authenticated !== true && account.type !== 'claude') return null;
    return {
        type: 'claude',
        email: typeof account.email === 'string' ? account.email : null,
        plan: typeof account.planType === 'string' ? account.planType : null,
    };
};

export const claudeLocate = (): Promise<CodexLocation> => invokeClaude('claude_locate');

export const claudeLogin = async (): Promise<void> => {
    await runClaudeOperation('login');
};

export const claudeLogout = async (): Promise<void> => {
    await runClaudeOperation('logout');
};

export const pickClaudeBinary = async (): Promise<string | null> => {
    const selected = await open({
        multiple: false,
        directory: false,
        title: 'Select the Claude executable',
        filters: [{ name: 'Executable', extensions: ['exe', 'cmd', 'bat'] }],
    });
    return typeof selected === 'string' ? selected : null;
};

export const claudeRespond = async (request: StreamRequest): Promise<StreamResult> => {
    const result = await runClaudeOperation(
        'response',
        {
            model: request.model,
            instructions: request.instructions,
            input: request.input,
            tools: request.tools,
        },
        request.requestId
    );
    const parsed = parseCodexResult(result);
    if (parsed.text !== '') request.onDelta(parsed.text);
    return parsed;
};

export const claudeCancel = (requestId: string): void => {
    void invokeClaude('claude_cancel', { requestId }).catch((error: unknown) => {
        console.error('[assistant] failed to cancel the Claude request', error);
    });
};
