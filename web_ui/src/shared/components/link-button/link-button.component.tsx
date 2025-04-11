// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Text } from '@adobe/react-spectrum';
import { StyleProps } from '@react-types/shared';

import { ActionButton } from '../button/button.component';

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
