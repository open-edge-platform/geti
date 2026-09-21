// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useRef, useState, type KeyboardEvent } from 'react';

import {
    ActionButton,
    Button,
    Flex,
    Item,
    Menu,
    MenuTrigger,
    Text,
    TextArea,
    Tooltip,
    TooltipTrigger,
} from '@geti-ui/ui';
import { CloseSmall, Image } from '@geti-ui/ui/icons';

import { MAX_ATTACHMENTS, MAX_INPUT_CHARS } from '../config';
import type { MediaAttachmentSource } from '../media-attachment';
import type { ChatAttachment, ChatStatus } from '../types';

import classes from './assistant.module.scss';

interface ComposerProps {
    status: ChatStatus;
    isDisabled: boolean;
    attachments: ChatAttachment[];
    attachmentSources: MediaAttachmentSource[];
    onAttach: (source: MediaAttachmentSource) => void;
    onAttachFiles?: (files: File[]) => void;
    placeholder?: string;
    onRemoveAttachment: (id: string) => void;
    onSend: (text: string) => void;
    onStop: () => void;
}

export const Composer = ({
    status,
    isDisabled,
    attachments,
    attachmentSources,
    onAttach,
    onAttachFiles,
    placeholder = 'Ask about labels, models, training…',
    onRemoveAttachment,
    onSend,
    onStop,
}: ComposerProps) => {
    const [text, setText] = useState('');
    const fileInput = useRef<HTMLInputElement>(null);

    const isBusy = status === 'busy';
    const canSend = !isBusy && !isDisabled && (text.trim() !== '' || attachments.length > 0);

    const submit = () => {
        if (!canSend) {
            return;
        }

        onSend(text.trim());
        setText('');
    };

    const handleKeyDown = (event: KeyboardEvent) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            submit();
        }
    };

    return (
        <Flex direction={'column'} gap={'size-100'}>
            {attachments.length > 0 && (
                <div className={classes.thumbnails}>
                    {attachments.map((attachment) => (
                        <Flex key={attachment.id} alignItems={'center'} gap={'size-50'}>
                            <img
                                src={attachment.dataUrl}
                                alt={attachment.name}
                                title={attachment.name}
                                className={classes.thumbnail}
                            />
                            <TooltipTrigger placement={'top'}>
                                <ActionButton
                                    isQuiet
                                    aria-label={`Remove ${attachment.name}`}
                                    onPress={() => onRemoveAttachment(attachment.id)}
                                >
                                    <CloseSmall />
                                </ActionButton>
                                <Tooltip>Remove {attachment.name}</Tooltip>
                            </TooltipTrigger>
                        </Flex>
                    ))}
                </div>
            )}

            <TextArea
                width={'100%'}
                height={'size-1000'}
                aria-label={'Message'}
                placeholder={placeholder}
                value={text}
                onChange={setText}
                onKeyDown={handleKeyDown}
                onPaste={(event) => {
                    const files = Array.from(event.clipboardData.files);
                    if (onAttachFiles && !isDisabled && !isBusy && files.length > 0) {
                        event.preventDefault();
                        onAttachFiles(files);
                    }
                }}
                maxLength={MAX_INPUT_CHARS}
                isDisabled={isDisabled}
            />

            <Flex alignItems={'center'} justifyContent={'space-between'} gap={'size-100'}>
                <Flex alignItems={'center'} gap={'size-100'}>
                    {onAttachFiles && (
                        <>
                            <input
                                ref={fileInput}
                                type={'file'}
                                hidden
                                multiple
                                accept={'image/png,image/jpeg,image/webp,image/gif'}
                                onChange={(event) => {
                                    onAttachFiles(Array.from(event.target.files ?? []));
                                    event.target.value = '';
                                }}
                            />
                            <ActionButton
                                isQuiet
                                aria-label={'Attach images from computer'}
                                isDisabled={isDisabled || isBusy || attachments.length >= MAX_ATTACHMENTS}
                                onPress={() => fileInput.current?.click()}
                            >
                                <Image />
                            </ActionButton>
                        </>
                    )}
                    {attachmentSources.length > 0 && (
                        <MenuTrigger>
                            <ActionButton
                                isQuiet
                                aria-label={'Attach an image'}
                                isDisabled={isDisabled || isBusy || attachments.length >= MAX_ATTACHMENTS}
                            >
                                <Image />
                            </ActionButton>
                            <Menu
                                items={attachmentSources}
                                onAction={(key) => {
                                    const source = attachmentSources.find(({ id }) => id === key);

                                    if (source !== undefined) {
                                        onAttach(source);
                                    }
                                }}
                            >
                                {(source: MediaAttachmentSource) => <Item key={source.id}>{source.name}</Item>}
                            </Menu>
                        </MenuTrigger>
                    )}
                    <Text UNSAFE_style={{ fontSize: 'var(--spectrum-global-dimension-font-size-50)' }}>
                        Enter to send, Shift + Enter for a new line
                    </Text>
                </Flex>
                {isBusy ? (
                    <Button variant={'secondary'} onPress={onStop}>
                        Stop
                    </Button>
                ) : (
                    <Button variant={'accent'} onPress={submit} isDisabled={!canSend}>
                        Send
                    </Button>
                )}
            </Flex>
        </Flex>
    );
};
