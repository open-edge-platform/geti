// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
