// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useRef } from 'react';

import { Content, Flex, Heading, InlineAlert, ProgressCircle } from '@geti-ui/ui';

import { getAiAgent } from '../agents';
import { useAiConnection } from '../connection';
import type { ChatMessage, ChatStatus } from '../types';
import { markForVendor } from './assistant-mark.component';

import classes from './assistant.module.scss';

const MessageItem = ({ message, isStreaming }: { message: ChatMessage; isStreaming: boolean }) => {
    const connection = useAiConnection();
    const agent = getAiAgent(connection.agentId);
    const Mark = markForVendor(agent.vendor);

    if (message.role === 'user') return <div className={classes.userMessage}>{message.content}</div>;

    return (
        <div className={classes.assistantMessage}>
            <div className={classes.assistantByline}>
                <Mark />
                <strong>{agent.vendor === 'openai' ? 'ChatGPT' : 'Claude'}</strong>
                <span>{connection.model || 'account default'}</span>
            </div>
            {message.content !== '' && <div className={classes.assistantText}>{message.content}</div>}
            {message.content === '' && message.error === undefined && isStreaming && (
                <ProgressCircle size='S' isIndeterminate aria-label='Thinking' />
            )}
            {message.toolCalls?.map((call) => (
                <div key={call.callId} className={classes.toolStatus}>
                    {call.status === 'running'
                        ? 'Preparing annotations'
                        : call.status === 'done'
                          ? 'Annotations added'
                          : 'Proposal rejected'}
                </div>
            ))}
            {message.error !== undefined && (
                <InlineAlert variant='negative' width='100%'>
                    <Heading>Request failed</Heading>
                    <Content>{message.error}</Content>
                </InlineAlert>
            )}
        </div>
    );
};

export const MessageList = ({ messages, status }: { messages: ChatMessage[]; status: ChatStatus }) => {
    const bottom = useRef<HTMLDivElement>(null);
    useEffect(() => bottom.current?.scrollIntoView({ block: 'end' }), [messages]);
    const lastId = messages.at(-1)?.id;

    return (
        <Flex direction='column' gap='size-250'>
            {messages.map((message) => (
                <MessageItem
                    key={message.id}
                    message={message}
                    isStreaming={status === 'busy' && message.id === lastId}
                />
            ))}
            <div ref={bottom} />
        </Flex>
    );
};
