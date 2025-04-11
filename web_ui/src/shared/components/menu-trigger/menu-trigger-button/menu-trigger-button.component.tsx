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

import { ComponentProps, ReactNode } from 'react';

import { Text } from '@adobe/react-spectrum';
import { Placement } from 'react-aria';

import { MoreMenu } from '../../../../assets/icons';
import { ButtonWithSpectrumTooltip } from '../../button-with-tooltip/button-with-tooltip.component';
import { Button } from '../../button/button.component';
import { MenuTriggerProps } from '../../upload-media/upload-media-button/upload-media-button.interface';
import { MenuTrigger } from '../menu-trigger.component';

import classes from '../menu-trigger.module.scss';

interface MenuTriggerButtonProps extends Omit<MenuTriggerProps, 'children'> {
    title?: string;
    isQuiet?: boolean;
    icon?: JSX.Element;
    variant?: ComponentProps<typeof Button>['variant'];
    ariaLabel?: string;
    isDisabled?: boolean;
    customTriggerContent?: ReactNode;
    menuTriggerClasses?: string;
    tooltipPlacement?: Placement;
}

export const MenuTriggerButton = ({
    items,
    onAction,
    disabledKeys,
    menuTooltip,
    onOpenChange,
    selectedKey,
    id,
    variant,
    ariaLabel = 'open menu',
    isQuiet,
    icon,
    menuTriggerClasses,
    title,
    customTriggerContent,
    isDisabled,
    tooltipPlacement = 'bottom',
}: MenuTriggerButtonProps): JSX.Element => {
    return (
        <MenuTrigger
            id={id}
            items={items}
            onAction={onAction}
            selectedKey={selectedKey}
            menuTooltip={menuTooltip}
            disabledKeys={disabledKeys}
            onOpenChange={onOpenChange}
            ariaLabel={ariaLabel}
        >
            <ButtonWithSpectrumTooltip
                id={id}
                variant={variant}
                aria-label={ariaLabel}
                isQuiet={isQuiet || !!icon}
                isDisabled={isDisabled}
                UNSAFE_className={[classes.menuTrigger, menuTriggerClasses].join(' ')}
                tooltip={title}
                tooltipPlacement={tooltipPlacement}
            >
                {customTriggerContent ?? icon ?? <>{isQuiet ? <MoreMenu /> : <Text>{title}</Text>}</>}
            </ButtonWithSpectrumTooltip>
        </MenuTrigger>
    );
};
