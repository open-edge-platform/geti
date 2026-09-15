// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useCallback, useMemo, useRef, useState } from 'react';

import { v4 as uuid } from 'uuid';

import { buildInstructions, MAX_HISTORY_ITEMS, MAX_TOOL_TURNS } from '../config';
import { useAiConnection } from '../connection';
import {
    ACTION_TOOLS,
    createGetiTools,
    describeToolCall,
    executeToolCall,
    GETI_TOOL_DEFINITIONS,
} from '../tools/geti-tools';
import { codexCancel, codexRespond } from '../transport/codex-transport';
import { cancelResponse, streamResponse } from '../transport/openai-transport';
import type {
    ChatAttachment,
    ChatMessage,
    ChatStatus,
    ChatToolCall,
    PendingApproval,
    ResponsesContentPart,
    ResponsesItem,
} from '../types';

const CANCELLED_BY_USER = 'Stopped.';

const DECLINED_OUTPUT = JSON.stringify({
    error: 'The user declined this action. Do not retry it; ask what to change instead.',
});

export interface AiChat {
    messages: ChatMessage[];
    status: ChatStatus;
    /** Set while an action tool waits for the user to approve or decline it. */
    pendingApproval: PendingApproval | null;
    resolveApproval: (isApproved: boolean) => void;
    send: (text: string, attachments: ChatAttachment[]) => void;
    stop: () => void;
    clear: () => void;
}

/**
 * Keeps the transcript bounded while never cutting a `function_call` away from
 * its `function_call_output`: a dangling pair makes the Responses API reject the
 * whole request.
 */
const trimHistory = (history: ResponsesItem[]): ResponsesItem[] => {
    if (history.length <= MAX_HISTORY_ITEMS) {
        return history;
    }

    let start = history.length - MAX_HISTORY_ITEMS;
    while (start < history.length && history[start].type === 'function_call_output') {
        start += 1;
    }

    return history.slice(start);
};

export const useAiChat = (projectId: string, context: string): AiChat => {
    const connection = useAiConnection();

    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [status, setStatus] = useState<ChatStatus>('idle');
    const [pendingApproval, setPendingApproval] = useState<PendingApproval | null>(null);

    const history = useRef<ResponsesItem[]>([]);
    const requestId = useRef<string | null>(null);
    const stopped = useRef(false);
    const approval = useRef<((isApproved: boolean) => void) | null>(null);

    const tools = useMemo(() => createGetiTools(projectId), [projectId]);

    const updateMessage = useCallback((id: string, update: (message: ChatMessage) => ChatMessage) => {
        setMessages((previous) => previous.map((message) => (message.id === id ? update(message) : message)));
    }, []);

    const resolveApproval = useCallback((isApproved: boolean) => {
        approval.current?.(isApproved);
        approval.current = null;
        setPendingApproval(null);
    }, []);

    const stop = useCallback(() => {
        stopped.current = true;
        resolveApproval(false);

        const id = requestId.current;

        if (id === null) {
            return;
        }

        if (connection.provider === 'api') {
            cancelResponse(id);
        } else {
            codexCancel(id);
        }
    }, [connection.provider, resolveApproval]);

    const clear = useCallback(() => {
        stop();
        history.current = [];
        setMessages([]);
        setStatus('idle');
    }, [stop]);

    const send = useCallback(
        (text: string, attachments: ChatAttachment[]) => {
            if (status === 'busy' || text.trim() === '') {
                return;
            }

            const content: ResponsesContentPart[] = [{ type: 'input_text', text }];
            attachments.forEach((attachment) => {
                content.push({ type: 'input_image', image_url: attachment.dataUrl, detail: 'high' });
            });

            history.current = [...history.current, { type: 'message', role: 'user', content }];

            const answerId = uuid();
            setMessages((previous) => [
                ...previous,
                { id: uuid(), role: 'user', content: text, attachments },
                { id: answerId, role: 'assistant', content: '' },
            ]);
            setStatus('busy');
            stopped.current = false;

            const respond = connection.provider === 'api' ? streamResponse : codexRespond;

            /** Holds the call until the user approves it on the card in the chat. */
            const runApprovedCall = async (callId: string, name: string, args: string) => {
                const isApproved = await new Promise<boolean>((resolve) => {
                    approval.current = resolve;
                    setPendingApproval({ callId, name, description: describeToolCall(name, args) });
                });

                if (!isApproved) {
                    return { output: DECLINED_OUTPUT, failed: true };
                }

                return executeToolCall(tools, name, args);
            };

            const run = async () => {
                for (let turn = 0; turn < MAX_TOOL_TURNS; turn++) {
                    const id = uuid();
                    requestId.current = id;

                    const result = await respond({
                        requestId: id,
                        model: connection.model,
                        instructions: buildInstructions(context),
                        input: trimHistory(history.current),
                        tools: GETI_TOOL_DEFINITIONS,
                        onDelta: (delta) => {
                            updateMessage(answerId, (message) => ({ ...message, content: message.content + delta }));
                        },
                    });

                    if (result.text !== '') {
                        history.current = [
                            ...history.current,
                            {
                                type: 'message',
                                role: 'assistant',
                                content: [{ type: 'output_text', text: result.text }],
                            },
                        ];
                        // Codex answers in one piece, so the streamed content may
                        // already be complete; assigning keeps both paths equal.
                        updateMessage(answerId, (message) => ({ ...message, content: result.text }));
                    }

                    if (result.functionCalls.length === 0) {
                        return;
                    }

                    const pending: ChatToolCall[] = result.functionCalls.map((call) => ({
                        callId: call.callId,
                        name: call.name,
                        status: 'running',
                        summary: call.arguments,
                    }));
                    updateMessage(answerId, (message) => ({
                        ...message,
                        toolCalls: [...(message.toolCalls ?? []), ...pending],
                    }));

                    for (const call of result.functionCalls) {
                        const { output, failed } = ACTION_TOOLS.has(call.name)
                            ? await runApprovedCall(call.callId, call.name, call.arguments)
                            : await executeToolCall(tools, call.name, call.arguments);

                        history.current = [
                            ...history.current,
                            {
                                type: 'function_call',
                                call_id: call.callId,
                                name: call.name,
                                arguments: call.arguments,
                            },
                            { type: 'function_call_output', call_id: call.callId, output },
                        ];

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

                throw new Error('The assistant kept looking things up without answering. Try a narrower question.');
            };

            void run()
                .catch((error: unknown) => {
                    const message = stopped.current
                        ? CANCELLED_BY_USER
                        : error instanceof Error
                          ? error.message
                          : 'The assistant request failed.';

                    updateMessage(answerId, (chatMessage) => ({ ...chatMessage, error: message }));
                })
                .finally(() => {
                    requestId.current = null;
                    resolveApproval(false);
                    setStatus('idle');
                });
        },
        [connection.model, connection.provider, context, resolveApproval, status, tools, updateMessage]
    );

    return { messages, status, pendingApproval, resolveApproval, send, stop, clear };
};
