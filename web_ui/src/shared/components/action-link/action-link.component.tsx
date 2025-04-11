// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
