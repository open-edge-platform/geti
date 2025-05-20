// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, Key, ReactNode } from 'react';

import { Item, Menu, MenuTrigger, Section, Text } from '@geti/ui';

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
