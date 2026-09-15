// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Flex, Heading, Text } from '@geti-ui/ui';

import classes from './assistant.module.scss';

const SUGGESTIONS = [
    'Which model architecture fits this project and my hardware?',
    'Is my dataset big and balanced enough to start training?',
    'My last model scored badly — look at the metrics and tell me why.',
    'Review my label set and point out overlapping or ambiguous labels.',
    'What should I annotate next to improve accuracy the most?',
];

export const WelcomeScreen = ({ onPick }: { onPick: (prompt: string) => void }) => {
    return (
        <Flex direction={'column'} gap={'size-200'}>
            <Flex direction={'column'} gap={'size-50'}>
                <Heading level={3} margin={0}>
                    Ask ChatGPT about this project
                </Heading>
                <Text UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-700)' }}>
                    The assistant can read your projects, dataset statistics, models, training curves and hardware to
                    give grounded advice. It can also start training or quantization — but only after you approve it.
                </Text>
            </Flex>

            <Flex direction={'column'} gap={'size-100'}>
                {SUGGESTIONS.map((suggestion) => (
                    <button
                        key={suggestion}
                        type={'button'}
                        className={classes.suggestion}
                        onClick={() => onPick(suggestion)}
                    >
                        {suggestion}
                    </button>
                ))}
            </Flex>
        </Flex>
    );
};
