// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ActionButton, Text } from '@geti/ui';
import { StyleProps } from '@react-types/shared';

interface LinkButtonProps extends StyleProps {
    text: string;
    onPress?: () => void;
    ariaLabel?: string;
    isDisabled?: boolean;
}

export const LinkButton = ({ text, onPress, ariaLabel, isDisabled, UNSAFE_style }: LinkButtonProps): JSX.Element => {
    return (
        <ActionButton
            onPress={onPress}
            isQuiet
            height={'100%'}
            isDisabled={isDisabled}
            UNSAFE_style={{ backgroundColor: 'transparent', border: 0, fontWeight: '500' }}
            aria-label={ariaLabel}
        >
            <Text
                UNSAFE_style={
                    isDisabled
                        ? {}
                        : {
                              ...UNSAFE_style,
                              color: 'var(--energy-blue)',
                              pointerEvents: 'all',
                              padding: 0,
                          }
                }
            >
                {text}
            </Text>
        </ActionButton>
    );
};
