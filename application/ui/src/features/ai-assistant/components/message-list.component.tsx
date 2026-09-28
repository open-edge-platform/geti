// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { memo, useEffect, useRef } from 'react';

import { useTranslation } from '@/i18n';
import { Content, Flex, Heading, InlineAlert, ProgressCircle } from '@geti-ui/ui';

import { getAiAgent } from '../agents';
import { useAiConnection } from '../connection';
import type { ChatMessage, ChatStatus } from '../types';
import { markForVendor } from './assistant-mark.component';

import classes from './assistant.module.scss';

// Distance from the bottom of the scroll area that still counts as "the user
// is reading the newest content", in pixels.
const STICKY_BOTTOM_THRESHOLD = 80;

const MessageItem = memo(({ message, isStreaming }: { message: ChatMessage; isStreaming: boolean }) => {
    const { t } = useTranslation();
    const connection = useAiConnection();
    const agent = getAiAgent(connection.agentId);
    const Mark = markForVendor(agent.vendor);

    if (message.role === 'user') return <div className={classes.userMessage}>{message.content}</div>;

    return (
        <div className={classes.assistantMessage}>
            <div className={classes.assistantByline}>
                <Mark />
                <strong>
                    {agent.vendor === 'openai' ? t('assistant.vendorOpenai') : t('assistant.vendorAnthropic')}
                </strong>
                <span>{connection.model || t('assistant.accountDefault')}</span>
            </div>
            {message.content !== '' && <div className={classes.assistantText}>{message.content}</div>}
            {message.content === '' && message.error === undefined && message.stopped !== true && isStreaming && (
                <ProgressCircle size='S' isIndeterminate aria-label='Thinking' />
            )}
            {message.toolCalls?.map((call) => (
                <div key={call.callId} className={classes.toolStatus}>
                    {call.status === 'running'
                        ? t('assistant.toolCallPreparing')
                        : call.status === 'done'
                          ? t('assistant.toolCallDone')
                          : t('assistant.toolCallRejected')}
                </div>
            ))}
            {message.stopped === true && <div className={classes.toolStatus}>{t('assistant.stoppedByUser')}</div>}
            {message.error !== undefined && (
                <InlineAlert variant='negative' width='100%'>
                    <Heading>{t('assistant.requestFailed')}</Heading>
                    <Content>{message.error}</Content>
                </InlineAlert>
            )}
        </div>
    );
});

export const MessageList = ({ messages, status }: { messages: ChatMessage[]; status: ChatStatus }) => {
    const bottom = useRef<HTMLDivElement>(null);
    const scrollContainer = useRef<HTMLElement | null>(null);
    const isNearBottom = useRef(true);
    const lastId = messages.at(-1)?.id;

    useEffect(() => {
        // The drawer's message area is the nearest scrollable ancestor; find it
        // once so streaming deltas can check whether the user is still following.
        let node: HTMLElement | null = bottom.current?.parentElement ?? null;

        while (node !== null) {
            const style = getComputedStyle(node);
            if (style.overflowY === 'auto' || style.overflowY === 'scroll') break;
            node = node.parentElement;
        }

        scrollContainer.current = node;

        if (node === null) {
            return;
        }

        const onScroll = () => {
            isNearBottom.current = node.scrollHeight - node.scrollTop - node.clientHeight < STICKY_BOTTOM_THRESHOLD;
        };

        node.addEventListener('scroll', onScroll, { passive: true });
        return () => node.removeEventListener('scroll', onScroll);
    }, []);

    useEffect(() => {
        // Follow the stream only while the user reads the newest content; a
        // deliberate scroll-up must not be yanked back on every delta.
        if (!isNearBottom.current) return;
        const node = scrollContainer.current;
        if (node === null) {
            bottom.current?.scrollIntoView({ block: 'end' });
            return;
        }
        node.scrollTop = node.scrollHeight;
    }, [messages]);

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
