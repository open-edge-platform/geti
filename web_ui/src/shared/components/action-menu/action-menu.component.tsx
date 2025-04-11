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
