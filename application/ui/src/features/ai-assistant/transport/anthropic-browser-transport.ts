// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { i18n } from '@/i18n';

import {
    AssistantConnectionError,
    AssistantStoppedError,
    type FunctionCall,
    type ResponsesContentPart,
    type ResponsesItem,
    type StreamRequest,
    type StreamResult,
} from '../types';
import { readStoredKey } from './key-service';
import { redactSecrets } from './redact';
import { consumeSse } from './sse';

const ANTHROPIC_MESSAGES_URL = 'https://api.anthropic.com/v1/messages';
const controllers = new Map<string, AbortController>();

type AnthropicContent =
    | { type: 'text'; text: string }
    | { type: 'image'; source: { type: 'base64'; media_type: string; data: string } }
    | { type: 'tool_use'; id: string; name: string; input: unknown }
    | { type: 'tool_result'; tool_use_id: string; content: string };

interface AnthropicMessage {
    role: 'user' | 'assistant';
    content: AnthropicContent[];
}

const asRecord = (value: unknown): Record<string, unknown> =>
    typeof value === 'object' && value !== null ? (value as Record<string, unknown>) : {};

const toContent = (parts: ResponsesContentPart[]): AnthropicContent[] =>
    parts.flatMap((part): AnthropicContent[] => {
        if (part.type !== 'input_image') return part.text === '' ? [] : [{ type: 'text', text: part.text }];
        const match = /^data:([^;,]+);base64,(.+)$/i.exec(part.image_url);
        if (match === null || !/^image\/(jpeg|png|gif|webp)$/i.test(match[1])) return [];
        return [{ type: 'image', source: { type: 'base64', media_type: match[1], data: match[2] } }];
    });

const translateInput = (items: ResponsesItem[]): AnthropicMessage[] => {
    const messages: AnthropicMessage[] = [];
    const push = (role: AnthropicMessage['role'], content: AnthropicContent[]) => {
        if (content.length === 0) return;
        const previous = messages.at(-1);
        if (previous?.role === role) previous.content.push(...content);
        else messages.push({ role, content });
    };

    items.forEach((item) => {
        if (item.type === 'message') {
            push(item.role, toContent(item.content));
        } else if (item.type === 'function_call') {
            let input: unknown = {};
            try {
                input = JSON.parse(item.arguments);
            } catch {
                input = {};
            }
            push('assistant', [{ type: 'tool_use', id: item.call_id, name: item.name, input }]);
        } else {
            push('user', [{ type: 'tool_result', tool_use_id: item.call_id, content: item.output }]);
        }
    });
    return messages;
};

export const buildAnthropicBody = (request: StreamRequest): Record<string, unknown> => ({
    model: request.model,
    max_tokens: 8192,
    system: request.instructions,
    messages: translateInput(request.input),
    tools: request.tools.map(({ name, description, parameters }) => ({
        name,
        description,
        input_schema: parameters,
    })),
    stream: true,
});

export class AnthropicAssembler {
    private readonly blocks = new Map<number, { type: 'text' | 'tool_use'; text: string; id: string; name: string }>();
    private readonly order: number[] = [];
    done = false;
    error: string | null = null;

    constructor(private readonly onDelta: (text: string) => void) {}

    accept(payload: string): void {
        let event: Record<string, unknown>;
        try {
            event = asRecord(JSON.parse(payload));
        } catch {
            // One malformed event must not discard the whole response.
            return;
        }
        if (event.type === 'content_block_start') {
            const index = typeof event.index === 'number' ? event.index : -1;
            const block = asRecord(event.content_block);
            if (index < 0) return;
            this.order.push(index);
            this.blocks.set(index, {
                type: block.type === 'tool_use' ? 'tool_use' : 'text',
                text: typeof block.text === 'string' ? block.text : '',
                id: typeof block.id === 'string' ? block.id : crypto.randomUUID(),
                name: typeof block.name === 'string' ? block.name : '',
            });
        } else if (event.type === 'content_block_delta') {
            const block = this.blocks.get(typeof event.index === 'number' ? event.index : -1);
            const delta = asRecord(event.delta);
            if (block === undefined) return;
            if (delta.type === 'text_delta' && typeof delta.text === 'string') {
                block.text += delta.text;
                this.onDelta(delta.text);
            } else if (delta.type === 'input_json_delta' && typeof delta.partial_json === 'string') {
                block.text += delta.partial_json;
            }
        } else if (event.type === 'message_stop') {
            this.done = true;
        } else if (event.type === 'error') {
            const error = asRecord(event.error);
            this.error =
                typeof error.message === 'string' ? error.message : i18n.t('assistant.anthropicCouldNotComplete');
            this.done = true;
        }
    }

    result(): StreamResult {
        const text = this.order
            .map((index) => this.blocks.get(index))
            .filter((block) => block?.type === 'text')
            .map((block) => block?.text ?? '')
            .join('');
        const functionCalls: FunctionCall[] = this.order
            .map((index) => this.blocks.get(index))
            .filter((block) => block?.type === 'tool_use')
            .map((block) => ({
                callId: block?.id ?? crypto.randomUUID(),
                name: block?.name ?? '',
                arguments: block?.text === '' ? '{}' : (block?.text ?? '{}'),
            }));
        return { text, functionCalls };
    }
}

const errorMessage = async (response: Response): Promise<string> => {
    const body = await response.json().catch(() => null);
    const error = asRecord(asRecord(body).error);
    const message =
        typeof error.message === 'string' ? error.message : `Anthropic request failed (${response.status}).`;
    return redactSecrets(message);
};

export const streamAnthropicInBrowser = async (request: StreamRequest): Promise<StreamResult> => {
    const key = readStoredKey('anthropic-api-key');
    if (key === null || key.trim() === '') throw new AssistantConnectionError(i18n.t('assistant.addAnthropicKey'));
    const controller = new AbortController();
    controllers.set(request.requestId, controller);

    try {
        const response = await fetch(ANTHROPIC_MESSAGES_URL, {
            method: 'POST',
            signal: controller.signal,
            headers: {
                'content-type': 'application/json',
                accept: 'text/event-stream',
                'x-api-key': key.trim(),
                'anthropic-version': '2023-06-01',
                'anthropic-dangerous-direct-browser-access': 'true',
            },
            body: JSON.stringify(buildAnthropicBody(request)),
        });
        if (!response.ok) throw new Error(await errorMessage(response));
        if (response.body === null) throw new Error(i18n.t('assistant.anthropicEnded'));
        const assembler = new AnthropicAssembler(request.onDelta);
        await consumeSse(response.body, (payload) => assembler.accept(payload));
        if (assembler.error !== null) throw new Error(redactSecrets(assembler.error));
        if (!assembler.done) throw new Error(i18n.t('assistant.anthropicIncomplete'));
        return assembler.result();
    } catch (error) {
        if (controller.signal.aborted) throw new AssistantStoppedError();
        throw error;
    } finally {
        controllers.delete(request.requestId);
    }
};

export const cancelAnthropicInBrowser = (requestId: string): void => controllers.get(requestId)?.abort();
