// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { getAiAgent } from '../agents';
import { setAiVendor, useAiConnection } from '../connection';
import type { AiVendor } from '../types';
import { ChatGptMark, ClaudeMark } from './assistant-mark.component';

import classes from './assistant.module.scss';

const CHOICES: { vendor: AiVendor; name: string; Mark: typeof ChatGptMark }[] = [
    { vendor: 'openai', name: 'ChatGPT', Mark: ChatGptMark },
    { vendor: 'anthropic', name: 'Claude', Mark: ClaudeMark },
];

export const AssistantSwitcher = ({ isDisabled = false }: { isDisabled?: boolean }) => {
    const connection = useAiConnection();
    const currentVendor = getAiAgent(connection.agentId).vendor;

    return (
        <div className={classes.assistantPills} role='radiogroup' aria-label='AI assistant'>
            {CHOICES.map(({ vendor, name, Mark }) => (
                <button
                    key={vendor}
                    type='button'
                    role='radio'
                    aria-checked={currentVendor === vendor}
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
