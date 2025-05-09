// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { Flex, Keyboard, Text } from '@adobe/react-spectrum';
import { isString } from 'lodash-es';

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
