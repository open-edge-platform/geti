// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, ReactNode } from 'react';

import { Text } from '@adobe/react-spectrum';
import { Button } from '@geti/ui';
import { Placement } from 'react-aria';

import { MoreMenu } from '../../../../assets/icons';
import { ButtonWithSpectrumTooltip } from '../../button-with-tooltip/button-with-tooltip.component';
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
