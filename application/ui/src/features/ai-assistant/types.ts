// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

/** How the assistant reaches a model: a metered API key, or a ChatGPT account. */
export type AiProvider = 'api' | 'chatgpt';

export interface AiConnection {
    provider: AiProvider;
    model: string;
    /** Optional absolute path to the Codex executable, for portable installs. */
    executable: string;
}

export type ResponsesContentPart =
    | { type: 'input_text'; text: string }
    | { type: 'input_image'; image_url: string; detail: 'auto' | 'low' | 'high' }
    | { type: 'output_text'; text: string };

/**
 * Items of the OpenAI Responses API `input` array. The ChatGPT transport
 * consumes the very same shape, so the chat runtime keeps one transcript
 * regardless of the selected provider.
 */
export type ResponsesItem =
    | { type: 'message'; role: 'user' | 'assistant'; content: ResponsesContentPart[] }
    | { type: 'function_call'; call_id: string; name: string; arguments: string }
    | { type: 'function_call_output'; call_id: string; output: string };

export interface ToolDefinition {
    type: 'function';
    name: string;
    description: string;
    strict: boolean;
    parameters: Record<string, unknown>;
}

export interface FunctionCall {
    callId: string;
    name: string;
    /** Raw JSON string, exactly as produced by the model. */
    arguments: string;
}

export interface StreamResult {
    text: string;
    functionCalls: FunctionCall[];
}

export interface StreamRequest {
    requestId: string;
    model: string;
    instructions: string;
    input: ResponsesItem[];
    tools: ToolDefinition[];
    onDelta: (text: string) => void;
}

export interface CodexAccount {
    email: string | null;
    plan: string | null;
}

/** A model the signed-in ChatGPT account may use. */
export interface CodexModel {
    id: string;
    label: string;
}

/** Where the desktop shell found the ChatGPT (Codex) executable, and where it looked. */
export interface CodexLocation {
    path: string | null;
    searched: string[];
}

export type ToolCallStatus = 'running' | 'done' | 'error';

export interface ChatToolCall {
    callId: string;
    name: string;
    status: ToolCallStatus;
    summary: string;
}

/** An action tool waiting for the user to approve or decline it. */
export interface PendingApproval {
    callId: string;
    name: string;
    description: string;
}

export interface ChatAttachment {
    id: string;
    name: string;
    /** `data:image/...;base64,…`, resolved before the message is sent. */
    dataUrl: string;
}

export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    attachments?: ChatAttachment[];
    toolCalls?: ChatToolCall[];
    error?: string;
}

export type ChatStatus = 'idle' | 'busy';
