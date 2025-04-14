// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties, ReactNode } from 'react';

import { Flex } from '@adobe/react-spectrum';
import { usePress } from 'react-aria';

interface ActionLinkProps {
    children: ReactNode;
    onPress: () => void;
    icon?: ReactNode;
    iconPosition?: 'start' | 'end';
    inline?: boolean;
    isDisabled?: boolean;
    ariaExpanded?: boolean;
    style?: CSSProperties;
    id?: string;
    dataTestId?: string;
}

export const ActionLink = ({
    children,
    onPress,
    icon,
    iconPosition = 'end',
    inline = true,
    isDisabled = false,
    ariaExpanded,
    style = {},
    id,
    dataTestId,
}: ActionLinkProps) => {
    const { pressProps } = usePress({ onPress, isDisabled });

    return (
        <div
            id={id}
            data-testid={dataTestId}
            aria-label='action-link'
            aria-expanded={ariaExpanded}
            style={{ width: 'fit-content', ...style, cursor: isDisabled ? 'default' : 'pointer', userSelect: 'none' }}
            {...pressProps}
        >
            {inline ? (
                <Flex alignItems='center'>
                    {iconPosition === 'start' && icon}
                    {children}
                    {iconPosition === 'end' && icon}
                </Flex>
            ) : (
                <Flex justifyContent='center' direction={'column'}>
                    {iconPosition === 'start' && icon}
                    {children}
                    {iconPosition === 'end' && icon}
                </Flex>
            )}
        </div>
    );
};
