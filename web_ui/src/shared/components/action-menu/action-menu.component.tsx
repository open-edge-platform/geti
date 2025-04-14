// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key } from 'react';

import { Icon, Item, Menu, Text, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { MenuTrigger as SpectrumMenuTrigger } from '@react-spectrum/menu';

import { MoreMenu } from '../../../assets/icons';
import { QuietActionButton } from '../quiet-button/quiet-action-button.component';
import { MenuAction } from './menu-action.interface';

interface ActionMenuProps<T> {
    id?: string;
    items: MenuAction<T>[];
    disabledKeys?: string[];
    onAction: (key: Key) => void;
    tooltipMessage?: string;
    ariaLabel?: string;
}
export const ActionMenu = <T extends string>({
    id,
    items,
    disabledKeys,
    onAction,
    ariaLabel = 'action menu',
    tooltipMessage = 'More',
}: ActionMenuProps<T>): JSX.Element => {
    return (
        <SpectrumMenuTrigger>
            <TooltipTrigger placement={'bottom'}>
                <QuietActionButton id={id} data-testid={id} aria-label={ariaLabel}>
                    <MoreMenu />
                </QuietActionButton>
                <Tooltip>{tooltipMessage}</Tooltip>
            </TooltipTrigger>
            <Menu onAction={onAction} disabledKeys={disabledKeys} items={items}>
                {(item) => {
                    return (
                        <Item textValue={item.name}>
                            <Text>{item.name}</Text>
                            {item.icon && <Icon>{item.icon}</Icon>}
                        </Item>
                    );
                }}
            </Menu>
        </SpectrumMenuTrigger>
    );
};
