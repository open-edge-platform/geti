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

import { ComponentProps } from 'react';

import { MenuTriggerButton } from '../menu-trigger/menu-trigger-button/menu-trigger-button.component';
import { CustomTabItem, CustomTabItemProps } from './custom-tab-item.component';

import classes from './custom-tab-item.module.scss';

type CustomTabItemWithMenuProps = CustomTabItemProps &
    Pick<
        ComponentProps<typeof MenuTriggerButton>,
        'items' | 'ariaLabel' | 'id' | 'onAction' | 'onOpenChange' | 'disabledKeys'
    >;

export const CustomTabItemWithMenu = ({
    items,
    ariaLabel,
    id,
    onAction,
    onOpenChange,
    name,
    isMoreIconVisible,
    disabledKeys,
}: CustomTabItemWithMenuProps): JSX.Element => {
    return (
        <MenuTriggerButton
            isQuiet
            id={id}
            items={items}
            onAction={onAction}
            ariaLabel={ariaLabel}
            onOpenChange={onOpenChange}
            disabledKeys={disabledKeys}
            customTriggerContent={<CustomTabItem name={name} isMoreIconVisible={isMoreIconVisible} />}
            menuTriggerClasses={classes.customTabItemMenuTrigger}
        />
    );
};
