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

import { ComponentProps, Key, ReactNode } from 'react';

import { Item, Menu, MenuTrigger, Section, Text } from '@adobe/react-spectrum';

import { idMatchingFormat } from '../../../../../test-utils/id-utils';
import { ColorMode, QuietActionButton } from '../../../quiet-button/quiet-action-button.component';

import classes from './header-submenu.module.scss';

interface HeaderSubmenuItems {
    children: {
        text: ReactNode;
        id: string;
        icon?: ReactNode;
    }[];
    id: string;
}

interface HeaderSubmenuProps {
    items: HeaderSubmenuItems[];
    icon: ReactNode;
    ariaLabel: string;
    onMenuAction: (key: Key) => void;
    isDarkMode: boolean;
    buttonClasses?: string;
    menuWidth?: ComponentProps<typeof Menu>['width'];
}

export const HeaderSubmenu = ({
    items,
    icon,
    onMenuAction,
    ariaLabel,
    isDarkMode,
    buttonClasses,
    menuWidth = 'size-2400',
}: HeaderSubmenuProps): JSX.Element => {
    return (
        <MenuTrigger>
            <QuietActionButton
                id={idMatchingFormat(ariaLabel)}
                aria-label={ariaLabel}
                colorMode={isDarkMode ? ColorMode.DARK : ColorMode.LIGHT}
                UNSAFE_className={buttonClasses}
            >
                {icon}
            </QuietActionButton>
            <Menu onAction={onMenuAction} width={menuWidth} UNSAFE_className={classes.headerSubmenu}>
                {items.map((item) => (
                    <Section items={item.children} key={item.id}>
                        {(childItem) => (
                            <Item key={childItem.id} textValue={childItem.id}>
                                {childItem.icon}
                                <Text marginY={'auto'}>{childItem.text}</Text>
                            </Item>
                        )}
                    </Section>
                ))}
            </Menu>
        </MenuTrigger>
    );
};
