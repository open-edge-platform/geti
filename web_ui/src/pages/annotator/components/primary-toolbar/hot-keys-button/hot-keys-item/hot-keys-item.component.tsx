// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ReactNode } from 'react';

import { Flex, Keyboard, Text } from '@adobe/react-spectrum';
import isString from 'lodash/isString';

import { getKeyName } from '../../../../../../shared/hotkeys';
import { idMatchingFormat } from '../../../../../../test-utils/id-utils';

import classes from './hot-keys-item.module.scss';

interface HotKeysItemProps {
    title: string;
    shortcut: ReactNode | string;
    disabled?: boolean;
}

export const HotKeysItem = ({ title, shortcut, disabled = false }: HotKeysItemProps): JSX.Element => {
    const isDisabledClass = disabled ? classes.hotKeysKeyboardDisabled : '';

    return (
        <Flex alignItems={'center'} justifyContent={'space-between'} marginBottom={'size-150'}>
            <Text flexBasis={'65%'} id={`${idMatchingFormat(title)}-id`} UNSAFE_className={isDisabledClass}>
                {title}
            </Text>
            <Keyboard
                UNSAFE_className={isDisabledClass}
                flexBasis={'35%'}
                id={`${idMatchingFormat(title)}-shortcut-id`}
            >
                {isString(shortcut) ? getKeyName(shortcut) : shortcut}
            </Keyboard>
        </Flex>
    );
};
