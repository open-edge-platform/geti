// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useRef, useState } from 'react';

import { useTranslation } from '@/i18n';
import {
    ActionButton,
    Button,
    Content,
    Flex,
    Heading,
    InlineAlert,
    ProgressCircle,
    Text,
    Tooltip,
    TooltipTrigger,
} from '@geti-ui/ui';
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
    const { t } = useTranslation();
    const status = useConnectionStatus();
    const chat = useAiChat(target);
    const [attachment, setAttachment] = useState<ChatAttachment | null>(null);
    const [attachmentError, setAttachmentError] = useState<string | null>(null);
    const [attachmentAttempt, setAttachmentAttempt] = useState(0);
    const [settingsOpen, setSettingsOpen] = useState(false);
    const autoOpenedSettings = useRef(false);
    const drawerRef = useRef<HTMLElement | null>(null);

    useEffect(() => {
        const controller = new AbortController();
        let active = true;
        setAttachment(null);
        setAttachmentError(null);
        void loadMediaAttachment(target.source, controller.signal)
            .then((value) => {
                if (active) setAttachment(value);
            })
            .catch((error: unknown) => {
                if (active && !(error instanceof DOMException && error.name === 'AbortError')) {
                    setAttachmentError(error instanceof Error ? error.message : t('assistant.mediaLoadFailed'));
                }
            });
        return () => {
            active = false;
            controller.abort();
        };
    }, [target.source, attachmentAttempt, t]);

    useEffect(() => {
        // Open the settings panel once when the assistant is not ready; after
        // that the user controls it and status changes must not fight the toggle.
        if (status.isLoading || autoOpenedSettings.current) return;
        if (!status.isReady) {
            autoOpenedSettings.current = true;
            setSettingsOpen(true);
        }
    }, [status.isLoading, status.isReady]);

    // `onClose` is a fresh closure on every parent render; the one-shot effects
    // below must not re-run with it, so it is tracked through a ref.
    const onCloseRef = useRef(onClose);

    useEffect(() => {
        onCloseRef.current = onClose;
    }, [onClose]);

    useEffect(() => {
        const onKeyDown = (event: KeyboardEvent) => {
            if (event.key === 'Escape') onCloseRef.current();
        };

        window.addEventListener('keydown', onKeyDown);
        return () => window.removeEventListener('keydown', onKeyDown);
    }, []);

    useEffect(() => {
        const previouslyFocused = document.activeElement instanceof HTMLElement ? document.activeElement : null;
        drawerRef.current?.focus();

        return () => {
            previouslyFocused?.focus();
        };
    }, []);

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
            <aside
                ref={drawerRef}
                className={classes.drawer}
                role='dialog'
                aria-modal={false}
                aria-label='Annotate with AI'
                tabIndex={-1}
            >
                <header className={classes.header}>
                    <div>
                        <Heading level={3} margin={0}>
                            {t('assistant.title')}
                        </Heading>
                        <AssistantSwitcher isDisabled={chat.status === 'busy'} />
                    </div>
                    <div className={classes.headerActions}>
                        <TooltipTrigger>
                            <ActionButton isQuiet aria-label='Clear conversation' onPress={chat.clear}>
                                <Delete />
                            </ActionButton>
                            <Tooltip>{t('assistant.clearConversation')}</Tooltip>
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
                            <Tooltip>{t('assistant.connectionSettings')}</Tooltip>
                        </TooltipTrigger>
                        <TooltipTrigger>
                            <ActionButton isQuiet aria-label='Close assistant' onPress={onClose}>
                                <Close />
                            </ActionButton>
                            <Tooltip>{t('common.actions.close')}</Tooltip>
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
                            <Button variant='secondary' onPress={() => setAttachmentAttempt((value) => value + 1)}>
                                {t('assistant.tryAgain')}
                            </Button>
                        </InlineAlert>
                    )}
                    {attachment === null && attachmentError === null && (
                        <Flex alignItems='center' gap='size-100'>
                            <ProgressCircle size='S' isIndeterminate aria-label='Loading media' />
                            <Text>{t('assistant.mediaLoading')}</Text>
                        </Flex>
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
