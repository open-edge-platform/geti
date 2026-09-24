// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState, type KeyboardEvent } from 'react';

import { Button, Flex, TextArea } from '@geti-ui/ui';

import { MAX_INPUT_CHARS } from '../config';
import type { ChatAttachment, ChatStatus } from '../types';

import classes from './assistant.module.scss';

interface ComposerProps {
    attachment: ChatAttachment;
    status: ChatStatus;
    isDisabled: boolean;
    onSend: (text: string) => void;
    onStop: () => void;
}

export const Composer = ({ attachment, status, isDisabled, onSend, onStop }: ComposerProps) => {
    const [text, setText] = useState('');
    const isBusy = status === 'busy';

    const submit = () => {
        if (isBusy || isDisabled) return;
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
        <Flex direction='column' gap='size-100'>
            <div className={classes.attachment}>
                <img src={attachment.dataUrl} alt='' />
                <span title={attachment.name}>{attachment.name}</span>
            </div>
            <TextArea
                width='100%'
                height='size-1000'
                aria-label='Annotation request'
                placeholder='Describe what to annotate...'
                value={text}
                onChange={setText}
                onKeyDown={handleKeyDown}
                maxLength={MAX_INPUT_CHARS}
                isDisabled={isDisabled}
            />
            <Button alignSelf='end' variant={isBusy ? 'secondary' : 'accent'} onPress={isBusy ? onStop : submit}>
                {isBusy ? 'Stop' : 'Send'}
            </Button>
        </Flex>
    );
};
