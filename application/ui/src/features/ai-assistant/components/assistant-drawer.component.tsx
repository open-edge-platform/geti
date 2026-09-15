// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useCallback, useEffect, useState } from 'react';

import { ActionButton, Content, Flex, Heading, InlineAlert, Text, Tooltip, TooltipTrigger } from '@geti-ui/ui';
import { Close, Delete, Gear } from '@geti-ui/ui/icons';

import { MAX_ATTACHMENTS } from '../config';
import { useAssistantContext } from '../context/use-assistant-context';
import { useConnectionStatus } from '../hooks/use-connection-status';
import { loadMediaAttachment, type MediaAttachmentSource } from '../media-attachment';
import { useAiChat } from '../runtime/use-ai-chat';
import type { ChatAttachment } from '../types';
import { ActionApproval } from './action-approval.component';
import { Composer } from './composer.component';
import { ConnectionSettings } from './connection-settings.component';
import { MessageList } from './message-list.component';
import { WelcomeScreen } from './welcome-screen.component';

import classes from './assistant.module.scss';

interface AssistantDrawerProps {
    projectId: string;
    /** Dataset images the user may attach to a question. */
    attachmentSources: MediaAttachmentSource[];
    onClose: () => void;
}

export const AssistantDrawer = ({ projectId, attachmentSources, onClose }: AssistantDrawerProps) => {
    const context = useAssistantContext(projectId);
    const status = useConnectionStatus();
    const {
        messages,
        status: chatStatus,
        pendingApproval,
        resolveApproval,
        send,
        stop,
        clear,
    } = useAiChat(projectId, context);

    const [attachments, setAttachments] = useState<ChatAttachment[]>([]);
    const [attachmentError, setAttachmentError] = useState<string | null>(null);
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);

    // An unusable connection is the one thing the user must fix first, so the
    // settings open themselves instead of hiding behind the gear.
    useEffect(() => {
        if (!status.isLoading && !status.isReady) {
            setIsSettingsOpen(true);
        }
    }, [status.isLoading, status.isReady]);

    useEffect(() => {
        const close = (event: KeyboardEvent) => {
            if (event.key === 'Escape') {
                onClose();
            }
        };

        window.addEventListener('keydown', close);

        return () => window.removeEventListener('keydown', close);
    }, [onClose]);

    const attach = useCallback((source: MediaAttachmentSource) => {
        setAttachmentError(null);

        void loadMediaAttachment(source)
            .then((attachment) => {
                setAttachments((previous) =>
                    previous.some(({ id }) => id === attachment.id) || previous.length >= MAX_ATTACHMENTS
                        ? previous
                        : [...previous, attachment]
                );
            })
            .catch((reason: unknown) => {
                setAttachmentError(reason instanceof Error ? reason.message : 'The image could not be attached.');
            });
    }, []);

    const submit = (text: string) => {
        send(text, attachments);
        setAttachments([]);
    };

    return (
        <>
            <div className={classes.overlay} onClick={onClose} aria-hidden />

            <aside className={classes.drawer} aria-label={'Annotate with ChatGPT'}>
                <Flex UNSAFE_className={classes.header} alignItems={'center'} justifyContent={'space-between'}>
                    <Heading level={3} margin={0}>
                        Annotate with ChatGPT
                    </Heading>

                    <Flex alignItems={'center'} gap={'size-50'}>
                        <TooltipTrigger placement={'bottom'}>
                            <ActionButton
                                isQuiet
                                aria-label={'Clear conversation'}
                                isDisabled={messages.length === 0}
                                onPress={clear}
                            >
                                <Delete />
                            </ActionButton>
                            <Tooltip>Clear conversation</Tooltip>
                        </TooltipTrigger>

                        <TooltipTrigger placement={'bottom'}>
                            <ActionButton
                                isQuiet
                                aria-label={'Connection settings'}
                                aria-pressed={isSettingsOpen}
                                onPress={() => setIsSettingsOpen((open) => !open)}
                            >
                                <Gear />
                            </ActionButton>
                            <Tooltip>Connection settings</Tooltip>
                        </TooltipTrigger>

                        <TooltipTrigger placement={'bottom'}>
                            <ActionButton isQuiet aria-label={'Close'} onPress={onClose}>
                                <Close />
                            </ActionButton>
                            <Tooltip>Close</Tooltip>
                        </TooltipTrigger>
                    </Flex>
                </Flex>

                {isSettingsOpen && <ConnectionSettings status={status} />}

                <div className={classes.body}>
                    {messages.length === 0 ? (
                        <WelcomeScreen onPick={status.isReady ? submit : () => setIsSettingsOpen(true)} />
                    ) : (
                        <MessageList messages={messages} status={chatStatus} />
                    )}
                </div>

                <div className={classes.footer}>
                    <Flex direction={'column'} gap={'size-100'}>
                        {!status.isLoading && !status.isReady && (
                            <Text UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-700)' }}>
                                Connect an OpenAI API key or the ChatGPT app to start.
                            </Text>
                        )}

                        {attachmentError !== null && (
                            <InlineAlert variant={'negative'} width={'100%'}>
                                <Content>{attachmentError}</Content>
                            </InlineAlert>
                        )}

                        {pendingApproval !== null && (
                            <ActionApproval approval={pendingApproval} onResolve={resolveApproval} />
                        )}

                        <Composer
                            status={chatStatus}
                            isDisabled={!status.isReady}
                            attachments={attachments}
                            attachmentSources={attachmentSources}
                            onAttach={attach}
                            onRemoveAttachment={(id) =>
                                setAttachments((previous) => previous.filter((attachment) => attachment.id !== id))
                            }
                            onSend={submit}
                            onStop={stop}
                        />
                    </Flex>
                </div>
            </aside>
        </>
    );
};
