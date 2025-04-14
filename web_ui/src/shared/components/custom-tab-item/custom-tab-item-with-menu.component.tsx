// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
