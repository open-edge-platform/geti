// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useCallback, useEffect, useState } from 'react';

import { ActionButton, Content, Flex, Heading, InlineAlert, Text, Tooltip, TooltipTrigger } from '@geti-ui/ui';
import { Close, Delete, Gear } from '@geti-ui/ui/icons';

import type { AnnotationTarget } from '../annotation/annotation-tools';
import { MAX_ATTACHMENTS } from '../config';
import { useAiConnection } from '../connection';
import { useAssistantContext } from '../context/use-assistant-context';
import { useConnectionStatus } from '../hooks/use-connection-status';
import { loadFileAttachment, loadMediaAttachment, type MediaAttachmentSource } from '../media-attachment';
import { useAiChat } from '../runtime/use-ai-chat';
import type { ChatAttachment } from '../types';
import { ActionApproval } from './action-approval.component';
import { ChatGptModelPicker } from './chatgpt-model-picker.component';
import { Composer } from './composer.component';
import { ConnectionSettings } from './connection-settings.component';
import { MessageList } from './message-list.component';
import { WelcomeScreen } from './welcome-screen.component';

import classes from './assistant.module.scss';

interface AssistantDrawerProps {
    projectId: string;
    /** Dataset images the user may attach to a question. */
    attachmentSources: MediaAttachmentSource[];
    annotationTarget?: AnnotationTarget;
    onClose: () => void;
}

export const AssistantDrawer = ({ projectId, attachmentSources, annotationTarget, onClose }: AssistantDrawerProps) => {
    const context = useAssistantContext(projectId);
    const status = useConnectionStatus();
    const { provider, model } = useAiConnection();
    const [attachments, setAttachments] = useState<ChatAttachment[]>([]);
    const [attachmentError, setAttachmentError] = useState<string | null>(null);
    const [isAttaching, setIsAttaching] = useState(false);
    const {
        messages,
        status: chatStatus,
        pendingApproval,
        resolveApproval,
        send,
        stop,
        clear,
    } = useAiChat(projectId, context, annotationTarget ? { target: annotationTarget } : undefined);

    const [isSettingsOpen, setIsSettingsOpen] = useState(false);

    const sourceId = annotationTarget?.source.id;
    const sourceUrl = annotationTarget?.source.url;
    const sourceName = annotationTarget?.source.name;
    useEffect(() => {
        if (!sourceId || !sourceUrl || !sourceName) return;
        let active = true;
        setIsAttaching(true);
        setAttachmentError(null);
        void loadMediaAttachment({ id: sourceId, url: sourceUrl, name: sourceName })
            .then((attachment) => {
                if (active) setAttachments([attachment]);
            })
            .catch((error: unknown) => {
                if (active)
                    setAttachmentError(error instanceof Error ? error.message : 'Could not load the current image.');
            })
            .finally(() => {
                if (active) setIsAttaching(false);
            });
        return () => {
            active = false;
        };
    }, [sourceId, sourceUrl, sourceName]);

    // An unusable connection is the one thing the user must fix first, so the
    // settings open themselves instead of hiding behind the gear -- and fold
    // away again the moment the connection starts working.
    useEffect(() => {
        if (!status.isLoading) {
            setIsSettingsOpen(!status.isReady);
        }
    }, [status.isLoading, status.isReady]);

    useEffect(() => {
        const close = (event: KeyboardEvent) => {
            if (event.key === 'Escape') {
                event.stopImmediatePropagation();
                onClose();
            }
        };

        window.addEventListener('keydown', close, true);

        return () => window.removeEventListener('keydown', close, true);
    }, [onClose]);

    const attach = useCallback((source: MediaAttachmentSource) => {
        setAttachmentError(null);
        setIsAttaching(true);

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
            })
            .finally(() => setIsAttaching(false));
    }, []);

    const attachFiles = (files: File[]) => {
        if (isAttaching || chatStatus === 'busy') return;
        setIsAttaching(true);
        setAttachmentError(null);
        void Promise.all(files.slice(0, MAX_ATTACHMENTS - attachments.length).map(loadFileAttachment))
            .then((loaded) => setAttachments((current) => [...current, ...loaded].slice(0, MAX_ATTACHMENTS)))
            .catch((error: unknown) =>
                setAttachmentError(error instanceof Error ? error.message : 'Could not attach images.')
            )
            .finally(() => setIsAttaching(false));
    };

    const submit = (text: string) => {
        if (isAttaching || !status.isReady || chatStatus === 'busy') return;
        if (annotationTarget && !attachments.some(({ id }) => id === annotationTarget.source.id)) {
            setAttachmentError('Attach the current image before generating annotations.');
            return;
        }
        send(
            text || (annotationTarget ? 'Annotate this image using the project labels.' : 'Describe this image.'),
            attachments
        );
        if (!annotationTarget) setAttachments([]);
    };

    const providerLabel = provider === 'api' ? 'OpenAI API key' : 'ChatGPT app';
    const connectionLabel = status.isLoading
        ? 'Checking connection…'
        : status.isReady
          ? `${providerLabel} · ${model === '' ? 'account default' : model}`
          : 'Not connected';

    return (
        <>
            {!annotationTarget && <div className={classes.overlay} onClick={onClose} aria-hidden />}

            <aside
                className={[classes.drawer, annotationTarget ? classes.dockedDrawer : ''].join(' ')}
                data-annotation-assistant={annotationTarget ? true : undefined}
                aria-label={'Annotate with ChatGPT'}
            >
                <Flex UNSAFE_className={classes.header} alignItems={'center'} justifyContent={'space-between'}>
                    <Flex direction={'column'} gap={'size-25'}>
                        <Heading level={3} margin={0}>
                            Annotate with ChatGPT
                        </Heading>

                        <span
                            className={[classes.providerState, status.isReady ? classes.providerStateConnected : '']
                                .join(' ')
                                .trim()}
                        >
                            {connectionLabel}
                        </span>
                    </Flex>

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

                {provider === 'chatgpt' && (
                    <div className={classes.modelSelector}>
                        <ChatGptModelPicker status={status} isBusy={chatStatus === 'busy'} />
                    </div>
                )}
                {isSettingsOpen && <ConnectionSettings status={status} />}

                <div className={classes.body}>
                    {annotationTarget && (
                        <Text>
                            Current image: {annotationTarget.source.name}. It will be included when you send a message.
                        </Text>
                    )}
                    {messages.length === 0 ? (
                        annotationTarget ? (
                            <Text>Describe what to annotate, or press Send to use the project labels.</Text>
                        ) : (
                            <WelcomeScreen onPick={status.isReady ? submit : () => setIsSettingsOpen(true)} />
                        )
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
                            placeholder={annotationTarget ? 'Describe what to annotate…' : undefined}
                            status={chatStatus}
                            isDisabled={!status.isReady || isAttaching}
                            attachments={attachments}
                            attachmentSources={attachmentSources}
                            onAttach={attach}
                            onAttachFiles={annotationTarget ? undefined : attachFiles}
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
