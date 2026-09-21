// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useRef } from 'react';

import { Content, Flex, Heading, InlineAlert, ProgressCircle, StatusLight, Text, View } from '@geti-ui/ui';

import type { ChatMessage, ChatStatus, ChatToolCall } from '../types';

import classes from './assistant.module.scss';

const TOOL_LABELS: Record<string, string> = {
    propose_annotations: 'Adding annotations to the image',
    list_projects: 'Reading your projects',
    get_project: 'Reading the project setup',
    get_dataset_statistics: 'Reading dataset statistics',
    list_media: 'Reading the media list',
    list_models: 'Reading trained models',
    get_model: 'Reading the model and its scores',
    get_training_metrics: 'Reading the training curves',
    get_training_logs: 'Reading the training log',
    list_dataset_revisions: 'Reading dataset revisions',
    list_model_architectures: 'Reading available architectures',
    list_training_devices: 'Reading training hardware',
    get_system_info: 'Reading system information',
    list_jobs: 'Reading running jobs',
    get_job: 'Reading the job status',
    start_training: 'Starting training',
    start_quantization: 'Starting quantization',
    cancel_job: 'Cancelling the job',
};

const ToolCallRow = ({ toolCall }: { toolCall: ChatToolCall }) => {
    const label = TOOL_LABELS[toolCall.name] ?? toolCall.name;

    return (
        <View UNSAFE_className={classes.toolCall}>
            {toolCall.status === 'running' ? (
                <ProgressCircle size={'S'} isIndeterminate aria-label={label} />
            ) : (
                <StatusLight variant={toolCall.status === 'error' ? 'negative' : 'positive'} margin={0} />
            )}
            <Text UNSAFE_style={{ fontSize: 'var(--spectrum-global-dimension-font-size-75)' }}>{label}</Text>
        </View>
    );
};

const MessageItem = ({ message, isStreaming }: { message: ChatMessage; isStreaming: boolean }) => {
    if (message.role === 'user') {
        return (
            <Flex direction={'column'} gap={'size-75'} alignItems={'end'}>
                {message.attachments !== undefined && message.attachments.length > 0 && (
                    <div className={classes.thumbnails}>
                        {message.attachments.map((attachment) => (
                            <img
                                key={attachment.id}
                                src={attachment.dataUrl}
                                alt={attachment.name}
                                title={attachment.name}
                                className={classes.thumbnail}
                            />
                        ))}
                    </div>
                )}
                <View UNSAFE_className={classes.userMessage}>{message.content}</View>
            </Flex>
        );
    }

    return (
        <Flex direction={'column'} gap={'size-100'} alignItems={'start'}>
            {message.toolCalls?.map((toolCall) => (
                <ToolCallRow key={toolCall.callId} toolCall={toolCall} />
            ))}

            {message.content !== '' && <View UNSAFE_className={classes.assistantMessage}>{message.content}</View>}

            {message.content === '' && message.error === undefined && isStreaming && (
                <ProgressCircle size={'S'} isIndeterminate aria-label={'Thinking'} />
            )}

            {message.error !== undefined && (
                <InlineAlert variant={'negative'} width={'100%'}>
                    <Heading>Something went wrong</Heading>
                    <Content>{message.error}</Content>
                </InlineAlert>
            )}
        </Flex>
    );
};

interface MessageListProps {
    messages: ChatMessage[];
    status: ChatStatus;
}

export const MessageList = ({ messages, status }: MessageListProps) => {
    const bottom = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottom.current?.scrollIntoView({ block: 'end' });
    }, [messages]);

    const lastId = messages.at(-1)?.id;

    return (
        <Flex direction={'column'} gap={'size-200'}>
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
