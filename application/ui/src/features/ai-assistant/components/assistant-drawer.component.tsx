// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useState } from 'react';

import { ActionButton, Content, Heading, InlineAlert, Tooltip, TooltipTrigger } from '@geti-ui/ui';
import { Close, Delete, Gear } from '@geti-ui/ui/icons';
import { createPortal } from 'react-dom';

import type { AnnotationTarget } from '../annotation/annotation-tools';
import { useConnectionStatus } from '../hooks/use-connection-status';
import { loadMediaAttachment } from '../media-attachment';
import { useAiChat } from '../runtime/use-ai-chat';
import type { ChatAttachment } from '../types';
import { AssistantSwitcher } from './assistant-switcher.component';
import { Composer } from './composer.component';
import { ConnectionSettings } from './connection-settings.component';
import { MessageList } from './message-list.component';

import classes from './assistant.module.scss';

export const AssistantDrawer = ({ target, onClose }: { target: AnnotationTarget; onClose: () => void }) => {
    const status = useConnectionStatus();
    const chat = useAiChat(target);
    const [attachment, setAttachment] = useState<ChatAttachment | null>(null);
    const [attachmentError, setAttachmentError] = useState<string | null>(null);
    const [settingsOpen, setSettingsOpen] = useState(false);

    useEffect(() => {
        let active = true;
        setAttachment(null);
        setAttachmentError(null);
        void loadMediaAttachment(target.source)
            .then((value) => {
                if (active) setAttachment(value);
            })
            .catch((error: unknown) => {
                if (active) {
                    setAttachmentError(
                        error instanceof Error ? error.message : 'The current media could not be loaded.'
                    );
                }
            });
        return () => {
            active = false;
        };
    }, [target.source]);

    useEffect(() => {
        if (!status.isLoading) setSettingsOpen(!status.isReady);
    }, [status.isLoading, status.isReady]);

    const submit = (text: string) => {
        if (attachment === null) return;
        const defaultPrompt =
            target.taskType === 'detection'
                ? 'Annotate all matching objects with tight bounding boxes using the project labels.'
                : 'Segment all matching objects with precise polygons using the project labels.';
        chat.send(text || defaultPrompt, attachment);
    };

    return createPortal(
        <>
            <div className={classes.backdrop} aria-hidden='true' />
            <aside className={classes.drawer} role='dialog' aria-modal={false} aria-label='Annotate with AI'>
                <header className={classes.header}>
                    <div>
                        <Heading level={3} margin={0}>
                            Annotate with AI
                        </Heading>
                        <AssistantSwitcher isDisabled={chat.status === 'busy'} />
                    </div>
                    <div className={classes.headerActions}>
                        <TooltipTrigger>
                            <ActionButton isQuiet aria-label='Clear conversation' onPress={chat.clear}>
                                <Delete />
                            </ActionButton>
                            <Tooltip>Clear conversation</Tooltip>
                        </TooltipTrigger>
                        <TooltipTrigger>
                            <ActionButton
                                isQuiet
                                aria-label='Connection settings'
                                aria-pressed={settingsOpen}
                                onPress={() => setSettingsOpen((open) => !open)}
                            >
                                <Gear />
                            </ActionButton>
                            <Tooltip>Connection settings</Tooltip>
                        </TooltipTrigger>
                        <TooltipTrigger>
                            <ActionButton isQuiet aria-label='Close assistant' onPress={onClose}>
                                <Close />
                            </ActionButton>
                            <Tooltip>Close</Tooltip>
                        </TooltipTrigger>
                    </div>
                </header>
                {settingsOpen && <ConnectionSettings status={status} />}
                <div className={classes.body}>
                    {chat.messages.length > 0 && <MessageList messages={chat.messages} status={chat.status} />}
                </div>
                <footer className={classes.footer}>
                    {attachmentError !== null && (
                        <InlineAlert variant='negative' width='100%'>
                            <Content>{attachmentError}</Content>
                        </InlineAlert>
                    )}
                    {attachment !== null && (
                        <Composer
                            attachment={attachment}
                            status={chat.status}
                            isDisabled={!status.isReady || target.labels.length === 0}
                            onSend={submit}
                            onStop={chat.stop}
                        />
                    )}
                </footer>
            </aside>
        </>,
        document.body
    );
};
