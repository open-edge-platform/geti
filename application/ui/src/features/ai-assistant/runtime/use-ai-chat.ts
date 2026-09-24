// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useCallback, useEffect, useRef, useState } from 'react';

import {
    annotationInstructions,
    annotationTool,
    parseAnnotationProposal,
    type AnnotationTarget,
} from '../annotation/annotation-tools';
import { AI_SYSTEM_INSTRUCTION, MAX_HISTORY_ITEMS, MAX_TOOL_TURNS } from '../config';
import { useAiConnection } from '../connection';
import { assistantRespond, cancelAssistantResponse } from '../transport/assistant-transport';
import type {
    ChatAttachment,
    ChatMessage,
    ChatStatus,
    ChatToolCall,
    ResponsesContentPart,
    ResponsesItem,
} from '../types';

export interface AiChat {
    messages: ChatMessage[];
    status: ChatStatus;
    send: (text: string, attachment: ChatAttachment) => void;
    stop: () => void;
    clear: () => void;
}

const trimHistory = (history: ResponsesItem[]): ResponsesItem[] => {
    if (history.length <= MAX_HISTORY_ITEMS) return history;
    let start = history.length - MAX_HISTORY_ITEMS;
    while (history[start]?.type === 'function_call_output') start += 1;
    return history.slice(start);
};

export const useAiChat = (target: AnnotationTarget): AiChat => {
    const connection = useAiConnection();
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [status, setStatus] = useState<ChatStatus>('idle');
    const history = useRef<ResponsesItem[]>([]);
    const requestId = useRef<string | null>(null);
    const runToken = useRef<{ cancelled: boolean } | null>(null);

    const updateMessage = useCallback((id: string, update: (message: ChatMessage) => ChatMessage) => {
        setMessages((current) => current.map((message) => (message.id === id ? update(message) : message)));
    }, []);

    const stop = useCallback(() => {
        if (runToken.current !== null) runToken.current.cancelled = true;
        if (requestId.current !== null) cancelAssistantResponse(requestId.current);
    }, []);

    const clear = useCallback(() => {
        stop();
        history.current = [];
        setMessages([]);
        setStatus('idle');
    }, [stop]);

    useEffect(() => clear, [clear]);
    useEffect(() => {
        clear();
    }, [clear, connection.agentId, target.key]);

    const send = useCallback(
        (text: string, attachment: ChatAttachment) => {
            if (status === 'busy') return;
            const token = { cancelled: false };
            runToken.current = token;
            const isCurrent = () => runToken.current === token && !token.cancelled;
            const content: ResponsesContentPart[] = [
                { type: 'input_text', text },
                { type: 'input_image', image_url: attachment.dataUrl, detail: 'high' },
            ];
            history.current = [
                ...history.current.map((item): ResponsesItem =>
                    item.type === 'message'
                        ? { ...item, content: item.content.filter((part) => part.type !== 'input_image') }
                        : item
                ),
                { type: 'message', role: 'user', content },
            ];

            const answerId = crypto.randomUUID();
            setMessages((current) => [
                ...current,
                { id: crypto.randomUUID(), role: 'user', content: text, attachments: [attachment] },
                { id: answerId, role: 'assistant', content: '' },
            ]);
            setStatus('busy');

            const run = async () => {
                for (let turn = 0; turn < MAX_TOOL_TURNS; turn++) {
                    const id = crypto.randomUUID();
                    requestId.current = id;
                    const result = await assistantRespond({
                        requestId: id,
                        model: connection.model,
                        instructions: `${AI_SYSTEM_INSTRUCTION}\n\n${annotationInstructions(target)}`,
                        input: trimHistory(history.current),
                        tools: [annotationTool(target)],
                        onDelta: (delta) => {
                            if (isCurrent()) {
                                updateMessage(answerId, (message) => ({
                                    ...message,
                                    content: message.content + delta,
                                }));
                            }
                        },
                    });
                    if (!isCurrent()) throw new Error('Stopped.');
                    if (result.text !== '') {
                        history.current.push({
                            type: 'message',
                            role: 'assistant',
                            content: [{ type: 'output_text', text: result.text }],
                        });
                        updateMessage(answerId, (message) => ({ ...message, content: result.text }));
                    }
                    if (result.functionCalls.length === 0) return;

                    const calls: ChatToolCall[] = result.functionCalls.map((call) => ({
                        callId: call.callId,
                        name: call.name,
                        status: 'running',
                        summary: call.arguments,
                    }));
                    updateMessage(answerId, (message) => ({
                        ...message,
                        toolCalls: [...(message.toolCalls ?? []), ...calls],
                    }));

                    for (const call of result.functionCalls) {
                        let output: string;
                        let failed = false;
                        try {
                            if (call.name !== 'propose_annotations') throw new Error('Unsupported assistant action.');
                            const args: unknown = JSON.parse(call.arguments);
                            if (typeof args !== 'object' || args === null || Array.isArray(args)) {
                                throw new Error('Invalid annotation proposal.');
                            }
                            const proposals = parseAnnotationProposal(args as Record<string, unknown>, target);
                            if (proposals.length > 0) target.apply(proposals);
                            output = JSON.stringify({ applied: proposals.length, saved: false });
                        } catch (error) {
                            failed = true;
                            output = JSON.stringify({
                                error: error instanceof Error ? error.message : 'Invalid annotation proposal.',
                            });
                        }
                        history.current.push(
                            {
                                type: 'function_call',
                                call_id: call.callId,
                                name: call.name,
                                arguments: call.arguments,
                            },
                            { type: 'function_call_output', call_id: call.callId, output }
                        );
                        updateMessage(answerId, (message) => ({
                            ...message,
                            toolCalls: message.toolCalls?.map((toolCall) =>
                                toolCall.callId === call.callId
                                    ? { ...toolCall, status: failed ? 'error' : 'done' }
                                    : toolCall
                            ),
                        }));
                    }
                }
                throw new Error('The assistant did not finish the annotation request.');
            };

            void run()
                .catch((error: unknown) => {
                    updateMessage(answerId, (message) => ({
                        ...message,
                        error: error instanceof Error ? error.message : 'The assistant request failed.',
                    }));
                })
                .finally(() => {
                    if (runToken.current !== token) return;
                    runToken.current = null;
                    requestId.current = null;
                    setStatus('idle');
                });
        },
        [connection.model, status, target, updateMessage]
    );

    return { messages, status, send, stop, clear };
};
