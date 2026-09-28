// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { KeyboardEvent } from 'react';

import { getAiAgent } from '../agents';
import { setAiVendor, useAiConnection } from '../connection';
import type { AiVendor } from '../types';
import { ChatGptMark, ClaudeMark } from './assistant-mark.component';

import classes from './assistant.module.scss';

const CHOICES: { vendor: AiVendor; name: string; Mark: typeof ChatGptMark }[] = [
    { vendor: 'openai', name: 'ChatGPT', Mark: ChatGptMark },
    { vendor: 'anthropic', name: 'Claude', Mark: ClaudeMark },
];

const moveSelection = (event: KeyboardEvent, group: HTMLDivElement, select: () => void): void => {
    const buttons = Array.from(group.querySelectorAll<HTMLButtonElement>('button[role="radio"]'));
    const index = buttons.findIndex((button) => button.getAttribute('aria-checked') === 'true');
    if (index === -1 || buttons.length === 0) return;
    const next = buttons[(index + 1) % buttons.length];
    select();
    next.focus();
    event.preventDefault();
};

export const AssistantSwitcher = ({ isDisabled = false }: { isDisabled?: boolean }) => {
    const connection = useAiConnection();
    const currentVendor = getAiAgent(connection.agentId).vendor;

    const handleKeyDown = (event: KeyboardEvent) => {
        if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
        moveSelection(event, event.currentTarget as HTMLDivElement, () =>
            setAiVendor(currentVendor === 'openai' ? 'anthropic' : 'openai')
        );
    };

    return (
        <div
            className={classes.assistantPills}
            role='radiogroup'
            aria-label='AI assistant'
            tabIndex={-1}
            onKeyDown={isDisabled ? undefined : handleKeyDown}
        >
            {CHOICES.map(({ vendor, name, Mark }) => (
                <button
                    key={vendor}
                    type='button'
                    role='radio'
                    aria-checked={currentVendor === vendor}
                    tabIndex={currentVendor === vendor ? 0 : -1}
                    disabled={isDisabled}
                    className={classes.assistantPill}
                    onClick={() => setAiVendor(vendor)}
                >
                    <Mark className={classes.assistantPillMark} />
                    <span>{name}</span>
                </button>
            ))}
        </div>
    );
};
