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

import { Key, ReactNode } from 'react';

import isFunction from 'lodash/isFunction';

import { MenuTriggerButton } from '../menu-trigger/menu-trigger-button/menu-trigger-button.component';

interface MenuTriggerListProps {
    id: string;
    title?: string;
    icon?: JSX.Element;
    tooltip?: ReactNode;
    isDisabled?: boolean;
    ariaLabel?: string;
    options: [string, () => void][];
}

export const MenuTriggerList = ({ options, ...props }: MenuTriggerListProps): JSX.Element => {
    const ITEMS: string[] = options.map(([key]) => key);

    const handleOnAction = (key: Key): void => {
        const optionKey = String(key).toLocaleLowerCase();
        const [, action] = options.find(([iKey]) => iKey.toLocaleLowerCase() === optionKey) ?? [];

        isFunction(action) && action();
    };

    return <MenuTriggerButton items={ITEMS} onAction={handleOnAction} {...props} isQuiet />;
};
